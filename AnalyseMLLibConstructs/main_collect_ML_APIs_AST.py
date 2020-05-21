import parso
import os
from fnmatch import fnmatch
from pydriller import RepositoryMining
import operator
from functools import reduce
import csv
import glob
from os.path import relpath
import Util
import git
import argparse

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

def get_all_ml_imports(module):
    ml_libs = Util.get_library_names().keys()
    lib_content = []
    imports = all_imports(module)
    for x in imports:
        if isinstance(x, parso.python.tree.ImportFrom):
            if len(x.get_from_names()) != 0 and x.get_from_names()[0].value in ml_libs:
                fully_qul_name = []
                for th in x.get_paths():
                    fully_qul_name.append(".".join([yh.value for yh in th]))
                lib_content.append(
                    (x.get_from_names()[0].value, [t.value for t in x.get_defined_names()], fully_qul_name))
        else:
            ml_lib_indexes = []
            for t, lib in enumerate(list(x._dotted_as_names())):
                if lib[0][0].value in ml_libs:
                    lib_name = lib[0][0].value
                    if lib[1] is not None:
                        as_name = lib[1].value
                    else:
                        as_name = '.'.join([u.value for u in lib[0]])
                    fullname = '.'.join([u.value for u in lib[0]])
                    lib_content.append((lib_name, [as_name], [fullname]))

            # if [yu for yu in x._dotted_as_names()][0][0][0].value in ml_libs:
            #     lib_name = [yu for yu in x._dotted_as_names()][0][0][0].value
            #     ful_name = ".".join([th.value for th in list(x._dotted_as_names())[0][0]])
            #     lib_content.append((lib_name, [th.value for th in x.get_defined_names()], [ful_name]))

    return lib_content;


def all_names(node):
    for fg in node.iter_funcdefs():
        yield from all_names(fg)
    for th in node.iter_classdefs():
        yield from all_names(th)
    yield from node.children


def all_imports(node):
    for subscope in node.iter_funcdefs():
        yield from all_imports(subscope)
    for subscope in node.iter_classdefs():
        yield from all_imports(subscope)
    yield from node.iter_imports()


def get_func_names(code, param1, added_ml_apis):
    node = all_names(parso.parse(code))
    for n in node:
        iterate_python_node(n, param1, added_ml_apis)


def iterate_python_node(th, ml_libs, api_list):
    if isinstance(th, parso.python.tree.PythonNode):
        if th.type == 'atom_expr' and len(th.children) > 0 and isinstance(th.children[0],
                                                                          parso.python.tree.Name) and str(
            th.children[0].value) in ml_libs and len(th.children) > 1 and isinstance(th.children[1],
                                                                                     parso.python.tree.PythonNode) and \
                th.children[1].type == 'trailer' and len(th.children[1].children) > 1 \
                and isinstance(th.children[1].children[0], parso.python.tree.Operator) and th.children[1].children[
            0].value == '.' and isinstance(th.children[1].children[1], parso.python.tree.Name):

            for gh in th.children[1:]:
                iterate_python_node(gh, ml_libs, api_list)

            api_name = str(th.children[0].value)
            for yj in th.children:
                if isinstance(yj,parso.python.tree.PythonNode) and yj.type=='trailer' and  yj.children[0].value=='.':
                    api_name += '.'+yj.children[1].value
            api_list.add((api_name,th.children[0].line))


        elif th.type == 'atom_expr' and isinstance(th.children[0], parso.python.tree.Name) and th.children[
            0].value in ml_libs and isinstance(
            th.children[1], parso.python.tree.PythonNode) and th.children[1].type == 'trailer' and \
                th.children[1].children[0].value == '(':

            # yield from str(th.children[0].value)
            for gh in th.children[1:]:
                iterate_python_node(gh, ml_libs, api_list)
            api_list.add((str(th.children[0].value),th.children[0].line))


        elif th.type == 'simple_stmt' and isinstance(th.children[0], parso.python.tree.ExprStmt):
            iterate_python_node(th.children[0].get_rhs(), ml_libs, api_list)
        else:
            for gh in th.children:
                iterate_python_node(gh, ml_libs, api_list)
    elif isinstance(th, parso.python.tree.Operator) == False and isinstance(th, parso.python.tree.Name) == False and \
            isinstance(th, parso.python.tree.Keyword) == False and isinstance(th,
                                                                              parso.python.tree.Newline) == False and \
            isinstance(th, parso.python.tree.String) == False and isinstance(th, parso.python.tree.Number) == False and \
            isinstance(th, parso.python.tree.Param) == False and isinstance(th,
                                                                            parso.python.tree.EndMarker) == False and \
            isinstance(th, parso.python.tree.PythonErrorLeaf) == False and isinstance(th,
                                                                                      parso.python.tree.FStringStart) \
            == False and isinstance(th, parso.python.tree.FStringString) == False and isinstance(th,
                                                                                                 parso.python.tree.FStringEnd) == False:
        for yg in th.children:
            iterate_python_node(yg, ml_libs, api_list)

    return api_list


