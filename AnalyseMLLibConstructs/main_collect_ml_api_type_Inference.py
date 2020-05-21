import os
from fnmatch import fnmatch
import ast
import jedi
import json
import argparse
import csv
import git

flatten = lambda l: [item for sublist in l for item in sublist]
curunt_file = []
function_jsons = []


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


def getNameOfAllMLPythonScripts(projct_path, csv):
    projct_clone = read_csv_file(csv)

    projects_path = projct_path + "/" + "TEMP/"
    api_paths = projct_path + "/" + "APIS/"
    if not os.path.exists(projct_path + "/TEMP"):
        os.makedirs(projct_path + "/TEMP")
    if not os.path.exists(projct_path + "/APIS"):
        os.makedirs(projct_path + "/APIS")

    for (project, link) in projct_clone:
        project_name = project.replace('/', '_')[:-4]
        project_name = project_name.replace('.', '_')
        if clone_project(projects_path, link, project_name):
            project_path = projects_path + "/" + project_name + "/"
        global function_jsons
        function_jsons = []
        pattern = "*.py"
        a = 0;
        for path, subdirs, files in os.walk(project_path):
            for name in files:
                if fnmatch(name, pattern):
                    a = a + 1
                    # get_open_fds()
                    root = ast.parse(open(os.path.join(path, name), 'r').read(), os.path.join(path, name))

                    if (len(analyzeImportStmt(root)) > 0):
                        curunt_file.insert(0, os.path.join(path, name))
                        print("Start Processing " + os.path.join(path, name))
                        AllVisitors().visit(root)

                        print(os.path.join(path, name))
                        if len(function_jsons) == 0:
                            with open(project + "_" + str(a) + ".json", 'w') as f:
                                print("function_jsons")
                                f.write(os.path.join(path, name))
                                f.close()
                        else:
                            with open(project + "_" + str(a) + ".json", 'w') as f:
                                print("function_jsons")
                                f.write(json.dumps(function_jsons))
                                f.close()

                            with open(project + "_" + str(a) + ".json", 'r') as f:
                                x = f.read()
                                print(json.loads(x))


