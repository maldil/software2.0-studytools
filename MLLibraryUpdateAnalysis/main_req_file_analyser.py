import ast
from datetime import datetime
import git
import json
import os
import glob
import requirements
import argparse
import csv
from fnmatch import fnmatch
import RequirementsTXT as req
import Util


def clone_project(clone_path, git_link, folder_name=None):
    """
    :return:
    :param clone_path: local path to download the project
    :param git_link: GitHub link
    :param folder_name: Folder name of the downloading project
    """
    if os.path.isdir(clone_path + '/' + str(folder_name)) is False:
        try:
            if folder_name is None:
                git.Git(clone_path).clone(git_link)
            else:
                git.Git(clone_path).clone(git_link, folder_name)
            return True
        except git.exc.GitCommandError as e:
            return False
        except UnicodeEncodeError as e:
            return False
    else:
        return True


def get_requirement_file_paths(path: object) -> object:
    requirement = []
    pattern = "*.txt"
    requirement_names = ["requirement", "Requirement"]
    for path, subdirs, files in os.walk(path):
        for name in files:
            if fnmatch(name, pattern):
                for r in requirement_names:
                    if r in name:
                        requirement.append((os.path.join(path, name), name))
    return requirement


def req_file_history(project_download, clone_links):
    if not os.path.exists(project_download + "/TEMP"):
        os.makedirs(project_download + "/TEMP")
    project_download_path = project_download + "/TEMP"

    if not os.path.exists(project_download + "/REQ_FILE_HIST"):
        os.makedirs(project_download + "/REQ_FILE_HIST")
    req_file_download_path = project_download + "/REQ_FILE_HIST/"

    updated_projects = [os.path.basename(x).split('.')[0] for x in glob.glob(req_file_download_path + '*.json')]
    print(updated_projects)
    for (project, cl_link) in clone_links:
        project_name = project.replace('/', '_')[:-4]
        project_name = project_name.replace('.', '_')
        if project_name in updated_projects:
            continue
        if clone_project(project_download_path, cl_link, project_name):
            projects_path = project_download_path + '/' + project_name + '/'
            myg = git.Git(projects_path)
            req_file_path = get_requirement_file_paths(projects_path)

            all_req_file_details = []

            if len(req_file_path) != 0:
                for req in req_file_path:
                    req_file_hist = []
                    commit_ana = myg.log('--pretty=%H,%ae,%an,%ad,%ce,%cn,%cd,', '--follow', req[0])
                    if commit_ana == "":
                        continue
                    for q in commit_ana.split('\n'):
                        hist = {}
                        hist["PATH"] = os.path.relpath(req[0], projects_path)
                        hist["GIT"] = cl_link
                        hist["HEX"] = q.split(',')[0]
                        hist["Auth_Email"] = q.split(',')[1]
                        hist["Auth_Name"] = q.split(',')[2]
                        try:
                            au_data = datetime.strptime(' '.join(q.split(',')[3].split(' ')[:-1]),
                                                        '%a %b %d %H:%M:%S %Y')
                        except ValueError as e:
                            print(q)
                            print(e)
                            break
                        hist["Auth_Date"] = au_data.strftime("%m/%d/%Y, %H:%M:%S")
                        hist["Com_Email"] = q.split(',')[4]
                        hist["Com_Name"] = q.split(',')[5]
                        cm_date = datetime.strptime(' '.join(q.split(',')[6].split(' ')[:-1]),
                                                    '%a %b %d %H:%M:%S %Y')
                        hist["Com_Date"] = cm_date.strftime("%m/%d/%Y, %H:%M:%S")
                        req_file_hist.append(hist)

                    code_diff = myg.log('--pretty=$ CommitMalinda %H', '-p', '--follow', req[0])
                    code_diffs = {code_diff.split('$')[0]}

                    code_dif_list = {}
                    for r in code_diff.split('$'):
                        hex = ""
                        additions = []
                        removal = []
                        code_diff_map = {}
                        for u in r.split('\n'):
                            u = u.strip()
                            if "CommitMalinda" in u:
                                hex = u.split(' ')[1]
                            if len(u) > 1 and "+" == u[0] and len(u) > 2 and "+" != u[1]:
                                additions.append(u[1:])
                            if len(u) > 1 and "-" == u[0] and len(u) > 2 and "-" != u[1]:
                                removal.append(u[1:])
                            code_dif_list[hex] = {'Addition': additions, 'Deletion': removal}

                    all_details_req_file = []
                    for t in req_file_hist:
                        t['CODE_DIFF'] = code_dif_list[t["HEX"]]
                        all_details_req_file.append(t)

                    all_req_file_details += all_details_req_file
                with open(req_file_download_path + "/" + project_name + '.json', 'w',
                          encoding='utf-8') as f:
                    json.dump(all_details_req_file, f, ensure_ascii=False, indent=4)


def read_csv_file(file_path):
    csv_content = csv.reader(open(file_path), delimiter=',')
    return [(th[0], th[1]) for th in csv_content][1:]  # return github clone links except the header of the csv file


def write_list_to_a_file(destination_path, filename, list_container):
    with open(destination_path + '/' + filename, 'w+') as file:
        for x in list_container:
            if type(x) == list:
                file.write(str(",".join(x)) + '\n')
            else:
                file.write(str(x) + '\n')
    file.close()


def get_updated_ml_libraries(req_file_download_path, download_path):
    updated_libraries = []
    updates_with_ml_libraries = []
    ml_libs = Util.get_library_names()
    updates = req.get_dates_for_library_updates(req_file_download_path)
    for project, updates in updates.items():
        for update in updates:
            updated_libraries.append(update[1])
            has_ml_libs = False
            for lib in update[1]:
                if lib in ml_libs.keys():
                    has_ml_libs = True
            if has_ml_libs:
                updates_with_ml_libraries.append(update[1])

    write_list_to_a_file(download_path + "/", 'all_library_update.txt', updated_libraries)
    write_list_to_a_file(download_path + "/", 'all_ml_library_updates.txt', updates_with_ml_libraries)
    write_list_to_a_file(download_path + "/", 'all_ml_library_cascade_updates.txt', [libraries for libraries in updates_with_ml_libraries if len(libraries)>1])
    print("precentage of ML library updates that trigger cascade library updates",round(len([libraries for libraries in updates_with_ml_libraries if len(libraries)>1])/len(updates_with_ml_libraries),2))
    print("precentage of library update commits that contain ML library updates",round(len(updates_with_ml_libraries)/len(updated_libraries),2))

def process(download_path, project_csv):
    req_file_download_path = download_path + "/REQ_FILE_HIST/"
    clone_links = read_csv_file(project_csv)
    req_file_history(download_path, clone_links)
    get_updated_ml_libraries(req_file_download_path, download_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Software 2.0.')
    parser.add_argument('PATH', type=str,
                        help='project download path')
    parser.add_argument('CSV_FILE', type=str,
                        help='CSV file with project and clone link')
    args = parser.parse_args()
    process(args.PATH, args.CSV_FILE)
