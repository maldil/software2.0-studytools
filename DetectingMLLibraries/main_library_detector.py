import parso
import csv
import argparse
import git
import os
from fnmatch import fnmatch


def clone_project(clone_path, git_link, folder_name=None):
    """
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

def process(download_path, csv_file):
    print("Started processing")
    clone_links = read_csv_file(csv_file)
    if not os.path.exists(download_path+"/TEMP"):
        os.makedirs(download_path+"/TEMP")
    project_download_path = download_path+"/TEMP"

    ml_libraries = []
    for (project,clone_link) in clone_links:
        project_name= project.replace('/','_')[:-4]
        project_name= project_name.replace('.','_')
        if clone_project(project_download_path,clone_link,project_name):
            ml_libs = get_ml_libraries(project_download_path+"/"+project_name+"/")
            ml_libraries.append(ml_libs)
    count_stats(ml_libraries)
    write_list_to_a_file(download_path,"multiple_ml_library.csv",[list(gh) for gh in ml_libraries if len(gh)>1])

def count_stats(library_list):
    library_names_stats = {}
    for lib_list in library_list:
        for lib in lib_list:
            library_names_stats.setdefault(lib,[]).append(lib_list)
    library_names_stats = {th[0]:len(th[1]) for th in library_names_stats.items()}
    print("ML libraries and number of projects ",library_names_stats)
    print("Libraries that use multiple libraries ", round(len([th for th in library_list if len(th)>1])*100/len(library_list),2))
    print("Libraries that use single libraries ", round(len([th for th in library_list if len(th)==1])/len(library_list),2))


def read_csv_file(file_path):
    csv_content = csv.reader(open(file_path), delimiter=',')
    return [(th[0],th[1]) for th in csv_content][1:]  #return github clone links except the header of the csv file

def all_imports(node):
    for subscope in node.iter_funcdefs():
        yield from all_imports(subscope)
    for subscope in node.iter_classdefs():
        yield from all_imports(subscope)
    yield from node.iter_imports()

def process_file(file_path: object) -> object:
    mllibs = ['tensorflow', 'keras', 'torch', 'sklearn', 'theano', 'caffe', 'h2o', 'caffe2', 'cntk', 'spacy', 'paddle',
              'sonnet', 'amazon-dsstne', 'neon', 'mxnet', 'tflearn', 'nltk']

    lib_content = set()
    try:
        source = open(file_path, "r", encoding="ISO-8859-1").read()
    except FileNotFoundError as f:
        print(f)
        os.system('say "Error"')
        print('\a\a\a')
        return lib_content;

    module = parso.parse(source)
    imports = all_imports(module)
    # print (imports)
    for x in imports:
        if isinstance(x, parso.python.tree.ImportFrom):
            for y in mllibs:
                if y in [y.value for y in x.get_from_names()]:
                    lib_content.add(y)
        else:
            for y in mllibs:
                import_name = []
                imname = [y[0] for y in x._dotted_as_names()]
                for l in imname:
                    for r in l:
                        import_name.append(r.value)
                        # print (import_name,file_path)
                if y == import_name[0]:
                    lib_content.add(y)

    return lib_content;

def write_list_to_a_file(destination_path, filename, list_container):
    print(destination_path, filename, )
    with open(destination_path + '/' + filename, 'w+') as file:
        for x in list_container:
            if type(x) == list:
                file.write(str(",".join(x)) + '\n')
            else:
                file.write(str(x) + '\n')
    file.close()


def get_ml_libraries(dir: object) -> object:
    pattern = "*.py"
    a = 0;
    ml_libs = set()
    python_files = 0
    for path, subdirs, files in os.walk(dir):
        a = a + 1
        for name in files:
            if fnmatch(name, pattern):
                python_files += 1
                ml_libs1 = process_file(os.path.join(path, name))
                ml_libs.update(ml_libs1)
    return ml_libs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Software 2.0.')
    parser.add_argument('PATH', type=str,
                        help='project download path')
    parser.add_argument('CSV_FILE', type=str,
                        help='CSV file with project and clone link')
    args = parser.parse_args()
    process(args.PATH, args.CSV_FILE)
