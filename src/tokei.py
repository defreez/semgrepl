import json
import os
import subprocess

class Tokei:

    @staticmethod
    def run(target: str):
        # NOTE: assumes tokei is already installed
        output = subprocess.check_output(
            ['tokei', target, '--output', 'json']).decode('utf-8')
        return json.loads(output)


    @staticmethod
    def trim_tokei(raw_tokei_output: dict, repo_path: str):
        # tokei returns a lot of output. We don't care about the stats breakdown
        # for every single file, let's grab the overall breakdown + list of files for
        # each type
        result = {}
        base = raw_tokei_output
        for lang_key, detail_dict in base.items():

            result[lang_key] = {
                'blanks': detail_dict['blanks'],
                'code': detail_dict['code'],
                'comments': detail_dict['comments'],
                'lines': 0,  # detail_dict['lines'], # new tokei 12.X removes this
                'files': [Tokei.relative_path(repo_path, x['name']) for x in detail_dict['reports']]
            }

        return result

    @staticmethod
    def relative_path(repo_path: str, file_path: str) -> str:
        rel_path = file_path.replace(repo_path, '')
        repo_name = os.path.basename(repo_path)

        return repo_name + rel_path