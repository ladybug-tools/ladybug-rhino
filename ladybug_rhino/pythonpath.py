"""Functions for dealing with inputs and outputs from Grasshopper components."""
import os
import io
import xml.etree.ElementTree
import plistlib


def create_python_package_dir():
    """Get the default path where the ladybug_tools Python packages are installed.

    This method works both on Windows and Mac. If the folder is not found, this
    method will create the folder.
    """
    home_folder = os.getenv('HOME') or os.path.expanduser('~')
    py_install = os.path.join(home_folder, 'ladybug_tools', 'python')
    py_path = os.path.join(py_install, 'Lib', 'site-packages') if os.name == 'nt' \
        else os.path.join(py_install, 'lib', 'python3.8', 'site-packages')
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
            folder for the default location of this file.
        destination_file: Optional destination file to write out the edited settings
            file. If it is None, the settings_file will be overwritten.
    """
    # run the simulation
    if os.name == 'nt':  # we are on Windows
        new_settings = iron_python_search_path_windows(
            python_package_dir, settings_file, destination_file)
    else:  # we are on Mac, Linux, or some other unix-based system
        new_settings = iron_python_search_path_mac(
            python_package_dir, settings_file, destination_file)
    return new_settings


def iron_python_search_path_windows(python_package_dir, settings_file=None,
                                    destination_file=None):
    """Set Rhino to search for libraries in a given directory (on Windows).

    This is used as part of the installation process to ensure that Grasshopper
    looks for the core Python libraries in the ladybug_tools folder. The file
    will not be edited if the python_package_dir is already in the settings file.

    Args:
        python_package_dir: The path to a directory that contains the Ladybug
            Tools core libraries.
        settings_file: An optional XML settings file to which the python_package_dir
            will be added. If None, this method will search the current user's
            AppData folder for the default location of this file.
        destination_file: Optional destination file to write out the edited settings
            file. If it is None, the settings_file will be overwritten.
    """
    # find the path to the IronPython plugin
    if settings_file is None:
        home_folder = os.getenv('HOME') or os.path.expanduser('~')
        plugin_folder = os.path.join(home_folder, 'AppData', 'Roaming', 'McNeel',
                                     'Rhinoceros', '6.0', 'Plug-ins')
        for plugin in os.listdir(plugin_folder):
            if plugin.startswith('IronPython'):
                ip_path = os.path.join(plugin_folder, plugin)
                break
        settings_file = os.path.join(ip_path, 'settings', 'settings-Scheme__Default.xml')

    # open the settings file and find the search paths
    with io.open(settings_file, 'r', encoding='utf-8') as fp:
        set_data = fp.read()
    element = xml.etree.ElementTree.fromstring(set_data)
    settings = element.find('settings')
    search_path_needed = True
    for entry in settings.iter('entry'):
        if 'SearchPaths' in list(entry.attrib.values()):
            if entry.text == python_package_dir:
                search_path_needed = False

    # add the search paths if it was not found
    if destination_file is None:
        destination_file = settings_file
    if search_path_needed:
        line_to_add = '    <entry key="SearchPaths">{}</entry>\n'.format(python_package_dir)
        with open(settings_file, 'r') as fp:
            contents = fp.readlines()
        for i, line in enumerate(contents):
            if 'ScriptForm_Location' in line:
                break
        contents.insert(i + 1, line_to_add)
        with open(destination_file, 'w') as fp:
            fp.write(''.join(contents))
    return destination_file


def iron_python_search_path_mac(python_package_dir, settings_file=None,
                                destination_file=None):
    """Set Rhino to search for libraries in a given directory (on Mac).

    This is used as part of the installation process to ensure that Grasshopper
    looks for the core Python libraries in the ladybug_tools folder. The file
    will not be edited if the python_package_dir is already in the settings file.

    Args:
        python_package_dir: The path to a directory that contains the Ladybug
            Tools core libraries.
        settings_file: An optional .plist settings file to which the python_package_dir
            will be added. If None, this method will search the current user's
            Library/Preferences folder for the default location of this file.
        destination_file: Optional destination file to write out the edited settings
            file. If it is None, the settings_file will be overwritten.
    """
    # TODO: Remove this once I figure out where the SearchPaths are on Mac
    raise NotImplementedError('set-python-search has not yet been implemented on Mac.')

    # find the path to the IronPython plugin
    if settings_file is None:
        home_folder = os.getenv('HOME') or os.path.expanduser('~')
        plugin_folder = os.path.join(home_folder, 'Library', 'Preferences')
        settings_file = os.path.join(plugin_folder, 'com.mcneel.rhinoceros.plist')

    # load the plist file and check the search paths
    with open(settings_file, 'rb') as fp:
        pl = plistlib.load(fp)
    for key in pl.keys():
        if 'Settings' in key:
            print(key)
