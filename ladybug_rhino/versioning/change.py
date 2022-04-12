"""Functions for changing the installed version of Ladybug Tools."""
import os
import json
import subprocess

try:
    from ladybug.config import folders
    from ladybug.futil import nukedir, copy_file_tree, \
        download_file_by_name, unzip_file
except ImportError as e:
    raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))

from ..pythonpath import iron_python_search_path, create_python_package_dir

# find the location where the Grasshopper user objects are stored
app_folder = os.getenv('APPDATA')
if app_folder is not None:
    UO_DIRECTORY = os.path.join(app_folder, 'Grasshopper', 'UserObjects')
    GHA_DIRECTORY = os.path.join(app_folder, 'Grasshopper', 'Libraries')
else:
    home_folder = os.getenv('HOME') or os.path.expanduser('~')
    gh_folder = os.path.join(home_folder, 'AppData', 'Roaming', 'Grasshopper')
    UO_DIRECTORY = os.path.join(gh_folder, 'UserObjects')
    GHA_DIRECTORY = os.path.join(gh_folder, 'Libraries')
if os.name == 'nt':
    # test to see if components live in the core installation
    lbt_components = os.path.join(folders.ladybug_tools_folder, 'grasshopper')
    print(lbt_components)
    if os.path.isdir(lbt_components):
        user_dir = os.path.join(UO_DIRECTORY, 'ladybug_grasshopper')
        if not os.path.isdir(user_dir):
            UO_DIRECTORY = lbt_components
            GHA_DIRECTORY = lbt_components


def get_gem_directory():
    """Get the directory where measures distributed with Ladybug Tools are installed."""
    measure_folder = os.path.join(folders.ladybug_tools_folder, 'resources', 'measures')
    if not os.path.isdir(measure_folder):
        os.makedirs(measure_folder)
    return measure_folder


def get_standards_directory():
    """Get the directory where Honeybee standards are installed."""
    hb_folder = os.path.join(folders.ladybug_tools_folder, 'resources', 'standards')
    if not os.path.isdir(hb_folder):
        os.makedirs(hb_folder)
    return hb_folder


def remove_dist_info_files(directory):
    """Remove all of the PyPI .dist-info folders from a given directory.

    Args:
        directory: A directory containing .dist-info folders to delete.
    """
    for fold in os.listdir(directory):
        if fold.endswith('.dist-info'):
            nukedir(os.path.join(directory, fold), rmdir=True)


def get_config_dict():
    """Get a dictionary of the ladybug configurations.

    This is needed in order to put the configurations back after update.
    """
    with open(folders.config_file, 'r') as cfg:
        config_dict = json.load(cfg)
    return config_dict


def set_config_dict(config_dict):
    """Set the configurations using a dictionary.

    Args:
        config_dict: A dictionary of configuration paths.
    """
    with open(folders.config_file, 'w') as fp:
        json.dump(config_dict, fp, indent=4)


