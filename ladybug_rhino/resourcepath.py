"""Functions for managing user resources like standards and measures."""
import os

try:
    from ladybug.futil import preparedir, nukedir
except ImportError as e:
    raise ImportError("Failed to import ladybug.\n{}".format(e))

STANDARDS_SUBFOLDERS = (
    'constructions', 'constructionsets', 'schedules', 'programtypes',
    'modifiers', 'modifiersets'
)


def setup_resource_folders(overwrite=False):
    """Set up user resource folders in their respective locations.

    Args:
        overwrite: Boolean to note whether the user resources should only be set
            up if they do not exist, in which case existing resources will be
            preserved, or should they be overwritten.
    """
    # first check if there's an environment variable available for APPDATA
    app_folder = os.getenv('APPDATA')
    if app_folder is not None:
        resource_folder = os.path.join(app_folder, 'ladybug_tools')
        # set up user standards
        lib_folder = os.path.join(resource_folder, 'standards')
        for sub_f in STANDARDS_SUBFOLDERS:
            sub_lib_folder = os.path.join(lib_folder, sub_f)
            if not os.path.isdir(sub_lib_folder) or overwrite:
                preparedir(sub_lib_folder)
        # set up the user weather
        epw_folder = os.path.join(resource_folder, 'weather')
        if not os.path.isdir(epw_folder) or overwrite:
            if os.path.isdir(epw_folder):
                nukedir(epw_folder, rmdir=True)  # delete all sub-folders
            preparedir(epw_folder)
        # set up the user measures folder
        measure_folder = os.path.join(resource_folder, 'measures')
        if not os.path.isdir(measure_folder) or overwrite:
            if os.path.isdir(measure_folder):
                nukedir(measure_folder, rmdir=True)  # delete all sub-folders
            preparedir(measure_folder)
        return resource_folder
