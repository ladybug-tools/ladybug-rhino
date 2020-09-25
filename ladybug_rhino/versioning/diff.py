"""Functions for managing components differences and syncing component versions."""
import os

try:
    import System.Drawing
except ImportError:
    raise ImportError("Failed to import System.")

try:
    import Grasshopper.Kernel as gh
except ImportError:
    raise ImportError("Failed to import Grasshopper.")

from ..grasshopper import give_warning
from .userobject import UO_FOLDER, FOLDER_MAP


# list of valid change tags for export
CHANGE_TAGS = ('fix', 'release', 'feat', 'perf', 'docs', 'ignore')


def validate_change_type(change_type):
    """Check that a change type is a valid tag."""
    assert change_type in CHANGE_TAGS, 'Invalid change_type "{}". Choose from ' \
        'the following:\n{}'.format(change_type, ' '.join(CHANGE_TAGS))
    return change_type


def current_userobject_version(component):
    """Get the current installed version of a component.

    Args:
        component: A Grasshopper Python component with the same name as an
            installed user object. If no matching user object is found, this
            method returns None.
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
    """Parse semantic version string into (major, minor, patch) tuple.

    Args:
        semver_str: Text for a component version (eg. "1.0.1").
    """
    try:
        major, minor, patch = [int(d) for d in semver_str.strip().split('.')]
    except ValueError:
        raise ValueError(
            '\nInvalid version format: %s\nYou must follow major.minor.patch format '
            'with 3 integer values' % semver_str
        )
    return major, minor, patch


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


def has_version_changed(user_object, component):
    """Check if the version of a component has changed from a corresponding user object.

    Note that this method only works for user objects that have been dropped on the
    canvas. For comparing the version with a user object that hasn't been loaded from
    the component server by dropping it on the canvas, the current_userobject_version
    method should be used.

    Args:
        user_object: A Grasshopper user object component instance.
        component: The Grasshopper component object for which the version is
            being checked.
    """
    return not user_object.Message == component.Message


def compare_port(p1, p2):
    """Compare two component port objects and return True if they are equal.

    Args:
        p1: The first port object.
        p2: The second port object.
    """
    if hasattr(p1, 'TypeHint'):
        if p1.Name != p2.Name:
            return False
        elif p1.TypeHint.TypeName != p2.TypeHint.TypeName:
            return False
        elif str(p1.Access) != str(p2.Access):
            return False
        else:
            return True
    else:
        # output
        if p1.Name != p2.Name:
            return False
        else:
            return True


def compare_ports(c1, c2):
    """Compare all of the ports of two components and return True if they are equal.

    Args:
        c1: The first component object.
        c2: The second component object.
    """
    for i in range(c1.Params.Input.Count):
        if not compare_port(c1.Params.Input[i], c2.Params.Input[i]):
            return True

    for i in range(c1.Params.Output.Count):
        if not compare_port(c1.Params.Output[i], c2.Params.Output[i]):
            return True

    return False


def input_output_changed(user_object, component):
    """Check if any of inputs or outputs have changed between two components.

    Args:
        user_object: A Grasshopper user object component instance.
        component: The Grasshopper component object for which the version is
            being checked.
    """
    if user_object.Params.Input.Count != component.Params.Input.Count:
        return True
    elif user_object.Params.Output.Count != component.Params.Output.Count:
        return True

    return compare_ports(user_object, component)


def insert_new_user_object(user_object, component, doc):
    """Insert a new user object next to an existing component in the Grasshopper doc.

    Args:
        user_object: A Grasshopper user object component instance.
        component: The outdated component where the userobject will be inserted
            next to.
        doc: The Grasshopper document object.
    """
    # use component to find the location
    x = component.Attributes.Pivot.X + 30
    y = component.Attributes.Pivot.Y - 20

    # insert the new one
    user_object.Attributes.Pivot = System.Drawing.PointF(x, y)
    doc.AddObject(user_object, False, 0)


def mark_component(doc, component, note=None):
    """Put a circular red group around a component and label it with a note.

    Args:
        doc: The Grasshopper document object.
        component: A Grasshopper component object on the canvas to be circled.
        note: Text for the message to be displayed on the circle. If None, a
            default message about input/output change wil be used.
    """
    note = note or 'There is a change in the input or output! ' \
        'Replace this component manually.'
    grp = gh.Special.GH_Group()
    grp.CreateAttributes()
    grp.Border = gh.Special.GH_GroupBorder.Blob
    grp.AddObject(component.InstanceGuid)
    grp.Colour = System.Drawing.Color.IndianRed  # way to pick a racist color name, .NET
    grp.NickName = note
    doc.AddObject(grp, False)
    return True


def sync_component(component, syncing_component):
    """Sync a component on the canvas with its corresponding installed version.

    This includes identifying if the component by name in the user object folder,
    injecting the code from that user object into the component, and (if the
    component inputs or outputs have changed) circling the component in red +
    dropping the new user object next to the component.

    Args:
        component: A Grasshopper component object on the canvas to be circled.
        syncing_component: An object for the component that is doing the syncing.
            This will be used to give warnings and access the Grasshopper doc.
            Typically, this can be accessed through the ghenv.Component call.
    """
    # identify the correct user object sub-folder to which the component belongs
    ghuser_file = '%s.ghuser' % component.Name
    if str(component.Name).startswith(('LB', 'HB', 'DF')):  # [+]
        fp = os.path.join(UO_FOLDER, FOLDER_MAP[component.Category],
                          'user_objects', ghuser_file)
    elif str(component.Name).startswith(('Ladybug', 'Honeybee', 'HoneybeePlus')):  # legacy
        category = str(component.Name).split('_')[0]
        fp = os.path.join(UO_FOLDER, category, ghuser_file)
    else:  # unidentified plugin; see if we can find it in the root
        fp = os.path.join(UO_FOLDER, ghuser_file)

    # check to see if the user object is installed
    if not os.path.isfile(fp):  # see if there's a folder for the category
        if component.Category in FOLDER_MAP:
            fp = os.path.join(UO_FOLDER, FOLDER_MAP[component.Category], ghuser_file)
        if not os.path.isfile(fp):  # see if the component is in the root
            fp = os.path.join(UO_FOLDER, ghuser_file)
            if not os.path.isfile(fp):  # all hope is lost; component not installed
                warning = 'Failed to find the userobject for %s' % component.Name
                give_warning(syncing_component, warning)
                return False

    # the the instance of the user object from the file
    uo = gh.GH_UserObject(fp).InstantiateObject()

    # check to see if the version of the userobject has changed
    if not has_version_changed(uo, component):
        return False

    # the version has changed, let's update the code
    component.Code = uo.Code
    doc = syncing_component.OnPingDocument()  # get the Grasshopper document

    # define the callback function and update the solution
    def call_back(document):
        component.ExpireSolution(False)

    doc.ScheduleSolution(2, gh.GH_Document.GH_ScheduleDelegate(call_back))

    # check if the inputs or outputs have changed
    if input_output_changed(uo, component):
        insert_new_user_object(uo, component, doc)
        mark_component(doc, component)  # mark component with a warning to the user
        return 'Cannot update %s. Replace manually.' % component.Name

    return 'Updated %s' % component.Name
