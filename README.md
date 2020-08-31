# semgrepl

Cool hack project.

## Getting Set Up

Python package dependencies can be installed using
`pip3 install -r requirements.txt`.

Also install [tokei](https://github.com/XAMPPRocky/tokei) for getting
code/languages used.

## Hacking on semgrepl in ipython

When developing semgrepl it is convenient to have ipython autoreload modules.
That way you can keep ipython open and it reloads the module when you save a
file. Type the following magic commands when ipython is first loaded:

```
%load_ext autoreload
%autoreload 2
```

Note: You can autorun the above commands on IPython startup using a config file
[docs](https://ipython.readthedocs.io/en/stable/config/intro.html). This can be
a global config file or via `ipython_config.py` in your current working
directory. You can see all locations in which IPython is looking for configuration files by starting ipython in debug mode:

~~~bash
$ ipython --debug -c 'exit()'
~~~

The main entrypoint into semgrepl is `utils.py` which can be loaded in ipython
with:


For example, to find all function definitions in the file `semgrepl/main.py`.
```
import semgrepl.main as sm
config = sm.init("semgrepl/main.py")
sm.find_all_function_defs(c)
```

### `semgrepl_init`

Oftentimes you have a specific target repo(s) in mind.

Use `semgrepl_init` to set your "working directory" of rules and target repo dirs, so you don't have pass them in to every semgrepl function.

~~~python
import semgrepl.main as sm
# Add 1 dir as a target
config = sm.init(path_to_repo)

# Or, Add every dir in a directory as a target, uses glob.glob()
config = sm.init_dir("Users/me/target_repos/*")

# Examine the config that's been set up
config

# See the various tech stacks used
config.print_languages_used()
~~~

### Running tests

From root of repo, type `pytest`.
