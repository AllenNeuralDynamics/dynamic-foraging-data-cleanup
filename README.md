# Data Cleanup Script

This script will delete old data off of dynamic foraging rigs if it has not been modified in some time and if it has successfully been uploaded and registered to the docdb.

It can also be configured to delete especially large subfolders sooner than the whole dataset.

## Configuration

Configuration is stored in SIPE's zookeeper config server, and fetched fresh upon every run. The configuration options are specified in config.py (which also contains sensible defaults). An example configuration file is below:

```yaml
data_directory: C:/behavior_data
age_limit_days: 4
# actually_delete: true
too_old_for_warning_days: 30
subfolder_age: {"behavior-videos": 0} # delete large behavior-videos subfolder quicker (if the dataset is in codeocean)
```

## Deployment

An ansible playbook to deploy this script lives [here](https://eng-gitlab.corp.alleninstitute.org/infrastructure/mpeci/-/blob/master/ansible/playbooks/install_data_cleanup_script.yml) in the mpeci repo. It doesn't work to run it through the legacy mpe deploy website, but it works if you run it from the command line on eng-tools, which is necessary to mass-deploy anyways.

Log into eng-tools and move to the ansible folder:
`ssh svc_mpe@eng-tools`
`cd /opt/mpeci/ansible/`

Ping all the dynamic foraging rigs (frg 1-3, 6-8) first: 
`ansible-playbook -i hosts --vault-password-file /opt/sw_inventory/.secrets/.ansible_vault_pass --limit frg_[123678]_* playbooks/ping.yml`

Run install_data_cleanup_script.yml playbook on dynamic foraging rigs: 
`ansible-playbook -i hosts --vault-password-file /opt/sw_inventory/.secrets/.ansible_vault_pass --limit frg_[123678]_* playbooks/install_data_cleanup_script.yml`

## Installation

- Install uv ([installation docs](https://docs.astral.sh/uv/getting-started/installation/#installation-methods))
    - Powershell method: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
    - using winget: `winget install --id=astral-sh.uv  -e`
    - using homebrew: `brew install uv`
- Set an environment variable to tell uv to cache python in a folder with no IT restrictions
    - `setx UV_PYTHON_INSTALL_DIR C:\ProgramData\AIBS_MPE\uv_python`
- Run `uvx dynamic-foraging-data-cleanup@git+https://github.com/AllenNeuralDynamics/dynamic-foraging-data-cleanup`

## Usage

Run this script with `uv run data_cleanup.py --data_directory C:/behavior_data --age_limit_days 14`

By default, it won't actually delete anything, but it will print "Identified deletable dataset {}".
To actually delete the deletable things, add `--actually_delete True`

It will log to a logfile named `data_cleanup.log` in the same directory as the python file.

Calling `uv run data_cleanup.py --test` will run doctests and a test_data_cleanup function.


## Adapters to SIPE Infrastructure

Config loads from a [http config server](https://github.com/AllenNeuralDynamics/ficus) via universal-pathlib.

This is currently set to use Zookeeper as the config storage backend. Instructions for use are [here](https://github.com/AllenNeuralDynamics/SIPE-Admin/wiki/SW%3A-How%E2%80%90To's#zookeeper)

Logs get sent to the [SIPE logserver](http://eng-logtools:8080/?page_length=500)

## Installation

See this [uv tool guide](https://github.com/AllenNeuralDynamics/SIPE-Admin/discussions/141) 

Install with `uv tool`:

```
set UV_TOOL_DIR=C:\\ProgramData\AllenInstitute\bin
uv tool install git+https://github.com/AllenNeuralDynamics/dynamic-foraging-data-cleanup@{{ branch|tag }}
```

This will install the executable and add it to the path, so it can be run with `dynamic-foraging-data-cleanup`
