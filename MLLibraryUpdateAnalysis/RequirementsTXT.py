import glob
import json
import os
from datetime import datetime
import Util
import requirements
import requirements as rm
import pkg_resources

class Requirements:
    def __init__(self, file_location):
        self.file_location = file_location

    def getAllDependancyNames(self):
        file = open(self.file_location, 'r')
        library_names = []

        for r in file:
            try:
                req = list(rm.parse(r))
                for u in req:
                    if self.get_ml_lib_name(u.name) is None:
                        library_names.append(u.name)
                    else:
                        library_names.append(self.get_ml_lib_name(u.name))
            except pkg_resources.RequirementParseError as e:
                qq = self.repair_requirment_specification(r)
                if qq is not None:
                    try:
                        req = list(rm.parse(qq))
                        for u in req:
                            if self.get_ml_lib_name(u.name) is None:
                                library_names.append(u.name)
                            else:
                                library_names.append(self.get_ml_lib_name(u.name))
                    except pkg_resources.RequirementParseError as e:
                        pass
            except FileNotFoundError as e:
                pass
            except ValueError as e:
                pass
        return [g for g in library_names if g is not None]

    @staticmethod
    def get_library_name_and_version(specification):
        req = None
        try:
            req = list(rm.parse(specification))
        except pkg_resources.RequirementParseError as e:
            qq = Requirements.repair_requirment_specification(specification)
            if qq is not None:
                try:
                    req = list(rm.parse(qq))
                except pkg_resources.RequirementParseError as e:
                    pass
                except FileNotFoundError as e:
                    pass
                except ValueError as e:
                    pass

        except FileNotFoundError as e:
            pass
        except ValueError as e:
            pass
        update = []
        if req is not None:
            for w in req:
                update.append((w.name, w.specs))

        return update

    @staticmethod
    def repair_requirment_specification(q):
        if q.count('=') == 1 and q.count('<') == 0 and q.count('>') == 0 and q.count('!') == 0 and q.count('~') == 0:
            zz = q.replace('=', '==')
            return zz
        if q.count("'") == 2:
            return q.replace("'", "")
        if q.count("=>") == 1:
            return q.replace("=>", ">=")
        if q.count("=<") == 1:
            return q.replace("=<", "<=")
        return None

    @staticmethod
    def get_ml_lib_name(lib_name):
        library_map = {'tensorflow': 'tensorflow',
                       'keras': 'keras',
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
                       'tensorboard': 'tensorflow',
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
                       'theano': 'theano',
                       'Keras-Preprocessing':'keras',
                       'theano-lstm': 'theano',
                       'onnx_caffe2': 'caffe',
                       'tensorflow_gpu': 'tensorflow',
                       'tensorflow_datasets': 'tensorflow'
                       }
        return library_map.get(lib_name)


def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2 and value is not None]
    return lst3


def get_version_for_library_updates(req_file_):
    file = glob.glob(req_file_ + '*.json')
    print(len(file), 'files selected')
    ml_updates = {}
    non_ml_updates = {}
    for g in file:  ##iterate each project
        project = os.path.basename(g).split('.')[0]
        ml_library_update = {}
        non_ml_library_update = {}
        with open(g, 'r') as json_data:
            d = json.loads(json_data.read())
            for t in d:  ##iterate each update
                code_addition = [g for g in t["CODE_DIFF"]['Addition'] if g is not None]
                code_deletion = [g for g in t["CODE_DIFF"]['Deletion']]

                if len(code_addition) is not 0 and len(code_deletion) is not 0:
                    added_libraries = []
                    deleted_libraries = []
                    for q in code_addition:
                        q = q.strip()
                        additions = Requirements.get_library_name_and_version(q)
                        if len(additions) is not 0:
                            added_libraries += [yt for yt in additions if yt[0] is not None]
                    for q in code_deletion:
                        q = q.strip()
                        deletions = Requirements.get_library_name_and_version(q)
                        if len(deletions) is not 0:
                            deleted_libraries += [yt for yt in deletions if yt[0] is not None]
                    updated_libs = []
                    if len(added_libraries) is not 0 and len(deleted_libraries) is not 0:
                        updated_libs = intersection([r[0] for r in added_libraries], [r[0] for r in deleted_libraries])
                    added_libraries_map = {}
                    for gu in added_libraries:
                        added_libraries_map[gu[0]] = gu[1]
                    deleted_libraries_map = {}
                    for gu in deleted_libraries:
                        deleted_libraries_map[gu[0]] = gu[1]

                    for libs in updated_libs:
                        if Requirements.get_ml_lib_name(libs) is not None:
                            ml_library_update.setdefault(Requirements.get_ml_lib_name(libs), []).append(
                                (deleted_libraries_map[libs], added_libraries_map[libs], t["HEX"]))  ## deleted first

                    for libs in updated_libs:
                        if libs is not None and Requirements.get_ml_lib_name(libs) is None:
                            non_ml_library_update.setdefault(libs, []).append(
                                (deleted_libraries_map[libs], added_libraries_map[libs], t["HEX"]))

        if len(non_ml_library_update) > 0:
            non_ml_updates[project] = non_ml_library_update
        if len(ml_library_update) > 0:
            ml_updates[project] = ml_library_update

    return ml_updates, non_ml_updates


