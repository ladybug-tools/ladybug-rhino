"""Command Line Interface (CLI) entry point for ladybug rhino.

Note:

    Do not import this module in your code directly. For running the commands,
    execute them from the command line or as a subprocess
    (e.g. ``subprocess.call(['ladybug-rhino', 'viz'])``)

Ladybug rhino is using click (https://click.palletsprojects.com/en/7.x/) for
creating the CLI.
"""

try:
    import click
except ImportError:
    raise ImportError(
        'click module is not installed. Try `pip install ladybug-rhino[cli]` command.'
    )

from ladybug_rhino.pythonpath import create_python_package_dir, iron_python_search_path

import sys
import logging
_logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def main():
    pass


@main.command('viz')
def viz():
    """Check if ladybug_rhino is flying!"""
    click.echo('viiiiiiiiiiiiizzzzzzzzz!')


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

        # validate the Model JSON
        click.echo('Setting Rhino IronPython search path ...')
        new_settings = iron_python_search_path(python_package_dir, settings_file)
        click.echo('Congratulations! Setting the search path in the following '
                   'file was successful:\n{}'.format('\n'.join(new_settings)))
    except Exception as e:
        _logger.exception('Setting IronPython search path failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
