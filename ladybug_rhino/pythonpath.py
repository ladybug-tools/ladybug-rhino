"""Functions for managing the setting of Rhino's IronPython path."""
import os
import io
import xml.etree.ElementTree

try:
    from ladybug.futil import nukedir, copy_file_tree
    from ladybug.config import folders as lb_folders
except ImportError as e:
    raise ImportError("Failed to import ladybug.\n{}".format(e))


# core library packages, which get copied or cleaned out of the Rhino scripts folder
PACKAGES = (
    'ladybug_rhino', 'ladybug_geometry', 'ladybug_geometry_polyskel',
    'ladybug', 'ladybug_comfort', 'honeybee', 'honeybee_standards', 'honeybee_energy',
    'honeybee_radiance', 'honeybee_radiance_folder', 'honeybee_radiance_command',
    'dragonfly', 'dragonfly_energy', 'dragonfly_radiance', 'dragonfly_uwg',
    'lbt_recipes', 'pollination_handlers'
)
# Rhino versions that the plugins are compatible with
RHINO_VERSIONS = ('6.0', '7.0')
# UUID that McNeel uses to identify the IronPython plugin
IRONPYTHON_ID = '814d908a-e25c-493d-97e9-ee3861957f49'


def create_python_package_dir():
    """Get the default path where the ladybug_tools Python packages are installed.

    This method works both on Windows and Mac. If the folder is not found, this
    method will create the folder.
    """
    py_install = os.path.join(lb_folders.ladybug_tools_folder, 'python')
    py_path = os.path.join(py_install, 'Lib', 'site-packages') if os.name == 'nt' \
        else os.path.join(py_install, 'lib', 'python3.7', 'site-packages')
    if not os.path.isdir(py_path):
        return os.makedirs(py_path)
    return py_path


def iron_python_search_path(python_package_dir, settings_file=None,
                            destination_file=None):
    """Set Rhino to search for libraries in a given directory (on either OS).

    This is used as part of the installation process to ensure that Grasshopper
    looks for the core Python libraries in the ladybug_tools folder. The file
    will not be edited if the python_package_dir is already in the settings file.

    Args:
        python_package_dir: The path to a directory that contains the Ladybug
            Tools core libraries.
        settings_file: An optional XML settings file to which the python_package_dir
            will be added. If None, this method will search the current user's
            folder for all copies of this file for the installed Rhino versions.
        destination_file: Optional destination file to write out the edited settings
            file. If it is None, the settings_file will be overwritten.
    """
    # make sure that the rhino scripts folder is clean to avoid namespace issues
    clean_rhino_scripts()
    # set the plugin to look for packages in ladybug_tools folder
    new_settings = []
    if os.name == 'nt':  # we are on Windows
        all_settings = [settings_file] if settings_file is not None else \
            find_ironpython_settings_windows()
        for sf in all_settings:
            dest_settings = iron_python_search_path_windows(
                python_package_dir, sf, destination_file)
            new_settings.append(dest_settings)
    else:  # we are on Mac, Linux, or some other unix-based system
        copy_packages_to_rhino_scripts(python_package_dir)
    return new_settings


def find_installed_rhino_versions_windows():
    """Get a list of the compatible Rhino versions installed on this Windows machine."""
    program_files = os.getenv('PROGRAMFILES')
    installed_vers = []
    for ver in RHINO_VERSIONS:
        rhino_path = os.path.join(
            program_files, 'Rhino {}'.format(ver[0]), 'System', 'Rhino.exe')
        if os.path.isfile(rhino_path):
            installed_vers.append(ver)
    return installed_vers


def find_ironpython_settings_windows():
    """Get a list of all settings XML files for the supported RHINO_VERSIONS."""
    installed_set_files = []
    appdata_roaming = os.getenv('APPDATA')
    for ver in find_installed_rhino_versions_windows():
        # get the settings folder or create it if it doesn't exist
        plugin_folder = os.path.join(
            appdata_roaming, 'McNeel', 'Rhinoceros', ver, 'Plug-ins')
        settings_path = os.path.join(
            plugin_folder, 'IronPython ({})'.format(IRONPYTHON_ID), 'settings')
        if not os.path.isdir(settings_path):
            os.makedirs(settings_path)
        # append the default settings to the list of files to edit
        sf = os.path.join(settings_path, 'settings-Scheme__Default.xml')
        installed_set_files.append(sf)
        # get the search paths for any Rhino-inside instances if they exist
        for set_file in os.listdir(settings_path):
            if set_file.startswith('settings-Scheme') and \
                    set_file != 'settings-Scheme__Default.xml':
                sf = os.path.join(settings_path, set_file)
                installed_set_files.append(sf)
    return installed_set_files


