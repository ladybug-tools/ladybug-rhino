"""Functions for managing the copying of user objects to the Grasshopper path."""
import os

try:
    from ladybug.futil import nukedir, copy_file_tree
except ImportError as e:
    raise ImportError("Failed to import ladybug.\n{}".format(e))


# core library packages, which get copied or cleaned out of the Rhino scripts folder
PACKAGES = \
    ('ladybug_grasshopper', 'honeybee_grasshopper_core', 'honeybee_grasshopper_energy',
     'honeybee_grasshopper_radiance', 'dragonfly_grasshopper')
# package containing .gha files
DOTNET_PACKAGES = ('ladybug_grasshopper_dotnet',)


def copy_components_packages(directory):
    """Copy all Ladybug tools components packages.

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
    """Get the path to the current user's Grasshopper user object folder if it exists."""
    if os.name == 'nt':  # we are on Windows
        appdata_roaming = os.getenv('APPDATA')
        uo_folder = os.path.join(appdata_roaming, 'Grasshopper', 'UserObjects')
    else:  # we are on Mac
        home_folder = os.getenv('HOME') or os.path.expanduser('~')
        uo_folder = os.path.join(home_folder, 'Library', 'Application Support',
                                 'Grasshopper', 'UserObjects')
    if not os.path.isdir(uo_folder):
        os.makedirs(uo_folder)
    return uo_folder


def copy_packages_to_userobjects(directory):
    """Copy Ladybug tools userobjects packages.

    Args:
        directory: The path to a directory that contains the Ladybug
            Tools Grasshopper python packages to be copied.
    """
    uo_folder = find_grasshopper_userobjects()
    for pkg in PACKAGES:
        lib_folder = os.path.join(directory, pkg)
        dest_folder = os.path.join(uo_folder, pkg)
        if os.path.isdir(lib_folder):
            copy_file_tree(lib_folder, dest_folder, True)


def clean_userobjects():
    """Remove installed Ladybug Tools packages from the userobjects folder."""
    directory = find_grasshopper_userobjects()
    for pkg in PACKAGES:
        lib_folder = os.path.join(directory, pkg)
        if os.path.isdir(lib_folder):
            nukedir(lib_folder, True)


def find_grasshopper_libraries():
    """Get the path to the current user's Grasshopper Libraries folder if it exists."""
    if os.name == 'nt':  # we are on Windows
        appdata_roaming = os.getenv('APPDATA')
        lib_folder = os.path.join(appdata_roaming, 'Grasshopper', 'Libraries')
    else:  # we are on Mac
        home_folder = os.getenv('HOME') or os.path.expanduser('~')
        lib_folder = os.path.join(home_folder, 'Library', 'Application Support',
                                 'Grasshopper', 'Libraries')
    if not os.path.isdir(lib_folder):
        os.makedirs(lib_folder)
    return lib_folder


def copy_packages_to_libraries(directory):
    """Copy Ladybug tools Libraries packages.

    Args:
        directory: The path to a directory that contains the Ladybug
            Tools Grasshopper python packages.
    """
    lib_folder = find_grasshopper_libraries()
    for pkg in DOTNET_PACKAGES:
        src_folder = os.path.join(directory, pkg)
        dest_folder = os.path.join(lib_folder, pkg)
        if os.path.isdir(src_folder):
            copy_file_tree(src_folder, dest_folder, True)


def clean_libraries():
    """Remove installed Ladybug Tools packages from the Libraries folder."""
    directory = find_grasshopper_libraries()
    for pkg in DOTNET_PACKAGES:
        lib_folder = os.path.join(directory, pkg)
        if os.path.isdir(lib_folder):
            nukedir(lib_folder, True)
