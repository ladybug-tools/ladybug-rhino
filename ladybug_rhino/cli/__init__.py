"""Command Line Interface (CLI) entry point for ladybug rhino.

Note:

    Do not import this module in your code directly. For running the commands,
    execute them from the command line or as a subprocess
    (e.g. ``subprocess.call(['ladybug-rhino', 'viz'])``)

Ladybug rhino is using click (https://click.palletsprojects.com/en/7.x/) for
creating the CLI.
"""

import sys
import os
import logging
import click

try:
    from ladybug.config import folders as lb_folders
except ImportError as e:
    raise ImportError("Failed to import ladybug.\n{}".format(e))

from ladybug_rhino.pythonpath import create_python_package_dir, iron_python_search_path
from ladybug_rhino.ghpath import copy_components_packages, \
    clean_userobjects, clean_libraries
from ladybug_rhino.resourcepath import setup_resource_folders
from ladybug_rhino.versioning.change import change_installed_version

_logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def main():
    pass


@main.command('viz')
def viz():
    """Check if ladybug_rhino is flying!"""
    click.echo('viiiiiiiiiiiiizzzzzzzzz!')


@main.command('setup-user-environment')
@click.option(
    '--component-directory', default=None, help='The path to a directory that '
    'contains all of the Ladybug Tools Grasshopper python packages to be copied '
    '(both user object packages and dotnet gha packages). If unspecified, this command '
    'will search for the site-packages folder in the ladybug_tools folder. If '
    'they are not found, no user objects will be copied.',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.option(
    '--python-package-dir', help='Path to the directory with the python '
    'packages, which will be added to the search path. If unspecified, this command '
    'will search for the site-packages folder in the ladybug_tools folder.',
    type=str, default=None, show_default=True)
@click.option(
    '--setup-resources/--overwrite-resources', ' /-o', help='Flag to note '
    'whether the user resources should be overwritten or they should only '
    'be set up if they do not exist, in which case existing resources will '
    'be preserved.', default=True)
def setup_user_environment(component_directory, python_package_dir, setup_resources):
    """Set up the entire environment for the current user.

    This includes setting the IronPython search path, copying the components to
    the user-specific folders, and creating any user resource folders if they
    do not already exist. Note that setting the IronPython search path won't
    work well if Rhino is open while running this command.
    """
    try:
        # set the ironpython search path
        if python_package_dir is None:
            python_package_dir = create_python_package_dir()
        if python_package_dir is not None:
            click.echo('Setting Rhino IronPython search path ...')
            new_settings = iron_python_search_path(python_package_dir, None)
            click.echo('Congratulations! Setting the search path in the following '
                       'file was successful:\n{}'.format('\n'.join(new_settings)))
        # copy the components if they exist
        if component_directory is None:
            component_directory = \
                os.path.join(lb_folders.ladybug_tools_folder, 'grasshopper')
        if os.path.isdir(component_directory):
            click.echo('Copying Grasshopper Components ...')
            copy_components_packages(component_directory)
            click.echo('Congratulations! All component packages are copied!')
        # set the user resources
        click.echo('Setting user-specific resources ...')
        overwrite = not setup_resources
        resource_folder = setup_resource_folders(overwrite)
        click.echo('Setting up user resources in the following '
                   'folder was successful:\n{}'.format(resource_folder))
    except Exception as e:
        _logger.exception('Setting up the user environment failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@main.command('set-python-search')
@click.option('--python-package-dir', help='Path to the directory with the python '
              'packages, which will be added to the search path. If None, this command '
              'will search for the site-packages folder in the ladybug_tools folder',
              type=str, default=None, show_default=True)
@click.option('--settings-file', help='Path to the Rhino settings file to which the '
              'python-package-dir will be added. If None, this command will search '
              'the current user folder for all copies of this file for the installed '
              'Rhino versions. ', type=str, default=None, show_default=True)
def set_python_search(python_package_dir, settings_file):
    """Set Rhino to search for libraries in a given directory."""
    try:
        # search for the python package directory if it is not there
        if python_package_dir is None:
            python_package_dir = create_python_package_dir()

        # set the search path
        click.echo('Setting Rhino IronPython search path ...')
        new_settings = iron_python_search_path(python_package_dir, settings_file)
        click.echo('Congratulations! Setting the search path in the following '
                   'file was successful:\n{}'.format('\n'.join(new_settings)))
    except Exception as e:
        _logger.exception('Setting IronPython search path failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@main.command('copy-gh-components')
@click.argument('component-directory', type=click.Path(
    exists=True, file_okay=False, dir_okay=True, resolve_path=True))
def copy_gh_components(component_directory):
    """Copy all component packages to the UserObjects and Libraries folder.

    \b
    Args:
        component_directory: The path to a directory that contains all of the Ladybug
            Tools Grasshopper python packages to be copied (both user object
            packages and dotnet gha packages).
    """
    try:
        # copy the grasshopper components
        click.echo('Copying Grasshopper Components ...')
        copy_components_packages(component_directory)
        click.echo('Congratulations! All component packages are copied!')
    except Exception as e:
        _logger.exception('Copying Grasshopper components failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@main.command('remove-gh-components')
def remove_gh_components():
    """Remove all component packages to the UserObjects and Libraries folder."""
    try:
        # copy the grasshopper components
        click.echo('Removing Grasshopper Components ...')
        clean_userobjects()
        clean_libraries()
        click.echo('Congratulations! All component packages are removed!')
    except Exception as e:
        _logger.exception('Removing Grasshopper components failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@main.command('setup-resources')
@click.option('--setup-only/--overwrite', ' /-o', help='Flag to note '
              'whether the user resources should be overwritten or they should only '
              'be set up if they do not exist, in which case existing resources will '
              'be preserved.', default=True)
def setup_resources(setup_only):
    """Set up user resource folders in their respective locations."""
    try:
        overwrite = not setup_only
        # setup the resource folders
        click.echo('Setting user-specific resources ...')
        resource_folder = setup_resource_folders(overwrite)
        click.echo('Setting up user resources in the following '
                   'folder was successful:\n{}'.format(resource_folder))
    except Exception as e:
        _logger.exception('Setting up resource folders failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@main.command('change-installed-version')
@click.option('--version', '-v', help=' An optional text string for the version of '
              'the LBT plugin to be installed. The input should contain only integers '
              'separated by two periods (eg. 1.0.0). If unspecified, the Ladybug '
              'Tools plugin shall be updated to the latest available version. The '
              'version specified here does not need to be newer than the current '
              'installation and can be older but grasshopper plugin versions less '
              'than 0.3.0 are not supported.', type=str, default=None)
def run_versioner_process(version):
    """Change the currently installed version of Ladybug Tools.

    This requires an internet connection and will update all core libraries and
    Grasshopper components to the specified version_to_install.
    """
    try:
        change_installed_version(version)
    except Exception as e:
        _logger.exception('Changing the installed version failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
