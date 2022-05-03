"""Functions for creating user objects."""
import os

try:
    import Grasshopper.Folders as Folders
    import Grasshopper.Kernel as gh
except ImportError:
    raise ImportError("Failed to import Grasshopper.")

try:
    from ladybug.config import folders
except ImportError as e:
    raise ImportError("Failed to import ladybug.\n{}".format(e))

# find the location where the Grasshopper user objects are stored
UO_FOLDER = Folders.UserObjectFolders[0]
GHA_FOLDER = Folders.DefaultAssemblyFolder
if os.name == 'nt':
    # search all assembly folders to see if they live in the core installation
    lbt_components = os.path.join(folders.ladybug_tools_folder, 'grasshopper')
    if os.path.isdir(lbt_components):
        comp_dir = 'C:\\ProgramData\\McNeel\\Rhinoceros\\packages'
        for a_fold in Folders.AssemblyFolders:
            a_fold = str(a_fold)
            if a_fold.startswith(comp_dir) and 'LadybugTools' in a_fold:
                # a special plugin loader has been added
                UO_FOLDER = lbt_components
                GHA_FOLDER = lbt_components
                break

# map from the AdditionalHelpFromDocStrings to values for user object exposure
EXPOSURE_MAP = (
    gh.GH_Exposure.dropdown,
    gh.GH_Exposure.primary,
    gh.GH_Exposure.secondary,
    gh.GH_Exposure.tertiary,
    gh.GH_Exposure.quarternary,
    gh.GH_Exposure.quinary,
    gh.GH_Exposure.senary,
    gh.GH_Exposure.septenary
)

# map from the component category to the plugin package folder
FOLDER_MAP = {
    'Ladybug': 'ladybug_grasshopper',
    'Honeybee': 'honeybee_grasshopper_core',
    'HB-Radiance': 'honeybee_grasshopper_radiance',
    'HB-Energy': 'honeybee_grasshopper_energy',
    'Dragonfly': 'dragonfly_grasshopper',
    'LB-Legacy': 'LB-Legacy',
    'HB-Legacy': 'HB-Legacy',
    'HoneybeePlus': 'HoneybeePlus'
}


def create_userobject(component, move=True):
    """Create UserObject from a component.

    Args:
        component: A Grasshopper Python component.
        move: A Boolean to note whether the component should be moved to a subdirectory
            based on FOLDER_MAP. (Default: True).
    """
    # initiate userobject
    uo = gh.GH_UserObject()
    # set attributes
    uo.Icon = component.Icon_24x24
    try:
        exposure = int(component.AdditionalHelpFromDocStrings)
    except Exception:  # no exposure category specified
        exposure = 1
    uo.Exposure = EXPOSURE_MAP[exposure]
    uo.BaseGuid = component.ComponentGuid
    uo.Description.Name = component.Name
    uo.Description.Description = component.Description
    uo.Description.Category = component.Category
    uo.Description.SubCategory = component.SubCategory

    # save the userobject to a file
    uo.SetDataFromObject(component)
    uo.SaveToFile()

    # move the user object file to the assigned folder
    if move:
        ufd = os.path.join(UO_FOLDER, FOLDER_MAP[component.Category], 'user_objects')
        ufp = os.path.join(ufd, '%s.ghuser' % component.Name)
        if not os.path.isdir(ufd):
            # create folder if it is not already created
            os.mkdir(ufd)
        elif os.path.isfile(ufp):
            # remove current userobject
            try:
                os.remove(ufp)
            except Exception:
                pass  # access is denied to the user object location
        uo.Path = ufp

    uo.SaveToFile()
    return uo
