import os
from git import Repo
from fnmatch import fnmatch
import git
import ast
from datetime import datetime
import time
from datetime import datetime, date, timedelta
class MyGit():
    def __init__(self, location):
        self.repo = Repo(location)
        # self.repo.git.checkout("master", force=True)
        try:
            self.activeBranch = self.repo.active_branch
        except TypeError:
            self.repo.git.checkout("master", force=True)
            self.activeBranch = self.repo.active_branch
        self.commitList = sorted(self.repo.iter_commits(rev=self.activeBranch), key=lambda t: t.committed_date)
        self.map_Hex_commitDate = {x.hexsha: datetime(*time.gmtime(x.committed_date)[:3]) for x in self.commitList}
        self.map_hex_author_commiter = {
            x.hexsha: ((x.committer.name, x.committer.email), (x.author.name, x.author.email)) for x in self.commitList}
        self.comit_hex = [x.hexsha for x in self.commitList]

    def get_commit_date(self, commithex):
        return self.map_Hex_commitDate[commithex]

    def get_sorted_commit_hexlist(self):
        commits = [x.hexsha for x in self.commitList]
        return commits

    def get_last_commit(self):
        return self.comit_hex[-1]

    def get_author_details(self):
        author_list = {}
        author_list_new = {}
        for x in self.commitList:
            author_list.setdefault(x.committer.email, []).append(
                (x.hexsha, x.committer.name, datetime(*time.gmtime(x.committed_date)[:3])))

        for k, v in author_list.items():
            author_list_new[k] = ((v[-1][2] - v[0][2] + timedelta(days=1)).days, v[-1][2].strftime('%m/%d/%Y'), v[0][1])

        return author_list_new

    def checkout_commit(self, commitHex):
        self.repo.git.checkout(commitHex, force=True)

    def resetRepo(self):

        try:
            self.repo.git.checkout('.', force=False)
            self.repo.git.clean('-f')
            self.repo.git.checkout(self.activeBranch, force=True)
        except git.exc.GitCommandError as e:
            print(e)
        except UnicodeEncodeError as e:
            print(e)
        except UnicodeEncodeError as p:
            print(p)

    def get_all_commit_after(self, point):
        try:
            target_index = self.comit_hex.index(point) + 1
        except ValueError as e:
            target_index = None
        return self.comit_hex[target_index:]

    def get_commit_index(self, hex):
        try:
            target_index = self.comit_hex.index(hex)
        except ValueError as e:
            target_index = None
        return target_index

    def get_commit_hexBy_index(self, index):
        return self.commitList[index].hexsha

    def get_commiterAndAuthor(self, hex):
        return self.map_hex_author_commiter[hex]

    def get_last_commit_date(self):
        return self.map_Hex_commitDate[self.commitList[-1].hexsha]

    def get_first_commit_date(self):
        return self.map_Hex_commitDate[self.commitList[0].hexsha]

def is_req_file_exist(path: str) -> bool:  # Function to check whether a requirments.txt exists
    requirement = []
    req = 0
    pattern = "*.txt"
    requirement_names = ["requirement", "Requirement"]
    for path, subdirs, files in os.walk(path):
        for name in files:
            if fnmatch(name, pattern):
                for r in requirement_names:
                    if r in name:
                        requirement.append((os.path.join(path, name), name))
    return 1 if len(requirement) > 0 else 0


def get_requirmentfile_paths(path):
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


def write_list_to_a_file(destination_path, filename, list_container):
    print(destination_path, filename, )
    with open(destination_path + '/' + filename, 'w+') as file:
        for x in list_container:
            if type(x) == list:
                file.write(str(",".join(x)) + '\n')
            else:
                file.write(str(x) + '\n')
    file.close()


def write_dictionary_to_a_file(destination_path, filename, dic_container):
    with open(destination_path + '/' + filename, 'w+') as file:
        for x, y in dic_container.items():
            if type(y) == list:
                file.write(str(x) + "," + str(",".join(y)) + '\n')
            else:
                file.write(str(x) + "," + str(y) + '\n')
    file.close()


def get_library_names():
    return {'tensorflow': 'tensorflow',
            'keras': 'keras',
            'Keras-Preprocessing': 'keras',
            'sklearn': 'scikit-learn',
            'scikit-learn': 'scikit-learn',
            'theano': 'theano',
            'caffe': 'caffe',
            'caffe2': 'caffe',
            'scikit-image': 'scikit-learn',
            'pytorch': 'pytorch',
            'torch': 'pytorch',
            'torchvision': 'pytorch',
            'tensorflow-gpu': 'tensorflow',
            'tensorflow-tensorboard': 'tensorflow',
            'tensorflow-probability': 'tensorflow',
            'tensorflow-estimator': 'tensorflow',
            'tensorflow-metadata': 'tensorflow',
            'tensorflow_text': 'tensorflow',
            'tensorflow-datasets': 'tensorflow',
            'tensorflow_probability': 'tensorflow',
            'tensorflow-hub': 'tensorflow',
            'tensorflow-graphics': 'tensorflow',
            'tensorflow-model-analysis': 'tensorflow',
            'tensorflow-transform': 'tensorflow',
            'Theano': 'theano',
            'tensorboard': 'tensorflow',
            'theano-lstm': 'theano',
            'onnx_caffe2': 'caffe',
            'tensorflow_gpu': 'tensorflow',
            'tensorflow-model-optimization': 'tensorflow',
            'tensorflow_datasets': 'tensorflow'
            }


def get_ml_lib_name(lib_name):
    library_map = get_library_names()
    return library_map.get(lib_name)


def get_dependency_libs_of_ml_libs():
    return {'keras': ['Numpy', 'h5py', 'Keras-Applications', 'Keras-Preprocessing', 'numpy', 'PyYAML', 'scipy', 'six'],
            'tensorflow': ['Numpy', 'absl-py', 'astor	gast', 'google-pasta', 'grpcio', 'h5py', 'Keras-Applications',
                           'Keras-Preprocessing', 'Markdown', 'numpy', 'opt-einsum', 'protobuf', 'six', 'tensorboard',
                           'tensorflow-estimator', 'termcolor', 'Werkzeug', 'wrapt'],
            'caffe': ['Numpy', 'appnope', 'backcall', 'cycler', 'Cython', 'decorator', 'h5py', 'imageio', 'ipython',
                      'ipython-genutils', 'jedi', '	kiwisolver', 'leveldb', 'matplotlib', 'networkx', 'nose',
                      'numpy', 'pandas', 'parso', 'pexpect', 'pickleshare', 'Pillow', 'prompt-toolkit', 'protobuf',
                      'ptyprocess', 'Pygments', 'pyparsing', 'python-dateutil', 'python-gflags', 'pytz', 'PyWavelets',
                      'PyYAML', '	scikit-image', 'scipy', 'six', 'traitlets', 'wcwidth'],
            'pytorch': ['Numpy', 'numpy', 'Pillow', 'six', 'torchvision'],
            'theano': ['Numpy', "numpy", "scipy", "six"],
            'scikit-learn': ['Numpy', "joblib", "numpy", "scipy"]}


def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2 and value is not None]
    return lst3