def iron_python_search_path_windows(python_package_dir, settings_file,
                                    destination_file=None):
    """Set Rhino to search for libraries in a given directory (on Windows).

    This is used as part of the installation process to ensure that Grasshopper
    looks for the core Python libraries in the ladybug_tools folder. The file
    will not be edited if the python_package_dir is already in the settings file.

    Args:
        python_package_dir: The path to a directory that contains the Ladybug
            Tools core libraries.
        settings_file: An XML settings file to which the python_package_dir
            will be added.
        destination_file: Optional destination file to write out the edited settings
            file. If it is None, the settings_file will be overwritten.
    """
    # open the settings file and find the search paths
    search_path_needed = True
    settings_key_needed = False
    existing_paths = None
    if os.path.isfile(settings_file):
        with io.open(settings_file, 'r', encoding='utf-8') as fp:
            set_data = fp.read()
        element = xml.etree.ElementTree.fromstring(set_data)
        settings = element.find('settings')
        if settings is not None:
            for entry in settings.iter('entry'):
                if 'SearchPaths' in list(entry.attrib.values()):
                    existing_paths = entry.text
        else:  # there's no settings key within the XML file; we must add it
            search_path_needed = False
            settings_key_needed = True
    else:
        contents = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<settings id="2.0">',
            '<settings>',
            '</settings>',
            '</settings>'
        ]
        with open(settings_file, 'w') as fp:
            fp.write('\n'.join(contents))

    # add the search paths if it was not found
    if destination_file is None:
        destination_file = settings_file
    if search_path_needed:
        if 'ladybug_tools' in python_package_dir and existing_paths is not None:
            existing_paths = filter_existing_paths(existing_paths)
        new_paths = '{};{}'.format(existing_paths, python_package_dir) \
            if existing_paths is not None and existing_paths != '' \
            else python_package_dir
        line_to_add = '    <entry key="SearchPaths">{}</entry>\n'.format(new_paths)
        with io.open(settings_file, 'r', encoding='utf-8') as fp:
            contents = fp.readlines()
        line_to_del = None
        for i, line in enumerate(contents):
            if '<entry key="SearchPaths">' in line:
                line_to_del = i
            elif '</settings>' in line:
                break
        contents.insert(i, line_to_add)
        if line_to_del is not None:
            del contents[line_to_del]
        with io.open(destination_file, 'w', encoding='utf-8') as fp:
            fp.write(''.join(contents))
    elif settings_key_needed:
        lines_to_add = '  <settings>\n    <entry key="SearchPaths">{}</entry>\n' \
            '  </settings>\n'.format(python_package_dir)
        with io.open(settings_file, 'r', encoding='utf-8') as fp:
            contents = fp.readlines()
        for i, line in enumerate(contents):
            if '</settings>' in line:
                break
        contents.insert(i, lines_to_add)
        with io.open(destination_file, 'w', encoding='utf-8') as fp:
            fp.write(''.join(contents))
    return destination_file


def filter_existing_paths(existing_paths):
    """Filter out any duplicate/unwanted search paths."""
    paths_list = existing_paths.split(';')
    filt_paths = [p for p in paths_list
                  if 'ladybug_tools' not in p and 'pollination' not in p]
    return ';'.join(filt_paths)


def find_installed_rhino_scripts():
    """Get the path to the current user's Rhino scripts folder if it exists."""
    installed_scripts = []
    if os.name == 'nt':  # we are on Windows
        appdata_roaming = os.getenv('APPDATA')
        for ver in find_installed_rhino_versions_windows():
            scripts_folder = os.path.join(appdata_roaming, 'McNeel',
                                          'Rhinoceros', ver, 'scripts')
            if os.path.isdir(scripts_folder):
                installed_scripts.append(scripts_folder)
    else:  # we are on Mac
        home_folder = os.getenv('HOME') or os.path.expanduser('~')
        for ver in RHINO_VERSIONS:
            scripts_folder = os.path.join(home_folder, 'Library', 'Application Support',
                                          'McNeel', 'Rhinoceros', ver, 'scripts')
            if not os.path.isdir(scripts_folder):
                os.makedirs(scripts_folder)
            installed_scripts.append(scripts_folder)
    return installed_scripts


def copy_packages_to_rhino_scripts(python_package_dir, directory=None):
    """Copy Ladybug tools packages into a directory.

    Args:
        python_package_dir: The path to a directory that contains the Ladybug
            Tools core libraries.
        directory: The directory into which the packages will be copied. If None,
            the function will search for all installed copies of the current user's
            Rhino scripts folder.
    """
    folders = find_installed_rhino_scripts() if directory is None else [directory]
    for fold in folders:
        for pkg in PACKAGES:
            lib_folder = os.path.join(python_package_dir, pkg)
            dest_folder = os.path.join(fold, pkg)
            if os.path.isdir(lib_folder):
                copy_file_tree(lib_folder, dest_folder, True)
                print('Python packages copied to: {}'.format(dest_folder))


def clean_rhino_scripts(directory=None):
    """Remove installed Ladybug Tools packages from the old library directory.

    This function is usually run in order to avoid potential namespace conflicts.

    Args:
        directory: The directory to be cleaned. If None, the function will
            search for all installed copies of the current user's
            Rhino scripts folder.
     """
    folders = find_installed_rhino_scripts() if directory is None else [directory]
    for fold in folders:
        for pkg in PACKAGES:
            lib_folder = os.path.join(fold, pkg)
            if os.path.isdir(lib_folder):
                nukedir(lib_folder, True)
                print('Python packages removed from: {}'.format(lib_folder))
