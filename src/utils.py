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

# Prompt user during setup to define the scope of what they're testing 
# (probably a repo), and the base rules dir.
#
#
# These will be used by default in various commands unless another
# value is explicitly passed in.


#
# How to automagically do the right thing across many languages?
#   Why? Sometimes repos are polyglot
#
# - Do you specify a language in the argument? (this should always be an option)
# - Can we infer it based on file extension or tools that infer language 
#   from text?
# 
# - Usually you probably have a main language you care about, maybe the user
#   specifies a default language that's used when one isn't specified?
#
# Should NOT do:
# - iterate over every file - figure out what type it is, run semgrep on that
# - (running semgrep N times for N files)
#
# HACK!
# 1. On project setup / config setup, specify target dir(s)
# 2. Auto-run tokei/fingerprint tech used -> languages
# 3. Auto set config.languages = [results from tokei]
# 4. Whenever you run find_classes() uses all of the langs in conf.languages
#    - Invoke semgrep once per language
# 
# If the above doesn't work for some reason, you can manually append a language
# to your config.languages and that'll be run in addition (or remove langs).

# =============
# Chaining
# =============
#
#
# Find every method calling exec()
#    for every result in ^, find methods calling it (repeat to entry points?)
#
#  find classes named Handler, find methods named get in results
#  ==> Find classes |> find methods
#
# find all entrypoints - finds all main()'s + routes
# |> extract stuff from inside
#     - all functions called inside 
#     - all user parameters accessed - (URL param, headers, POST body param)
# ==> Find fxn defs |> find function calls within those | variables used
#
# Approximating Call Graph analysis / flow between files and methods
# - "How do I get here?"
# - Need: entrypoints
#   - Finding all functions called within entrypoints
#   - Doing this recursively
#
# Matching things across multiple files (sorta rule A depends on B)
# - Find me all patterns that look like <foo> but only if <bar> pattern appears
#   in another file (either a specific file or any file)
# - Given property X holds for the target repo, search out Y.
# ==> run query X, run query Y, return True if len(X) > 0 && len(Y) > 0
#     run query X and run query Y
#
# Seem to need to be able to go:
# - Inward - what's inside what is matched
# - Outward - parents, seems hard to do precisely, maybe requires 
#             running semgrep across multiple times, a bit tricky
#
# Basically what IDEs give you:
# - Find definition
# - Find references ("outward")
#
# ================
#
# Default queries that run on init.
    # - extract imports. class names. class hierarchy
    # - run strings
    # - runs tokei
    # - just say go and it shows you all these things
    # - automate the first 1 hour of any pen test / grokking a new repo
# could be easy to personalize. Each person has their own config
# - always do this on new repos. Maybe config per lang/framework.
#
#
# Flask to start with.
# - extract routes
# - annotations more generally, csrf, auth
# - url parameters, cookies, headers, post body, path parameters
# - file i/o. network i/o. crypto. pickle. shell exec. eval
# - env variables
#   - look at names
# - main()
# - fingerprint test files
# - technologies used? SSO, JWT, authn/authz, AWS/GCP/Azure (cloud), ...
#

#
# ===========
# Integrate with VS Code: Jump to program point
# 1. run the pattern in the Terminal at the bottom
# 2. match some stuff
# 3. Click on what you matched to jump to where it is in the code
#
# Similar: triage workflow
# 1. Match a bunch of things
# 2. Make it easy to go through them one at a time, marking as:
#    - Interesting, def not interesting, review later, ...
# 3. Bring up the relevant code
#
# -- Stretch: be able to annotate the code non destructively / share notes --
class SemgreplConfig:
    def __init__(self, targets = None, rules_dir = "", default_language = ""):
        self.rules_dir = rules_dir
        self.default_language = default_language

        if targets is None:
            self.targets = []
        else:
            self.targets = targets
        

# $CUR_CONFIG = SemgreplConfig()
# implicly use ^ if not otherwise specified


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