def compose_api_full_names(lib_names, import_details):
    #    as_name_lib = { for v in import_details }
    as_api = {}
    for t in import_details:
        for i, g in enumerate(t[1]):
            as_api[g] = t[2][i]

    real_api_name = []
    for ut in lib_names:
        as_name = ut[0].split('.')[0]
        rest = ut[0].split('.')[1:]
        real_api_name.append(((as_api[as_name] + '.' + '.'.join(rest)),ut[1]))

    return real_api_name

def read_csv_file(file_path):
    csv_content = csv.reader(open(file_path), delimiter=',')
    return [(th[0], th[1]) for th in csv_content][1:]  # return github clone links except the header of the csv file

def process(folder_path,csv_file):
    print("Processing",folder_path)
    projects_clone_link = read_csv_file(csv_file)
    project_path = folder_path +"/"+"TEMP/"
    api_paths = folder_path +"/"+"APIS/"
    if not os.path.exists(folder_path + "/TEMP"):
        os.makedirs(folder_path + "/TEMP")
    if not os.path.exists(folder_path + "/APIS"):
        os.makedirs(folder_path + "/APIS")
    updated_projects = [os.path.basename(x).split('.')[0] for x in glob.glob(api_paths + '*.txt')]
    for (project,clone_link) in projects_clone_link:
        if project in updated_projects:
            continue
        project_name = project.replace('/', '_')[:-4]
        project_name = project_name.replace('.', '_')

        ml_apis_projects=[]
        if clone_project(project_path, clone_link, project_name):
            projectpath = project_path + str(project_name)
            git_project = Util.MyGit(projectpath)
            pattern = "*.py"
            for path, go, files in os.walk(projectpath):
                for name in files:
                    if fnmatch(name, pattern):
                        try:
                            content = open(os.path.join(path, name),'r').read()
                            import_details = get_all_ml_imports(parso.parse(content))

                            if len(import_details) > 0:
                                new_as_names = reduce(operator.concat, [g[1] for g in import_details])
                                added_ml_apis = set()
                                get_func_names(content, new_as_names, added_ml_apis)
                                file_path = relpath(os.path.join(path, name), projectpath)
                                new_apis = compose_api_full_names(list(added_ml_apis), import_details)
                                for fg in new_apis:
                                    ml_apis_projects.append([fg[0], clone_link[
                                                                    :-4] + '/blob/' + git_project.get_last_commit() + '/' + file_path + '/#L' + str(
                                        fg[1])])
                        except UnicodeDecodeError as e:
                            print(e)
                        except FileNotFoundError as e:
                            print(e)

                                # print(projects_clone_link[project][:-4]+'/blob/'+git_project.get_last_commit()+'/'+file_path+'/#L'+str(fg[1]),fg[0])
                        # print(import_details)
        if len(ml_apis_projects)>0:
            Util.write_list_to_a_file(api_paths,project_name+'.txt',ml_apis_projects)
        else:
            print('invalid project ',project)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process Software 2.0.')
    parser.add_argument('PATH', type=str,
                        help='project download path')
    parser.add_argument('CSV_FILE', type=str,
                        help='CSV file with project and clone link')
    args = parser.parse_args()
    process(args.PATH,args.CSV_FILE)
