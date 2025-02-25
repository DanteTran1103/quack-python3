#!/usr/bin/env python
# pylint: disable=C0325,W0603

"""Quack!!"""

import argparse
import os
import shutil
import subprocess

import git
import yaml
from git import Repo

_ARGS = None


def _setup():
    """Setup parser if executed script directly."""
    parser = argparse.ArgumentParser(description='Quack builder')
    parser.add_argument(
        '-y', '--yaml', help='Provide custom yaml. default: quack.yaml')
    parser.add_argument(
        '-p', '--profile', help='Run selected profile. default: init',
        nargs='?')
    return parser.parse_args()


def _remove_dir(directory):
    """Remove directory."""
    if os.path.exists(directory):
        shutil.rmtree(directory)
        return True
    return False


def _create_dir(directory):
    """Create directory."""
    if not os.path.exists(directory):
        os.makedirs(directory)


def _get_config():
    """Return yaml configuration."""
    yaml_file = (hasattr(_ARGS, 'yaml') and _ARGS.yaml) or 'quack.yaml'
    if os.path.isfile(yaml_file):
        with open(yaml_file) as file_pointer:
            return yaml.load(file_pointer, Loader=yaml.Loader)
    return


def _fetch_modules(config, specific_module=None):
    """Fetch git submodules."""
    module_list = config.get('modules')
    if not module_list:
        print('No modules found.')
        return
    modules = '.quack/modules'
    ignore_list = []
    _remove_dir(os.path.join(modules, ''))
    _remove_dir('.git/modules/')
    _create_dir(modules)
    if config.get('gitignore') and os.path.isfile('.gitignore'):
        with open('.gitignore', 'r') as file_pointer:
            ignore_list = list(set(file_pointer.read().split('\n')))

    for module in module_list.items():
        module_path = module[0]
        if specific_module and specific_module != module_path:
            continue
        repo_url = module[1].get('repository')
        if not repo_url:
            print(f'{module_path}: Please config a repository url')
            continue
        chosen_branch = module[1].get('branch')
        tag = module[1].get('tag')
        hexsha = module[1].get('hexsha')
        has_hexsha_config = hexsha is not None
        has_tag_config = tag is not None

        if not chosen_branch and not has_hexsha_config and not has_tag_config:
            print(f'{module_path}: must have at least branch or tag or hexsha')
            continue

        if tag and hexsha:
            print(f'{module_path}: Cannot be both tag & hexsha.')
            continue

        print('Cloning: ' + repo_url)
        temp_cloned_path = os.path.join(modules, module_path)
        if chosen_branch:
            repo = Repo.clone_from(
                url=repo_url,
                to_path=temp_cloned_path,
                single_branch=True,
                branch=chosen_branch)
        else:  # if not specific the branch, clone with the default branch
            repo = Repo.clone_from(
                url=repo_url,
                to_path=temp_cloned_path,
                single_branch=True)

        path = module[1].get('path', '')
        from_path = os.path.join(modules, module_path, path)
        if tag:
            subprocess.call(['git', 'checkout', '--quiet', 'tags/' + tag], cwd=from_path)
            tag = ' (' + tag + ') '
        elif hexsha:
            subprocess.call(['git', 'checkout', '--quiet', hexsha], cwd=from_path)
            hexsha = ' (' + hexsha + ')'
        else:
            hexsha = ' (' + repo.head.commit.hexsha + ')'

        is_exists = os.path.exists(from_path)
        if (path and is_exists) or not path:
            if module[1].get('isfile'):
                if os.path.isfile(module_path):
                    os.remove(module_path)
                shutil.copyfile(from_path, module_path)
            else:
                _remove_dir(module_path)
                if has_hexsha_config or has_tag_config:
                    shutil.copytree(from_path, module_path, ignore=shutil.ignore_patterns('.git*'))
                else:
                    shutil.copytree(from_path, module_path)
        elif not is_exists:
            print(f'{path} folder does not exists. Skipped.')

        # Remove temporary cloned repo.
        _remove_dir(from_path)
        if os.path.isfile('.gitmodules'):
            subprocess.call('rm .gitmodules'.split())
            subprocess.call('git rm --quiet --cached .gitmodules'.split())

        print('Cloned: ' + module_path + (tag or hexsha))

        if config.get('gitignore'):
            with open('.gitignore', 'a') as file_pointer:
                if module_path not in ignore_list:
                    file_pointer.write('\n' + module_path)
                    ignore_list.append(module_path)


def _clean_modules(config, specific_module=None):
    """Remove all given modules."""
    for module in config.get('modules').items():
        if specific_module and specific_module != module[0]:
            continue
        if _remove_dir(module[0]):
            print('Cleaned', module[0])


def _run_nested_quack(dependency):
    """Execute all required dependencies."""
    if not dependency or dependency[0] != 'quack':
        return
    quack = dependency[1]
    slash_index = quack.rfind('/')
    command = ['quack']
    module = '.'
    if slash_index > 0:
        module = quack[:slash_index]
    colon_index = quack.find(':')
    if len(quack) > colon_index + 1:
        command.append('-p')
        command.append(quack[colon_index + 1: len(quack)])
    if colon_index > 0:
        command.append('-y')
        command.append(quack[slash_index + 1:colon_index])
    print('Quack..' + module)
    git.Repo.init(module)
    subprocess.call(command, cwd=module)
    _remove_dir(module + '/.git')
    return True


def _run_tasks(config, profile):
    """Run given tasks."""
    dependencies = profile.get('dependencies', {})
    stats = {'tasks': 0, 'dependencies': 0}
    if isinstance(dependencies, dict):
        for dependency in profile.get('dependencies', {}).items():
            _run_nested_quack(dependency)
            stats['dependencies'] += 1
    tasks = profile.get('tasks', [])
    if not tasks:
        print('No tasks found.')
        return stats
    for command in tasks:
        stats['tasks'] += 1
        is_negate = command[0] == '-'
        if is_negate:
            command = command[1:]
        module = None
        is_modules = command.find('modules:') == 0 or 'modules' == command
        is_quack = command.find('quack:') == 0
        is_cmd = command.find('cmd:') == 0

        if is_modules and command != 'modules':
            module = command.replace('modules:', '')
        elif is_quack:
            _run_nested_quack(('quack', command.replace('quack:', '')))
        elif is_cmd:
            cmd = command.replace('cmd:', '')
            subprocess.call(cmd.split())

        if is_modules and not is_negate:
            _fetch_modules(config, module)
        elif is_modules and is_negate:
            _clean_modules(config, module)
    return stats


def _prompt_to_create():
    """Prompt user to create quack configuration."""
    prompt = input
    yes_or_no = prompt(
        'No quack configuration found, do you want to create one? (y/N): ')
    if yes_or_no.lower() == 'y':
        project_name = prompt('Provide project name: ')
        with open('quack.yaml', 'a') as file_pointer:
            file_pointer.write(f"""name: {project_name}
modules:
profiles:
  init:
    tasks: ['modules']""")
        return _get_config()
    return


def main():
    """Entry point."""
    global _ARGS
    _create_dir('.quack')
    if _ARGS is None:
        _ARGS = _setup()
    config = _get_config()
    if not config:
        config = _prompt_to_create()
        if not config:
            return
    if not _ARGS.profile:
        _ARGS.profile = 'init'
    profile = config.get('profiles', {}).get(_ARGS.profile, {})
    # print(_ARGS.profile, profile)
    stats = _run_tasks(config, profile)
    print('%s task(s) completed with %s dependencies.' % (
        stats['tasks'], stats['dependencies']))


if __name__ == '__main__':
    _ARGS = _setup()
    main()
