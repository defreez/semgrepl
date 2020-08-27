import json
import os
import tempfile
from collections import defaultdict
from typing import List
from io import StringIO
from semgrep.output import OutputHandler
from semgrep.output import OutputSettings
from semgrep.constants import OutputFormat
import semgrep.semgrep_main
from jinja2 import Environment, FileSystemLoader
import semgrepl

def semgrep_pattern(pattern: str, targets: List[str], config = ""):
    io_capture = StringIO()
    output_handler = OutputHandler(
        OutputSettings(
            output_format=OutputFormat.JSON,
            output_destination=None,
            error_on_findings=False,
            strict=False,
        ),
        stdout=io_capture,
    )
    semgrep.semgrep_main.main(
        output_handler=output_handler,
        target=[str(t) for t in targets],
        pattern=pattern,
        config=config,
        lang="python")
    output_handler.close()
    return json.loads(io_capture.getvalue())

def collect_matches(fn, matches: List[semgrepl.SemgreplObject]):
    ret = defaultdict(set)
    for match in matches:
        k = fn(match)
        ret[k].add(match)
    return ret

# Organize SemgreplImports
def collect_imports(imports : List[semgrepl.SemgreplImport]):
    return collect_matches(lambda i: i.import_path, imports)

# Dict returned from collect_matches: {"string_key": [SemgreplObj1, ...]}
# Returns: {"key": count, "key2": count}
def count_collection(obj_collection):
    result = {}
    for key, items in obj_collection.items():
        result[key] = len(items)
    return result

def _render_and_run(rules_dir, config_file, target, template_vars={}):
    env = Environment(loader = FileSystemLoader(rules_dir), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(config_file)
    rendered_config = template.render(**template_vars)
    # This is ugly, but semgrep_main wants a config file path...
    # Use a lower-level API to avoid tmp file creation?
    tf = tempfile.NamedTemporaryFile(mode='wt')
    tf.write(rendered_config)
    tf.flush()
    matches = semgrep_pattern("", [target], tf.name)
    tf.close()
    return matches

# TODO: generalize across other langs

def find_imports(target, rules_dir) -> List[semgrepl.SemgreplImport]:
    rule_path = os.path.join(rules_dir, "python", "python-imports.yaml")
    matches = semgrep_pattern("", [target], rule_path)
    import_matches = [semgrepl.SemgreplImport(x) for x in matches['results']]
    return collect_matches(lambda i: i.import_path, import_matches)

def find_function_calls(target, rules_dir, function_name) -> List[semgrepl.SemgreplFunctionCall]:
    python_rules_dir = os.path.join(rules_dir, "python")
    template_vars = {"function_name": function_name}
    matches = _render_and_run(python_rules_dir, "function-calls.yaml", target, template_vars)
    call_matches = [semgrepl.SemgreplFunctionCall(function_name, x) for x in matches['results']]
    return call_matches

def find_function_defs_by_name(target, rules_dir, function_name) -> List[semgrepl.SemgreplFunctionDef]:
    python_rules_dir = os.path.join(rules_dir, "python")
    template_vars = {"function_name": function_name}
    matches = _render_and_run(python_rules_dir, "function-defs.yaml", target, template_vars)
    function_def_matches = [semgrepl.SemgreplFunctionDef(x, function_name) for x in matches['results']]
    return function_def_matches

def find_all_function_defs(target, rules_dir) -> List[semgrepl.SemgreplFunctionDef]:
    return find_function_defs_by_name(target, rules_dir, "$X")

def find_classes_by_name(target, rules_dir, class_name):
    python_rules_dir = os.path.join(rules_dir, "python")
    template_vars = {"class_name": class_name}
    matches = _render_and_run(python_rules_dir, "classes.yaml", target, template_vars)
    class_matches = [semgrepl.SemgreplClass(x, class_name) for x in matches['results']]
    return class_matches

def find_all_classes(target, rules_dir):
    return find_classes_by_name(target, rules_dir, "$X")

def all_annotations(target, rules_dir):
    annotations = set()
    all_functions = find_all_function_defs(target, rules_dir)
    for f in all_functions:
        for a in f.annotations:
            annotations.add(a)
    return annotations

def strings(target, rules_dir):
    matches = _render_and_run(rules_dir, "strings.yaml", target)
    string_matches = [semgrepl.SemgreplString(x) for x in matches['results']]
    return string_matches