def update_libraries_pip(python_exe, package_name, version=None, target=None):
    """Change python libraries to be of a specific version using pip.
    Args:
        python_exe: The path to the Python executable to be used for installation.
        package_name: The name of the PyPI package to install.
        version: An optional string for the version of the package to install.
            If None, the library will be updated to the latest version with -U.
        target: An optional target directory into which the package will be installed.
        """
    # build up the command using the inputs
    if version is not None:
        package_name = '{}=={}'.format(package_name, version)
    cmds = [python_exe, '-m', 'pip', 'install', package_name]
    if version is None:
        cmds.append('-U')
    if target is not None:
        cmds.extend(['--target', target, '--upgrade'])

    # execute the command and print any errors
    print('Installing "{}" version via pip'.format(package_name))
    use_shell = True if os.name == 'nt' else False
    process = subprocess.Popen(
        cmds, shell=use_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = process.communicate()
    stdout, stderr = output
    error_msg = 'Package "{}" may not have been updated correctly\n' \
        'or its usage in the plugin may have changed. See pip stderr below:\n' \
        '{}'.format(package_name, stderr)
    return error_msg


def download_repo_github(repo, target_directory, version=None):
    """Download a repo of a particular version from from github.
    Args:
        repo: The name of a repo to be downloaded (eg. 'lbt-grasshopper').
        target_directory: the directory where the library should be downloaded to.
        version: The version of the repository to download. If None, the most
            recent version will be downloaded. (Default: None)
        """
    # download files
    if version is None:
        url = "https://github.com/ladybug-tools/{}/archive/master.zip".format(repo)
    else:
        url = "https://github.com/ladybug-tools/{}/archive/v{}.zip".format(repo, version)
    zip_file = os.path.join(target_directory, '%s.zip' % repo)
    print('Downloading "{}"  github repository to: {}'.format(repo, target_directory))
    try:
        download_file_by_name(url, target_directory, zip_file)
    except ValueError:
        msg = 'Access is denied to: {}\nMake sure that you are running Rhino as ' \
            'an Administrator by right-clicking on\nRhino and selecting "Run As ' \
            'Administrator" before opening Grasshopper and\n running this ' \
            'component.'.format(target_directory)
        print(msg)
        raise ValueError(msg)

    # unzip the file
    unzip_file(zip_file, target_directory)

    # try to clean up the downloaded zip file
    try:
        os.remove(zip_file)
    except Exception:
        print('Failed to remove downloaded zip file: {}.'.format(zip_file))

    # return the directory where the unzipped files live
    if version is None:
        return os.path.join(target_directory, '{}-master'.format(repo))
    else:
        return os.path.join(target_directory, '{}-{}'.format(repo, version))


def parse_lbt_gh_versions(lbt_gh_folder):
    """Parse versions of compatible libs from a clone of the lbt-grasshopper repo.

    Args:
        lbt_gh_folder: Path to the clone of the lbt-grasshopper repo

    Returns:
        A dictionary of library versions formatted like so (but with actual version
        numbers in place of '0.0.0').

        {
            'lbt-dragonfly' = '0.0.0',
            'ladybug-rhino' = '0.0.0',
            'lbt-recipes' = '0.0.0',
            'honeybee-openstudio-gem' = '0.0.0',
            'lbt-measures' = '0.0.0',
            'honeybee-standards' = '0.0.0',
            'honeybee-energy-standards' = '0.0.0',
            'ladybug-grasshopper': '0.0.0',
            'honeybee-grasshopper-core': '0.0.0',
            'honeybee-grasshopper-radiance': '0.0.0',
            'honeybee-grasshopper-energy': '0.0.0',
            'dragonfly-grasshopper': '0.0.0',
            'ladybug-grasshopper-dotnet': '0.0.0'
        }
    """
    # set the names of the libraries to collect and the version dict
    version_dict = {
        'lbt-dragonfly': None,
        'ladybug-rhino': None,
        'lbt-recipes': None,
        'honeybee-standards': None,
        'honeybee-energy-standards': None,
        'honeybee-openstudio-gem': None,
        'lbt-measures': None,
        'ladybug-grasshopper': None,
        'honeybee-grasshopper-core': None,
        'honeybee-grasshopper-radiance': None,
        'honeybee-grasshopper-energy': None,
        'dragonfly-grasshopper': None,
        'ladybug-grasshopper-dotnet': None
        }
    libs_to_collect = list(version_dict.keys())

    def search_versions(version_file):
        """Search for version numbers within a .txt file."""
        with open(version_file) as ver_file:
            for row in ver_file:
                try:
                    library, version = row.strip().split('==')
                    if library in libs_to_collect:
                        version_dict[library] = version
                except Exception:  # not a row with a ladybug tools library
                    pass

    # search files for versions
    requirements = os.path.join(lbt_gh_folder, 'requirements.txt')
    dev_requirements = os.path.join(lbt_gh_folder, 'dev-requirements.txt')
    ruby_requirements = os.path.join(lbt_gh_folder, 'ruby-requirements.txt')
    search_versions(requirements)
    search_versions(dev_requirements)
    search_versions(ruby_requirements)
    return version_dict


def change_installed_version(version_to_install=None):
    """Change the currently installed version of Ladybug Tools.

    This requires an internet connection and will update all core libraries and
    Grasshopper components to the specified version_to_install.

    Args:
        version_to_install: An optional text string for the version of the LBT
            plugin to be installed. The input should contain only integers separated
            by two periods (eg. 1.0.0). If None, the Ladybug Tools plugin shall
            be updated to the latest available version. The version specified here
            does not need to be newer than the current installation and can be older
            but grasshopper plugin versions less than 0.3.0 are not supported.
            A list of all versions of the Grasshopper plugin can be found
            here - https://github.com/ladybug-tools/lbt-grasshopper/releases
    """
    # ensure that Python has been installed in the ladybug_tools folder
    py_exe, py_lib = folders.python_exe_path, folders.python_package_path
    assert py_exe is not None and py_lib is not None, \
        'No valid Python installation was found at: {}.\nThis is a requirement in ' \
        'order to contine with installation'.format(
            os.path.join(folders.ladybug_tools_folder, 'python'))

    # get the compatible versions of all the dependencies
    temp_folder = os.path.join(folders.ladybug_tools_folder, 'temp')
    lbt_gh_folder = download_repo_github(
        'lbt-grasshopper', temp_folder, version_to_install)
    ver_dict = parse_lbt_gh_versions(lbt_gh_folder)
    ver_dict['lbt-grasshopper'] = version_to_install

    # install the core libraries
    print('Installing Ladybug Tools core Python libraries.')
    config_dict = get_config_dict()  # load configs so they can be put back after update
    df_ver = ver_dict['lbt-dragonfly']
    stderr = update_libraries_pip(py_exe, 'lbt-dragonfly', df_ver)
    if os.path.isdir(os.path.join(py_lib, 'lbt_dragonfly-{}.dist-info'.format(df_ver))):
        print('Ladybug Tools core Python libraries successfully installed!\n ')
    else:
        print(stderr)
    set_config_dict(config_dict)  # restore the previous configurations

    # install the library needed for interaction with Rhino
    print('Installing ladybug-rhino Python library.')
    rh_ver = ver_dict['ladybug-rhino']
    stderr = update_libraries_pip(py_exe, 'ladybug-rhino', rh_ver)
    if os.path.isdir(os.path.join(py_lib, 'ladybug_rhino-{}.dist-info'.format(rh_ver))):
        print('Ladybug-rhino Python library successfully installed!\n ')
    else:
        print(stderr)
    if os.name != 'nt':  # make sure libraries are copied to the rhino scripts folder
        iron_python_search_path(create_python_package_dir())

    # install the grasshopper components
    print('Installing Ladybug Tools Grasshopper components.')
    gh_ver = ver_dict['lbt-grasshopper']
    stderr = update_libraries_pip(py_exe, 'lbt-grasshopper', gh_ver, UO_DIRECTORY)
    lb_gh_ver = ver_dict['ladybug-grasshopper']
    lb_gh_info = 'ladybug_grasshopper-{}.dist-info'.format(lb_gh_ver)
    if os.path.isdir(os.path.join(UO_DIRECTORY, lb_gh_info)):
        print('Ladybug Tools Grasshopper components successfully installed!\n ')
        remove_dist_info_files(UO_DIRECTORY)  # remove the .dist-info files
    else:
        print(stderr)

    # install the .gha Grasshopper components
    gha_location = os.path.join(GHA_DIRECTORY, 'ladybug_grasshopper_dotnet')
    if os.path.isdir(gha_location):
        msg = '.gha files already exist in your Components folder and cannot be ' \
            'deleted while Grasshopper is open.\nClose Grasshopper, delete the ' \
            'ladybug_grasshopper_dotnet folder at\n{}\nand rerun this versioner ' \
            'component to get the new .gha files.\nOr simply keep '\
            'using the old .gha component if you do not need the latest ' \
            '.gha features.\n '.format(gha_location)
        print(msg)
    else:
        gha_ver = ver_dict['ladybug-grasshopper-dotnet']
        stderr = update_libraries_pip(
            py_exe, 'ladybug-grasshopper-dotnet', gha_ver, GHA_DIRECTORY)
        package_dir = os.path.join(
            GHA_DIRECTORY, 'ladybug_grasshopper_dotnet-{}.dist-info'.format(gha_ver))
        if os.path.isdir(package_dir):
            print('Ladybug Tools .gha Grasshopper components successfully installed!\n ')
            remove_dist_info_files(GHA_DIRECTORY)  # remove the dist-info files
        else:
            print(stderr)

    # install the lbt_recipes package
    print('Installing Ladybug Tools Recipes.')
    rec_ver = ver_dict['lbt-recipes']
    stderr = update_libraries_pip(py_exe, 'lbt-recipes', rec_ver)
    if os.path.isdir(os.path.join(py_lib, 'lbt_recipes-{}.dist-info'.format(rec_ver))):
        print('Ladybug Tools Recipes successfully installed!\n ')
    else:
        print(stderr)

    # install the honeybee-openstudio ruby gem
    gem_ver = ver_dict['honeybee-openstudio-gem']
    print('Installing Honeybee-OpenStudio gem version {}.'.format(gem_ver))
    gem_dir = get_gem_directory()
    base_folder = download_repo_github('honeybee-openstudio-gem', gem_dir, gem_ver)
    source_folder = os.path.join(base_folder, 'lib')
    lib_folder = os.path.join(gem_dir, 'honeybee_openstudio_gem', 'lib')
    print('Copying "honeybee_openstudio_gem" source code to {}\n '.format(lib_folder))
    copy_file_tree(source_folder, lib_folder)
    nukedir(base_folder, True)

    # install the lbt-measures ruby gem
    mea_ver = ver_dict['lbt-measures']
    print('Installing Ladybug Tools Measures version {}.'.format(mea_ver))
    base_folder = download_repo_github('lbt-measures', gem_dir, mea_ver)
    source_folder = os.path.join(base_folder, 'lib')
    print('Copying "lbt_measures" source code to {}\n '.format(gem_dir))
    copy_file_tree(source_folder, gem_dir)
    nukedir(base_folder, True)

    # always update the honeybee-energy-standards package
    print('Installing Honeybee energy standards.')
    stand_dir = get_standards_directory()
    hes_ver = ver_dict['honeybee-energy-standards']
    if os.path.isdir(os.path.join(stand_dir, 'honeybee_energy_standards')):
        nukedir(os.path.join(stand_dir, 'honeybee_energy_standards'), True)
    stderr = update_libraries_pip(
        py_exe, 'honeybee-energy-standards', hes_ver, stand_dir)
    hes_info = 'honeybee_energy_standards-{}.dist-info'.format(hes_ver)
    if os.path.isdir(os.path.join(stand_dir, hes_info)):
        print('Honeybee energy standards successfully installed!\n ')
        remove_dist_info_files(stand_dir)  # remove the dist-info files
    else:
        print(stderr)

    # delete the temp folder and give a completion message
    nukedir(temp_folder, True)
    version = 'LATEST' if version_to_install is None else version_to_install
    success_msg = 'Change to Version {} Successful!'.format(version)
    restart_msg = 'RESTART RHINO to load the new components + library.'
    sync_msg = 'The "LB Sync Grasshopper File" component can be used\n' \
        'to sync Grasshopper definitions with your new installation.'
    for msg in (success_msg, restart_msg, sync_msg):
        print(msg)