def get_dates_for_library_updates(req_file_history_location: object) -> object:
    file = glob.glob(req_file_history_location + '*.json')
    print(len(file), 'files selected')
    # print(len(list(filter(lambda x: True if len(json.loads(open(x, 'r').read())) > 1 else False,file))))
    updates = {}
    for g in file:
        project = os.path.basename(g).split('.')[0]
        with open(g, 'r') as json_data:
            d = json.loads(json_data.read())

            for t in d:
                com_date = datetime.strptime(t["Com_Date"], "%m/%d/%Y, %H:%M:%S")
                hex = t["HEX"]
                code_addition = t["CODE_DIFF"]['Addition']
                code_deletion = t["CODE_DIFF"]['Deletion']
                additions = set()
                deletion = set()
                if code_addition is not "" and code_deletion is not "":

                    for q in code_addition:
                        q = q.strip()
                        try:
                            req = list(requirements.parse(q))
                            for u in req:
                                if Util.get_ml_lib_name(u.name) is None:
                                    additions.add(u.name)
                                else:
                                    additions.add(Util.get_ml_lib_name(u.name))
                        except pkg_resources.RequirementParseError as e:
                            qq = Requirements.repair_requirment_specification(q)
                            if qq is not None:
                                try:
                                    req = list(requirements.parse(qq))
                                    for u in req:
                                        if Util.get_ml_lib_name(u.name) is None:
                                            additions.add(u.name)
                                        else:
                                            additions.add(Requirements.get_ml_lib_name(u.name))
                                except pkg_resources.RequirementParseError as e:
                                    pass

                            else:
                                pass
                                # print(e)
                                # print(q,qq,code_addition)
                                # print(g)
                        except FileNotFoundError as e:
                            pass
                        except ValueError as e:
                            pass

                    for q in code_deletion:
                        try:
                            req = list(requirements.parse(q))
                            for u in req:
                                if Util.get_ml_lib_name(u.name) is None:
                                    deletion.add(u.name)
                                else:
                                    deletion.add(Util.get_ml_lib_name(u.name))
                        except pkg_resources.RequirementParseError as e:
                            q = Requirements.repair_requirment_specification(q)
                            if q is not None:
                                try:
                                    req = list(requirements.parse(q))
                                    for u in req:
                                        if Util.get_ml_lib_name(u.name) is None:
                                            deletion.add(u.name)
                                        else:
                                            deletion.add(Util.get_ml_lib_name(u.name))
                                except pkg_resources.RequirementParseError as p:
                                    pass
                            else:
                                pass
                                # print(e)
                                # print(q, code_addition)
                                # print(g)

                        except FileNotFoundError as e:
                            pass
                        except ValueError as e:
                            pass

                if len(deletion) > 0 and len(additions) > 0:
                    if len(intersection(additions, deletion)) != 0:
                        updates.setdefault(project, []).append((com_date, intersection(additions, deletion),hex))
            #    print(com_date, additions, deletion)
    return updates
