"""Functions for creating user objects and checking version with current installation."""
import os

try:
    import Grasshopper.Folders as Folders
    import Grasshopper.Kernel as gh
except ImportError:
    raise ImportError("Failed to import Grasshopper.")

# location where the Grasshopper user objects are stored
UO_FOLDER = Folders.UserObjectFolders[0]

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
    'Dragonfly': 'dragonfly_grasshopper'
}

# list of valid change tags for export
CHANGE_TAGS = ('fix', 'release', 'feat', 'perf', 'docs', 'ignore')


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
            os.remove(ufp)
        uo.Path = ufp

    uo.SaveToFile()
    return uo


def current_userobject_version(component):
    """Get the current installed version of a userobject that has the same name.

    Args:
        component: A Grasshopper Python component.
    """
    # load component from the folder where it should be
    assert component.Category in FOLDER_MAP, \
        'Unknown category: %s. Add category to folder_dict.' % component.Category
    fp = os.path.join(UO_FOLDER, FOLDER_MAP[component.Category], 'user_objects',
                      '%s.ghuser' % component.Name)

    if os.path.isfile(fp):  # if the component was found, parse out the version
        uo = gh.GH_UserObject(fp).InstantiateObject()
        # uo.Message returns None so we have to find it the old school way!
        for lc, line in enumerate(uo.Code.split('\n')):
            if lc > 200:  # this should never happen for valid userobjects
                raise ValueError(
                    'Failed to find version from UserObject for %s' % uo.Name
                )
            if line.strip().startswith("ghenv.Component.Message"):
                return line.split("=")[1].strip()[1:-1]
    else:  # there is no currently installed version of this userobject
        return None


def parse_version(semver_str):
    """Parse semantic version into major, minor, patch.

    Args:
        semver_str: Text for a component version (eg. 1.0.1).
    """
    try:
        major, minor, patch = [int(d) for d in semver_str.strip().split('.')]
    except ValueError:
        raise ValueError(
            '\nInvalid version format: %s\nYou must follow major.minor.patch format '
            'with 3 integer values' % semver_str
        )
    return major, minor, patch


def validate_change_type(change_type):
    """Check that a change type is a valid tag."""
    assert change_type in CHANGE_TAGS, 'Invalid change_type "{}". Choose from ' \
        'the following:\n{}'.format(change_type, ' '.join(CHANGE_TAGS))
    return change_type


def validate_version(current_version, new_version, change_type):
    """Validate that a version tag conforms to currently-installed version difference.

    Args:
        current_version: Semantic version string for the currently installed version.
        new_version: Semantic version string for the new component version.
        change_type: Text tag for the change type (eg. "fix").
    """
    if current_version is None:
        # this is the first time that this component is created; give it a pass
        print('    New component. No change in version: %s' % current_version)
        return True

    x, y, z = parse_version(current_version)
    parse_version(new_version)  # just make sure the semantic version format is valid

    msg = '\nFor a \'%s\' the component version should change to %s not %s.' \
        '\nFix the version or select the correct change type and try again.'
    if change_type == 'ignore':
        valid_version = new_version
    elif change_type == 'fix':
        valid_version = '.'.join(str(i) for i in (x, y, z + 1))
    elif change_type == 'feat' or change_type == 'perf':
        valid_version = '.'.join(str(i) for i in (x, y + 1, 0))
    elif change_type == 'release':
        valid_version = '.'.join(str(i) for i in (x + 1, 0, 0))
    elif change_type == 'docs':
        valid_version = '.'.join(str(i) for i in (x, y, z))
    else:
        raise ValueError('Invalid change_type: %s' % change_type)

    assert valid_version == new_version, msg % (change_type, valid_version, new_version)

    if current_version == new_version:
        print('    No change in version: %s' % current_version)
    else:
        print('    Version is changed from %s to %s.' % (current_version, new_version))
