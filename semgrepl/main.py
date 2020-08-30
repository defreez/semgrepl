import json
import os
import tempfile
import glob
from collections import defaultdict
from typing import List, Dict
from io import StringIO
from semgrep.output import OutputHandler
from semgrep.output import OutputSettings
from semgrep.constants import OutputFormat
import semgrep.semgrep_main
from jinja2 import Environment, FileSystemLoader
import semgrepl.abstract
import semgrepl.tokei
from semgrepl.config import SemgreplConfig

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


# Default to the rules dir in this repo
DEFAULT_RULES_DIR = os.path.abspath('rules')

# A default pack that runs all security rules
SEMGREP_RULES_ALL_SECURITY = "https://semgrep.dev/p/r2c-security-audit"

def init(target, rules_dir = DEFAULT_RULES_DIR, default_language = None):
    """ Run at the beginning of your session to set up your target and initialize semgrep.
    """
    semgrepl_config = SemgreplConfig([target], rules_dir, default_language)
    return semgrepl_config

def init_dir(target_dir, rules_dir = DEFAULT_RULES_DIR, default_language = None):
    """ Run at the beginning of your session to set up your target
        Adds a whole dir to targets.
    """
    dirs = glob.glob(target_dir)
    if len(dirs) == 0:
        print("[!] ERROR Provided glob did not match any dirs")
        print("Note that characters like ~ are not expanded")
        print("glob.glob is used from: https://docs.python.org/3/library/glob.html")
        return
    semgrepl_config = SemgreplConfig(dirs, rules_dir, default_language)
    return semgrepl_config

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
        target=[str(os.path.abspath(t)) for t in targets],
        pattern=pattern,
        config=config,
        lang="python")
    output_handler.close()
    return json.loads(io_capture.getvalue())

def collect_matches(fn, matches: List[semgrepl.abstract.SemgreplObject]):
    ret = defaultdict(set)
    for match in matches:
        k = fn(match)
        ret[k].add(match)
    return ret

# Organize SemgreplImports
def collect_imports(imports : List[semgrepl.abstract.SemgreplImport]):
    return collect_matches(lambda i: i.import_path, imports)

# Dict returned from collect_matches: {"string_key": [SemgreplObj1, ...]}
# Returns: {"key": count, "key2": count}
def count_collection(obj_collection):
    result = {}
    for key, items in obj_collection.items():
        result[key] = len(items)
    return result

def _render_and_run(semgrepl_config, rules_yaml_file, template_vars={}):
    matches = []
    languages = list(semgrepl_config.languages)
    languages.append("")        # some rules work for all languages
    for lang in languages:
        lang_dir = os.path.join(semgrepl_config.rules_dir, lang)
        semgrepl_config.logger.debug(lang_dir)
        env = Environment(loader = FileSystemLoader(lang_dir), trim_blocks=True, lstrip_blocks=True)
        if not os.path.exists(os.path.join(lang_dir, rules_yaml_file)):
            if lang:
                semgrepl_config.logger.warning("{} does not exist for language {}".format(rules_yaml_file, lang))
            continue
        template = env.get_template(rules_yaml_file)
        rendered_config = template.render(**template_vars)
        # This is ugly, but semgrep_main wants a config file path...
        # Use a lower-level API to avoid tmp file creation?
        tf = tempfile.NamedTemporaryFile(mode='wt')
        tf.write(rendered_config)
        tf.flush()
        matches.extend(semgrep_pattern("", semgrepl_config.targets, tf.name)['results'])
        tf.close()

    return matches

def find_imports(semgrepl_config) -> List[semgrepl.abstract.SemgreplImport]:
    matches = _render_and_run(semgrepl_config, "imports.yaml")
    import_matches = [semgrepl.abstract.SemgreplImport(x) for x in matches]
    return collect_matches(lambda i: i.import_path, import_matches)

def find_function_calls(semgrepl_config, function_name) -> List[semgrepl.abstract.SemgreplFunctionCall]:
    template_vars = {"function_name": function_name}
    matches = _render_and_run(semgrepl_config, "function-calls.yaml", template_vars)
    call_matches = [semgrepl.abstract.SemgreplFunctionCall(function_name, x) for x in matches]
    return call_matches

def find_function_defs_by_name(semgrepl_config, function_name) -> List[semgrepl.abstract.SemgreplFunctionDef]:
    template_vars = {"function_name": function_name}
    matches = _render_and_run(semgrepl_config, "function-defs.yaml", template_vars)
    function_def_matches = [semgrepl.abstract.SemgreplFunctionDef(x, function_name) for x in matches]
    return function_def_matches

def find_all_function_defs(semgrepl_config) -> List[semgrepl.abstract.SemgreplFunctionDef]:
    return find_function_defs_by_name(semgrepl_config, "$X")

def find_classes_by_name(semgrepl_config, class_name):
    template_vars = {"class_name": class_name}
    matches = _render_and_run(semgrepl_config, "classes.yaml", template_vars)
    class_matches = [semgrepl.abstract.SemgreplClass(x, class_name) for x in matches]
    return class_matches

def find_all_classes(semgrepl_config):
    return find_classes_by_name(semgrepl_config, "$X")

def all_annotations(semgrepl_config):
    annotations = set()
    all_functions = find_all_function_defs(semgrepl_config)
    for f in all_functions:
        for a in f.annotations:
            annotations.add(a)
    return annotations

def strings(semgrepl_config):
    matches = _render_and_run(semgrepl_config, "strings.yaml", semgrepl_config.targets)
    string_matches = [semgrepl.abstract.SemgreplString(x) for x in matches['results']]
    return string_matches
