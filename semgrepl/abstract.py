import os
from typing import List, Dict
import semgrepl
from semgrepl import tokei

class SemgreplObject:
    pass

class SemgreplImport(SemgreplObject):
    def __init__(self, match):
        metavars = match['extra']['metavars']
        self.file_path = match['path']
        self.start = match['start']
        self.end = match['end']
        self.match = match

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
        metavars = match['extra']['metavars']
        self.file_path = match['path']
        self.start = match['start']
        self.end = match['end']
        self.name = function_name
        self.instance = None
        self.match = match

        if '$INSTANCE' in metavars:
            self.instance = metavars['$INSTANCE']['abstract_content']

        if '$NAME' in metavars:
            self.name = metavars['$NAME']['abstract_content']

    @property
    def location(self):
        return "{}:{}".format(self.file_path, self.start['line'])

    def __repr__(self):
        return "<SemgreplFunctionCall file_path={} name={} instance={}>".format(self.file_path, self.name, self.instance)

    def __hash__(self):
        return hash(self.file_path + self.name)

    def __eq__(self, other):
        return self.file_path == other.file_path and self.name == other.name

class SemgreplFunctionDef(SemgreplObject):
    def __init__(self, match, function_name=None):
        metavars = match['extra']['metavars']
        self.file_path = match['path']
        self.start = match['start']
        self.end = match['end']
        self.match = match

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

    @property
    def location(self):
        return "{}:{}".format(self.file_path, self.start['line'])

    def __repr__(self):
        return "<SemgreplFunctionDef file_path={} name={}>".format(self.file_path, self.name)

    def __hash__(self):
        return hash(self.file_path + self.name)

    def __eq__(self, other):
        return self.file_path == other.file_path and self.name == other.name

class SemgreplClass(SemgreplObject):
    def __init__(self, match, class_name=None):
        self.file_path = match['path']
        metavars = match['extra']['metavars']
        self.match = match

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

    def __repr__(self):
        return "<SemgreplClass file_path={} name={}".format(self.file_path, self.name)

    def __hash__(self):
        return hash(self.file_path + self.name)

    def __eq__(self, other):
        return self.file_path == other.file_path and self.name == other.name

class SemgreplString(SemgreplObject):
    def __init__(self, match):
        self.file_path = match['path']
        metavars = match['extra']['metavars']
        self.match = match

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