def analyzeImportStmt(root):
    importStatements = []
    mllibs = ['tensorflow', 'keras', 'torch', 'sklearn', 'theano', 'caffe', 'h2o']

    for node in ast.iter_child_nodes(root):

        im = ()
        if isinstance(node, ast.Import):
            for x in node.names:
                for y in (x.name.split('.')):
                    if (y in mllibs):
                        im = (x.name, x.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                for x in node.module.split('.'):
                    if x in mllibs:
                        for y in node.names:
                            im = (node.module, y.name, y.asname)
        else:
            continue
        if (len(im) > 0):
            importStatements.append(im)
    return importStatements


class AllVisitors(ast.NodeVisitor):  # class Call(func, args, keywords, starargs, kwargs)
    # mllibs = ['tensorflow', 'keras', 'torch', 'sklearn', 'theano', 'caffe', 'h2o']

    Func_Calls = []

    def visit_Call(self, node):
        print(str(node.func) + " ROW " + str(node.lineno) + " CLM " + str(node.col_offset))
        assert (type(node.func) == ast.Name or type(node.func) == ast.Attribute or type(node.func) == ast.Subscript or
                type(node.func) == ast.Call)
        json_info = {}
        method_full_name = ""
        if isinstance(node.func, ast.Name):  # Not relevent to us
            print("DIRECT CALL FUNC :" + str(node.func.id))
            print("File :" + curunt_file[0])
            with open(curunt_file[0], 'r') as f:
                source = f.read()
                # source = open(curunt_file[0], "r").read()

                script = jedi.Script(source, node.lineno, node.col_offset)
                defs = script.goto_definitions()
                if len(defs) == 0:
                    print("Error: No defs found")

                for x in defs:
                    print("GOTO DEFS : " + str(x.full_name))
                    for y in ['tensorflow', 'keras', 'torch', 'sklearn', 'theano', 'caffe', 'h2o']:
                        if y in x.full_name:
                            if (len(defs) > 1):  # If more than one def found, continue
                                continue
                            print("FULL NAME :" + x.full_name)
                            method_full_name = x.full_name
                            json_info.update({'full_name': x.full_name})
                            json_info.update({'filename': curunt_file[0]})
                f.close()
                del (source)
        elif isinstance(node.func, ast.Attribute):
            fully_qulified_name = []
            # source = open(curunt_file[0], "r").read()
            print("FUNC ID RECEIVER :" + str(node.func.attr))
            print("File :" + curunt_file[0])
            if (isinstance(node.func.value, ast.Attribute)):
                col_length = node.col_offset + len(node.func.attr) + getColumnLength(node.func.value)
            else:
                col_length = node.col_offset + len(node.func.attr)
            print("COL_LENGTH " + str(col_length))
            # script = jedi.Script(source, node.lineno, node.col_offset+len(node.func.attr)+1)
            with open(curunt_file[0], 'r') as f:
                source = jedi.Script(f.read(), node.lineno, col_length)

                defs = source.goto_definitions()
                if (len(defs) == 0):
                    print("Error: No defs found")

                for x in defs:
                    print("FULL NAME :" + x.full_name)
                    for y in ['tensorflow', 'keras', 'torch', 'sklearn', 'theano', 'caffe', 'h2o']:
                        if y in x.full_name:
                            if (len(defs) > 1):  # If more than one def found, continue
                                continue
                            print("FULL NAME :" + x.full_name)
                            method_full_name = x.full_name
                            print("Code- " + x.get_line_code())

                            try:
                                print(x.params)
                                parameters = []
                                for y in x.params:
                                    para = {}
                                    para.update({"Name": y.name})
                                    para.update({"Type": y.type})
                                    para.update({"Description": y.type})
                                    para.update({"Line Code": str(y.get_line_code())})
                                    para.update({"Full name": y.full_name})
                                    parameters.append(para)
                                json_info.update({'Parameters': parameters})
                            except AttributeError as e:
                                print(e)
                            json_info.update({'full_name': x.full_name})
                            json_info.update({'filename': curunt_file[0]})
                self.Func_Calls.append(fully_qulified_name)
                f.close()
                del (source)
        elif isinstance(node.func, ast.Subscript):
            print("Subscript")
        elif isinstance(node.func, ast.Call):
            print("Call")
        else:
            assert (0)

        if method_full_name != "":
            argument = []
            json_info.update({"Number of Po Arg": len(node.args)})
            json_info.update({"Number of KeyWords": len(node.keywords)})
            for x in node.args:
                arg = {}

                if isinstance(x, ast.List):
                    print("elts")
                    print(x.elts)
                    arg.update({"Arg Value": str(x.elts)})
                    arg.update({"Arg Type": "ast.List"})
                    arg.update({"Arg CTX": str(x.ctx)})
                elif isinstance(x, ast.Name):
                    print(x.id)
                    arg.update({"Arg Value": str(x.id)})
                    arg.update({"Arg Type": ""})
                    arg.update({"Arg CTX": str(x.ctx)})
                elif isinstance(x, ast.Attribute):
                    if (isinstance(x.value, ast.Name)):
                        arg.update({"Arg Value": str(x.value.id)})
                    else:
                        print(x.value)
                        arg.update({"Arg Value": ""})
                    arg.update({"Arg Type": "ast.Attribute"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x, ast.Call):
                    if (isinstance(x.func, ast.Attribute)):
                        arg.update({"Arg Value": str(x.func.attr)})
                        arg.update({"Arg Type": "ast.Call"})
                        arg.update({"Arg CTX": ""})
                    elif (isinstance(x.func, ast.Name)):
                        arg.update({"Arg Value": str(x.func.id)})
                        arg.update({"Arg Type": "ast.Call"})
                        arg.update({"Arg CTX": ""})
                    else:
                        arg.update({"Arg Value": str(x.func)})
                        arg.update({"Arg Type": "ast.Call"})
                        arg.update({"Arg CTX": ""})
                elif isinstance(x, ast.Str):
                    arg.update({"Arg Value": str(x.s)})
                    arg.update({"Arg Type": "String"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x, ast.Subscript):
                    arg.update({"Arg Value": str(x.value)})
                    arg.update({"Arg Type": str(type(x))})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x, ast.NameConstant):
                    arg.update({"Arg Value": str(x.value)})
                    arg.update({"Arg Type": "ast.Constant"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x, ast.Num):
                    arg.update({"Arg Value": str(x.n)})
                    arg.update({"Arg Type": "ast.Num"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x, ast.BinOp):
                    arg.update({"Arg Value": str(x.left) + str(x.op) + str(x.right)})
                    arg.update({"Arg Type": "ast.BinOp"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x, ast.Dict):
                    arg.update({"Arg Value": str(x.keys) + str(x.values)})
                    arg.update({"Arg Type": "ast.Dict"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x, ast.UnaryOp):
                    arg.update({"Arg Value": str(x.op) + str(x.operand)})
                    arg.update({"Arg Type": "ast.UnaryOp"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x, ast.ListComp):
                    arg.update({"Arg Value": str(x.elt) + str(x.generators)})
                    arg.update({"Arg Type": "ast.ListComp"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x, ast.Tuple):
                    arg.update({"Arg Value": str(x.elts)})
                    arg.update({"Arg Type": "ast.Tuple"})
                    arg.update({"Arg CTX": str(x.ctx)})
                elif isinstance(x, ast.Subscript):
                    arg.update({"Arg Value": str(x.value.id)})
                    arg.update({"Arg Type": ""})
                    arg.update({"Arg CTX": str(x.value.ctx)})
                elif isinstance(x, ast.Lambda):
                    arg.update({"Arg Value": str(x.body)})
                    arg.update({"Arg Type": "ast.Lambda"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x, ast.Compare):
                    arg.update({"Arg Value": str(x.left) + str(x.ops) + str(x.comparators)})
                    arg.update({"Arg Type": "ast.Compare"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x, ast.Starred):
                    arg.update({"Arg Value": str(x.value)})
                    arg.update({"Arg Type": "ast.Starred"})
                    arg.update({"Arg CTX": str(x.ctx)})
                else:
                    print(x)
                    assert (0)
                argument.append(arg)
            print("Number of Arguments :" + str(len(node.args)))
            print("Number of Keyword arguments : " + str(len(node.keywords)))
            json_info.update({"Argument": argument})

            key_word_argu = []
            for x in node.keywords:  # keywords holds a list of keyword objects representing arguments passed by keyword.
                arg = {}

                print(x.arg)  # Don't care about the value
                arg.update({"Key": str(x.arg)})
                if isinstance(x.value, ast.Name):
                    arg.update({"Value": str(x.value.id)})
                    arg.update({"CTX": str(x.value.ctx)})
                    arg.update({"Arg Type": ""})
                elif isinstance(x.value, ast.Str):
                    arg.update({"Arg Type": "String"})
                    arg.update({"Value": str(x.value.s)})
                    arg.update({"CTX": ""})
                elif isinstance(x.value, ast.Subscript):
                    if (isinstance(x.value.value, ast.Name)):
                        arg.update({"Arg Value": str(x.value.value.id)})
                        arg.update({"Arg Type": type(x.value.value)})
                        arg.update({"Arg CTX": str(x.value.value.ctx)})
                    else:
                        arg.update({"Arg Value": str(x.value)})
                        arg.update({"Arg Type": str(type(x.value.value))})
                        arg.update({"Arg CTX": ""})
                elif isinstance(x.value, ast.Attribute):
                    arg.update({"Arg Value": str(x.value.attr)})
                    arg.update({"Arg Type": "ast.Attribute"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x.value, ast.Call):
                    arg.update({"Arg Value": str(x.value.func)})
                    arg.update({"Arg Type": "ast.Call"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x.value, ast.NameConstant):
                    arg.update({"Arg Value": str(x.value.value)})
                    arg.update({"Arg Type": "ast.Constant"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x.value, ast.Num):
                    arg.update({"Arg Value": str(x.value.n)})
                    arg.update({"Arg Type": "ast.Num"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x.value, ast.UnaryOp):
                    arg.update({"Arg Value": ""})
                    arg.update({"Arg Type": "UnaryOp"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x.value, ast.Tuple):
                    arg.update({"Arg Value": str(x.value.elts)})
                    arg.update({"Arg Type": "ast.Tuple"})
                    arg.update({"Arg CTX": str(x.value.ctx)})
                elif isinstance(x.value, ast.Dict):
                    arg.update({"Arg Value": "Keys=" + str(x.value.keys) + " Values=" + str(x.value.keys)})
                    arg.update({"Arg Type": "ast.Dict"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x.value, ast.List):
                    arg.update({"Arg Value": str(x.value.elts)})
                    arg.update({"Arg Type": "ast.List"})
                    arg.update({"Arg CTX": str(x.value.ctx)})
                elif isinstance(x.value, ast.Lambda):
                    arg.update({"Arg Value": str(x.value.body)})
                    arg.update({"Arg Type": "ast.Lambda"})
                    arg.update({"Arg CTX": ""})
                elif isinstance(x.value, ast.BinOp):
                    arg.update({"Arg Value": str(x.value.left) + str(x.value.op) + str(x.value.right)})
                    arg.update({"Arg Type": "ast.BinOp"})
                    arg.update({"Arg CTX": ""})
                else:
                    print("fuck")
                    print(x.value)
                    assert (0)
                key_word_argu.append(arg)
            json_info.update({"Key_Word_Arguments": key_word_argu})
            json_info.update({"Row": node.lineno})
            json_info.update({"Col_offset": node.col_offset})
            print(json_info)
            function_jsons.append(json_info)

        # for a in node.args:
        #     if isinstance(a,ast.IfExp):
        #         ifIFNode(n=a)
        #     elif isinstance(a,ast.Num):
        #         print (a.n)
        #     elif isinstance(a,ast.Name):
        #         ifNameNode(a,[])
        #     elif isinstance(a,ast.Call):
        #         pass
        #     elif isinstance(a,ast.BinOp):
        #         pass
        #     else:
        #         print (a)
        #         assert()

        # if node.starargs:  TODO : Turn-on this for Python 2.5
        #     print ("Star argument ")
        #     exit (0)
        #
        # if node.kwargs:
        #     print ("Kwargs argument ")
        #     exit (0)

        self.generic_visit(node)


def getColumnLength(x):
    if (isinstance(x, ast.Attribute)):
        return len(x.attr) + getColumnLength(x.value)
    if (isinstance(x, ast.Name)):
        return len(x.id)


def read_csv_file(file_path):
    csv_content = csv.reader(open(file_path), delimiter=',')
    return [(th[0], th[1]) for th in csv_content][1:]  # return github clone links except the header of the csv file


if __name__ == '__main__':
    # selectProjectList()
    parser = argparse.ArgumentParser(description='Process Software 2.0.')
    parser.add_argument('REPO_PATH', type=str,
                        help='project path')
    parser.add_argument('CSV', type=str,
                        help='CSV file with project and clone link')
    args = parser.parse_args()

    getNameOfAllMLPythonScripts(args.REPO_PATH, args.CSV)
