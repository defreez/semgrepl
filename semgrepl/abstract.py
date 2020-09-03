import os
from typing import List, Dict
import semgrepl
from semgrepl import tokei

class SemgreplObject:
    def __init__(self, match):
        self.start = match['start']
        self.end = match['end']
        self.match = match
        self.file_path = match['path']

    @property
    def location(self):
        return "{}:{}".format(self.file_path, self.start['line'])

class SemgreplImport(SemgreplObject):
    def __init__(self, match):
        super().__init__(match)

        metavars = match['extra']['metavars']
        if '$MODULE' in metavars:
            self.import_path = metavars['$MODULE']['abstract_content']
        else:
            print("Failed on file: " + self.file_path)
            self.import_path = "FAILED"

    def __repr__(self):
        return "<SemgreplImport file_path={} import_path={}>".format(self.file_path, self.import_path)

    def __hash__(self):
        return hash(self.import_path + self.file_path)

    def __eq__(self, other):
        return self.file_path == other.file_path and self.import_path == other.import_path

class SemgreplFunctionCall(SemgreplObject):
    def __init__(self, function_name, match):
        super().__init__(match)
        metavars = match['extra']['metavars']
        self.name = function_name
        self.instance = None

        if '$INSTANCE' in metavars:
            self.instance = metavars['$INSTANCE']['abstract_content']

        if '$NAME' in metavars:
            self.name = metavars['$NAME']['abstract_content']

    def __repr__(self):
        return "<SemgreplFunctionCall file_path={} name={} instance={}>".format(self.file_path, self.name, self.instance)

    def __hash__(self):
        return hash(self.file_path + self.name)

    def __eq__(self, other):
        return self.file_path == other.file_path and self.name == other.name

class SemgreplFunctionDef(SemgreplObject):
    def __init__(self, match, function_name=None):
        super().__init__(match)
        metavars = match['extra']['metavars']

        if function_name != "$X":
            self.name = function_name
        elif '$X' in metavars:
            self.name = metavars['$X']['abstract_content']
        else:
            print("Failed on file: " + self.file_path)
            self.name = "FAILED"

    @property
    def annotations(self):
        annotations = []
        lines = self.match['extra']['lines']
        for l in lines.split("\n"):
            if "@" in l:
                annotations.append(l.strip())
        return annotations

    def __repr__(self):
        return "<SemgreplFunctionDef file_path={} name={}>".format(self.file_path, self.name)

    def __hash__(self):
        return hash(self.file_path + self.name)

    def __eq__(self, other):
        return self.file_path == other.file_path and self.name == other.name

class SemgreplClass(SemgreplObject):
    def __init__(self, match, class_name=None):
        super().__init__(match)
        metavars = match['extra']['metavars']

        self.parent = None

        if class_name != "$NAME":
            self.name = class_name
        elif '$NAME' in metavars:
            self.name = metavars['$NAME']['abstract_content']
        else:
            print("Failed on file: " + self.file_path)
            self.name = "FAILED"

        if '$PARENT' in metavars:
            self.parent = metavars['$PARENT']['abstract_content']

        #self.qualified_name = " ".join(os.path.basename().split(".")) + " " + self.name

    def __repr__(self):
        return "<SemgreplClass file_path={} name={}".format(self.file_path, self.name)

    def __hash__(self):
        return hash(self.file_path + self.name)

    def __eq__(self, other):
        return self.file_path == other.file_path and self.name == other.name

class PythonClass(SemgreplClass):
    def __init__():
        pass

class SemgreplString(SemgreplObject):
    def __init__(self, match):
        super().__init__(match)
        metavars = match['extra']['metavars']

        if '$X' in metavars:
            self.name = metavars['$X']['abstract_content']
        else:
            print("Failed on file: " + self.file_path)
            self.name = "FAILED"

    def __repr__(self):
        return "<SemgreplString file_path={} name={}".format(self.file_path, self.name)

    def __hash__(self):
        return hash(self.file_path + self.name)

    def __eq__(self, other):
        return self.file_path == other.file_path and self.name == other.name
