import os
from typing import List, Dict
import semgrepl
from semgrepl import tokei

class SemgreplObject:
    def __init__(self, match):
        self.file_path = "unresolved"
        self.metavars = {}
        if match:
            self.match = match
            self.start = match['start']
            self.end = match['end']
            self.file_path = match['path']
            self.metavars = match['extra']['metavars']


    @property
    def location(self):
        return "{}:{}".format(self.file_path, self.start['line'])

class SemgreplImport(SemgreplObject):
    def __init__(self, match):
        super().__init__(match)

        if '$MODULE' in self.metavars:
            self.import_path = self.metavars['$MODULE']['abstract_content']
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
        self.name = function_name
        self.instance = None

        if '$INSTANCE' in self.metavars:
            self.instance = self.metavars['$INSTANCE']['abstract_content']

        if '$NAME' in self.metavars:
            self.name = self.metavars['$NAME']['abstract_content']

    def __repr__(self):
        return "<SemgreplFunctionCall file_path={} name={} instance={}>".format(self.file_path, self.name, self.instance)

    def __hash__(self):
        return hash(self.file_path + self.name)

    def __eq__(self, other):
        return self.file_path == other.file_path and self.name == other.name

class SemgreplFunctionDef(SemgreplObject):
    def __init__(self, match, function_name=None):
        super().__init__(match)

        if function_name != "$X":
            self.name = function_name
        elif '$X' in self.metavars:
            self.name = self.metavars['$X']['abstract_content']
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

        # The name of the parent class, if any.
        self.parent_name = None

        # The resolved parent class object, if any.
        self.parent_class = None

        if class_name != "$NAME":
            self.name = class_name
        elif '$NAME' in self.metavars:
            self.name = self.metavars['$NAME']['abstract_content']
        else:
            print("Failed on file: " + self.file_path)
            self.name = "FAILED"

        if '$PARENT' in self.metavars:
            self.parent_name = self.metavars['$PARENT']['abstract_content']

        # The fully-qualified name of the class.
        # Defaults to class name, language-specific subclasses of SemgreplClass
        # may change this.
        self.qualified_name = self.name

    def __repr__(self):
        return "<SemgreplClass file_path={} name={}".format(self.file_path, self.name)

    def __hash__(self):
        return hash(self.file_path + self.name)

    def __eq__(self, other):
        return self.file_path == other.file_path and self.name == other.name

class SemgreplPythonClass(SemgreplClass):
    def __init__(self, match, class_name):
        super().__init__(match, class_name)

        self.qualified_name = os.path.basename(
            os.path.splitext(self.file_path)[0] +
            "." +
            self.name
        )

        if self.parent_name:
            self.parent_name = self.parent_name.replace(" ", ".")


def class_factory(match, class_name):
    if match['check_id'] == "tmp.python-class":
        return SemgreplPythonClass(match, class_name)
    else:
        return SemgreplClass(match, class_name)

class SemgreplString(SemgreplObject):
    def __init__(self, match):
        super().__init__(match)

        if '$X' in self.metavars:
            self.name = self.metavars['$X']['abstract_content']
        else:
            print("Failed on file: " + self.file_path)
            self.name = "FAILED"

    def __repr__(self):
        return "<SemgreplString file_path={} name={}".format(self.file_path, self.name)

    def __hash__(self):
        return hash(self.file_path + self.name)

    def __eq__(self, other):
        return self.file_path == other.file_path and self.name == other.name
