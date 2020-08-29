import json
import os
import subprocess
from typing import Dict

class TokeiOutput:
    def __init__(self, data: Dict[str, str], repo_path):
        self.target = repo_path
        self.data = {}
        for lang_key, detail_dict in data.items():
            self.data[lang_key] = TokeiLanguageInfo(detail_dict, repo_path)

    @property
    def language_names(self):
        return list(self.data.keys())

    def __repr__(self):
        return "<TokeiOutput target='{}' data={}>".format(self.target,
            self.data)

    @property
    def languages_by_frequency(self):
        # [(lang1, tokeiLanguageInfo), (lang2, ...)]
        return sorted(self.data.items(), key=lambda x: x[1].code, reverse=True)

    # print to STDOUT an unformatted table of languages in descending order
    # TODO: should probably use pandas or at least format the spacing so
    # it's easier to read.
    def print_languages_used(self):
        # sort by most code
        sortd = self.languages_by_frequency
        for lang, lang_info in sortd:
            print("{}: LOC={}, files={}".format(lang, lang_info.code, len(lang_info.files)))

        pass

class TokeiLanguageInfo:
    def __init__(self, tokei_dict: Dict[str, int], repo_path: str):
        self.blanks = tokei_dict['blanks']
        self.code = tokei_dict['code']
        self.comments = tokei_dict['comments']
        self.files = [Tokei.relative_path(repo_path, x['name']) for x in
                         tokei_dict['reports']]


    def __repr__(self):
        return "<TokeiLanguageInfo code={} files={}>".format(self.code,
            len(self.files))

class Tokei:

    @staticmethod
    def run(target: str):
        raw_results = Tokei._run(target)
        return TokeiOutput(raw_results, target)

    @staticmethod
    def _run(target: str):
        # NOTE: assumes tokei is already installed
        output = subprocess.check_output(
            ['tokei', target, '--output', 'json']).decode('utf-8')
        return json.loads(output)

    @staticmethod
    def relative_path(repo_path: str, file_path: str) -> str:
        rel_path = file_path.replace(repo_path, '')
        repo_name = os.path.basename(repo_path)

        return repo_name + rel_path