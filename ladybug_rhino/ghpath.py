"""Functions for managing the copying of user objects to the Grasshopper path."""
import os

try:
    from ladybug.futil import nukedir, copy_file_tree
except ImportError as e:
    raise ImportError("Failed to import ladybug.\n{}".format(e))

from .pythonpath import RHINO_VERSIONS

# core library packages, which get copied or cleaned out of the Rhino scripts folder
PACKAGES = \
    ('ladybug_grasshopper', 'honeybee_grasshopper_core', 'honeybee_grasshopper_energy',
     'honeybee_grasshopper_radiance', 'dragonfly_grasshopper')
# package containing .gha files
DOTNET_PACKAGES = ('ladybug_grasshopper_dotnet',)
GRASSHOPPER_ID = 'b45a29b1-4343-4035-989e-044e8580d9cf'


def copy_components_packages(directory):
    """Copy all Ladybug tools components packages to their respective locations.

    Args:
        directory: The path to a directory that contains all of the Ladybug
            Tools Grasshopper python packages to be copied (both user object
            packages and dotnet gha packages).
    """
    clean_userobjects()
    copy_packages_to_userobjects(directory)
    clean_libraries()
    copy_packages_to_libraries(directory)


def find_grasshopper_userobjects():
    """Get the paths to the current user's Grasshopper user object folder.

    The folder(s) will be created if they do not already exist.
    """
    if os.name == 'nt':  # we are on Windows
        appdata_roaming = os.getenv('APPDATA')
        uo_folder = [os.path.join(appdata_roaming, 'Grasshopper', 'UserObjects')]
    else:  # we are on Mac
        home_folder = os.getenv('HOME') or os.path.expanduser('~')
        uo_folder = []
        for ver in RHINO_VERSIONS:
            uo_fold = os.path.join(
                home_folder, 'Library', 'Application Support', 'McNeel',
                'Rhinoceros', ver, 'Plug-ins', 'Grasshopper ({})'.format(GRASSHOPPER_ID),
                'UserObjects')
            uo_folder.append(uo_fold)
    for uo_fold in uo_folder:
        if not os.path.isdir(uo_fold):
            os.makedirs(uo_fold)
    return uo_folder


def copy_packages_to_userobjects(directory):
    """Copy Ladybug Tools user object packages to the current user's userobject folder.

    Args:
        directory: The path to a directory that contains the Ladybug
            Tools Grasshopper python packages to be copied.
    """
    uo_folders = find_grasshopper_userobjects()
    for uo_folder in uo_folders:
        for pkg in PACKAGES:
            lib_folder = os.path.join(directory, pkg)
            dest_folder = os.path.join(uo_folder, pkg)
            if os.path.isdir(lib_folder):
                copy_file_tree(lib_folder, dest_folder, True)
                print('UserObjects copied to: {}'.format(dest_folder))


def clean_userobjects():
    """Remove installed Ladybug Tools packages from the user's userobjects folder."""
    uo_folders = find_grasshopper_userobjects()
    for uo_folder in uo_folders:
        for pkg in PACKAGES:
            lib_folder = os.path.join(uo_folder, pkg)
            if os.path.isdir(lib_folder):
                nukedir(lib_folder, True)
                print('UserObjects removed from: {}'.format(lib_folder))


def find_grasshopper_libraries():
    """Get the paths to the current user's Grasshopper Libraries folder.

    The folder(s) will be created if they do not already exist.
    """
    if os.name == 'nt':  # we are on Windows
        appdata_roaming = os.getenv('APPDATA')
        lib_folder = [os.path.join(appdata_roaming, 'Grasshopper', 'Libraries')]
    else:  # we are on Mac
        home_folder = os.getenv('HOME') or os.path.expanduser('~')
        lib_folder = []
        for ver in RHINO_VERSIONS:
            lib_fold = os.path.join(
                home_folder, 'Library', 'Application Support', 'McNeel',
                'Rhinoceros', ver, 'Plug-ins', 'Grasshopper ({})'.format(GRASSHOPPER_ID),
                'Libraries')
            lib_folder.append(lib_fold)
    for lib_fold in lib_folder:
        if not os.path.isdir(lib_fold):
            os.makedirs(lib_fold)
    return lib_folder


def copy_packages_to_libraries(directory):
    """Copy Ladybug tools Libraries packages to the current user's libraries folder.

    Args:
        directory: The path to a directory that contains the Ladybug
            Tools Grasshopper python packages.
    """
    lib_folders = find_grasshopper_libraries()
    for lib_folder in lib_folders:
        for pkg in DOTNET_PACKAGES:
            src_folder = os.path.join(directory, pkg)
            dest_folder = os.path.join(lib_folder, pkg)
            if os.path.isdir(src_folder):
                copy_file_tree(src_folder, dest_folder, True)
                print('Components copied to: {}'.format(dest_folder))


def clean_libraries():
    """Remove installed Ladybug Tools packages from the user's Libraries folder."""
    lib_folders = find_grasshopper_libraries()
    for lib_folder in lib_folders:
        for pkg in DOTNET_PACKAGES:
            lib_folder = os.path.join(lib_folder, pkg)
            if os.path.isdir(lib_folder):
                nukedir(lib_folder, True)
                print('Components removed from: {}'.format(lib_folder))
