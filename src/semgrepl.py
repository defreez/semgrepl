import os
import tokei
from typing import List, Dict

class SemgreplObject:
    pass

# Decision: is it worth having custom Python classes for everything?
#   Convenient but feels like it is duplicating a lot.

class SemgreplImport(SemgreplObject):
    def __init__(self, match):
        metavars = match['extra']['metavars']
        self.file_path = match['path']
        self.start = match['start']
        self.end = match['end']
        self.match = match

        if '$X' in metavars:
            self.import_path = metavars['$X']['abstract_content']
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

        if '$X' in metavars:
            self.instance = metavars['$X']['abstract_content']

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

        if class_name != "$X":
            self.name = class_name
        elif '$X' in metavars:
            self.name = metavars['$X']['abstract_content']
        else:
            print("Failed on file: " + self.file_path)
            self.name = "FAILED"

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


##########
# Config #
##########

# Default to the rules dir in this repo
DEFAULT_RULES_DIR = os.path.abspath(os.path.join('..', 'rules'))

# TODO: should infer this from semgrep somehow
SEMGREP_SUPPORTED_LANGUAGES = ["python", "golang", "java", "javascript", "ruby"]

# A default pack that runs all security rules
SEMGREP_RULES_ALL_SECURITY = "https://semgrep.dev/p/r2c-security-audit"

# Creating global vars #yoloswag
config = None

# Run at the beginning of your session to set up your target
def semgrepl_init(target, rules_dir = DEFAULT_RULES_DIR, default_language = None):
    global config
    config = SemgreplConfig([target], rules_dir, default_language)
    print("[~] Printing languages used in target repos")

# Run at the beginning of your session to set up your target
# Adds a whole dir to targets
def semgrepl_init_dir(target_dir, rules_dir = DEFAULT_RULES_DIR, default_language = None):
    global config
    import glob
    dirs = glob.glob(target_dir)
    if len(dirs) == 0:
        print("[!] Error: provided glob did not match any dirs")
        print("Note that characters like ~ are not expanded")
        print("glob.glob is used from: https://docs.python.org/3/library/glob.html")
        print()
        return
    config = SemgreplConfig(dirs, rules_dir, default_language)


class SemgreplConfig:
    def __init__(self, targets, rules_dir = "", default_language = None):
        self.rules_dir = os.path.abspath(rules_dir)
        self.default_language = default_language

        self.targets = targets

        # Make all targets absolute paths
        self.targets = [os.path.abspath(x) for x in targets]

        self.languages_used = {}

        # Run tokei on all targets
        print("[*] Determining languages used in target repos...")
        for target in self.targets:
            # for ease of reference, just have the base dirname of the repo
            # be the key
            key = os.path.basename(target)
            self.languages_used[key] = tokei.Tokei.run(target)
        print("     ...done")
        print()

        # self.languages is the union list of languages used in any repo
        # in [targets] that semgrep can currently parse
        self.languages = self.semgrep_supported_langs_any_repo(self.languages_used)

        self.print_languages_used()


    def print_languages_used(self):
        for repo, tokei_output in self.languages_used.items():
            print("[*] {}".format(repo))
            tokei_output.print_languages_used()
            print()

    def __repr__(self):
        return "<SemgreplConfig rules_dir={}, default_language={}, targets={}, languages_used={}".format(
            self.rules_dir, self.default_language, self.targets,
            self.languages_used)

    def semgrep_supported_langs_any_repo(self, langs: Dict[str, tokei.TokeiOutput]):
        result = set()
        for repo, tokei_output in langs.items():

            for lang in tokei_output.language_names:
                if lang.lower() in SEMGREP_SUPPORTED_LANGUAGES:
                    result.add(lang.lower())

        return list(result)

