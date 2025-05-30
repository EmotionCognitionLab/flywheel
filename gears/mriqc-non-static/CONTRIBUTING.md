# Contributing

## Getting started

1. Follow instructions to [install poetry](https://python-poetry.org/docs/#installation).
2. Follow instructions to [install pre-commit](https://pre-commit.com/#install)

After cloning the repo:

1. Run `poetry install` to install project and all dependencies
(see __Dependency management__ below)
2. Run `pre-commit install` to install pre-commit hooks
(see __Linting and Testing__ below)

(If you need to change your python version:)

```shell
poetry env use <path/to/your/python/executable>
poetry update
```

## Dependency management

This gear uses [`poetry`](https://python-poetry.org/) to manage dependencies,
develop, build and publish.

### Dependencies

Dependencies are listed in the `pyproject.toml` file.

#### Managing dependencies

* Adding: Use `poetry add [--dev] <dep>`
* Removing: Use `poetry remove [--dev] <dep>`
* Updating: Use `poetry update <dep>` or `poetry update` to update all deps.
  * Can also not update development dependencies with `--no-dev`
  * Update dry run: `--dry-run`

#### Using a different version of python

Poetry manages virtual environments and can create a virtual environment
with different versions of python,
however that version must be installed on the machine.  

You can configure the python version
by using `poetry env use <path/to/executable>`

#### Helpful poetry config options

See full options [Here](https://python-poetry.org/docs/configuration/#available-settings).

List current config: `poetry config --list`

* `poetry config virtualenvs.in-project <true|false|None>`:
create virtual environment inside project directory
* `poetry config virtualenvs.path <path>`: Path to virtual environment directory.

## Linting and Testing

Local linting and testing scripts
are managed through [`pre-commit`](https://pre-commit.com/).  
Pre-commit allows running hooks which can be defined locally, or in other
repositories. Default hooks to run on each commit:

* gearcheck: Specific check for this gear repo template
* poetry_export: Export poetry based dependencies to requirements.txt
* docker-build: Build docker image
* yamllint: Linte for YAML file
* black: Run black lintter
* isort: Sort import statements
* pytest: Run pytest

These hooks will all run automatically on commit, but can also be run manually
or just be disabled.

More hooks can be enabled upon need. List of available 
[hooks](https://gitlab.com/flywheel-io/tools/etc/qa-ci#table-of-contents).

### pre-commit usage

* Run hooks manually:
  * Run on all files: `pre-commit run -a`
  * Run on certain files: `pre-commit run --files test/*`
* Update (e.g. clean and install) hooks: `pre-commit clean && pre-commit install`
* Disable all hooks: `pre-commit uninstall`
* Enable all hooks: `pre-commit install`
* Skip a hook on commit: `SKIP=<hook-name> git commit`
* Skip all hooks on commit: `git commit --no-verify`

## Adding a contribution

Every contribution should be
associated with a ticket on the GEAR JIRA board, or be a hotfix.  
You should contribute by creating
a branch titled with either `hotfix-<hotfix_name` or `GEAR-<gear_num>-<description>`.  
For now, other branch names will be accepted,
but soon branch names will be rejected
if they don't follow this pattern.

When contributing, make a Merge Request against the main branch.

### Merge requests

The merge request should contain at least:

1. Your relevant change with the corresponding test.
1. A high level description of your changes and additional information to guide
the reviewer eyes as deemed appropriate.
1. An as clean as possible git history.
