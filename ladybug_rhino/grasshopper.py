"""Functions for dealing with inputs and outputs from Grasshopper components."""
import collections

try:
    from Grasshopper.Kernel import GH_RuntimeMessageLevel as Message
    from Grasshopper.Kernel.Types import GH_ObjectWrapper as Goo
    from Grasshopper import DataTree
    from Grasshopper.Kernel.Data import GH_Path as Path
except ImportError:
    raise ImportError(
        "Failed to import Grasshopper. Make sure the path is added to sys.path.")
try:
    from System import Object
except ImportError:
    print("Failed to import System.")


def give_warning(component, message):
    """Give a warning message (turning the component orange).

    Args:
        component: The grasshopper component object, which can be accessed through
            the ghenv.Component call within Grasshopper API.
        message: Text string for the warning message.
    """
    component.AddRuntimeMessage(Message.Warning, message)


def give_remark(component, message):
    """Give an remark message (giving a little grey ballon in the upper left).

    Args:
        component: The grasshopper component object, which can be accessed through
            the ghenv.Component call within Grasshopper API.
        message: Text string for the warning message.
    """
    component.AddRuntimeMessage(Message.Remark, message)


def all_required_inputs(component):
    """Check that all required inputs on a component are present.

    Note that this method needs required inputs to be written in the correct
    format on the component in order to work (required inputs have a
    single _ at the start and no _ at the end).

    Args:
        component: The grasshopper component object, which can be accessed through
            the ghenv.Component call within Grasshopper API.

    Returns:
        True if all required inputs are present. False if they are not.
    """
    is_input_missing = False
    for param in component.Params.Input:
        if param.NickName.startswith('_') and not param.NickName.endswith('_'):
            missing = False
            if not param.VolatileDataCount:
                missing = True
            elif param.VolatileData[0][0] is None:
                missing = True

            if missing is True:
                msg = 'Input parameter {} failed to collect data!'.format(param.NickName)
                print(msg)
                give_warning(component, msg)
                is_input_missing = True
    return not is_input_missing


def wrap_output(output):
    """Wrap Python objects as Grasshopper generic objects.

    Passing output lists of Python objects through this function can greatly reduce
    the time needed to run the component since Grasshopper can spend a long time
    figuring out the object type is if it is not recognized.  However, if the number
    of output objects is usually < 100, running this method won't really make a
    difference and so there's no need to use it.

    Args:
        output: A list of values to be wrapped as GOO.
    """
    if not output:
        return output
    try:
        return (Goo(i) for i in output)
    except Exception as e:
        raise ValueError('Failed to wrap {}:\n{}.'.format(output, e))


def data_tree_to_list(input):
    """Convert a grasshopper DataTree to nested lists of lists.

    Args:
        input: A Grasshopper DataTree.

    Returns:
        listData -- A list of namedtuples (path, dataList)
    """
    all_data = list(range(len(input.Paths)))
    Pattern = collections.namedtuple('Pattern', 'path list')

    for i, path in enumerate(input.Paths):
        data = input.Branch(path)
        branch = Pattern(path, [])

        for d in data:
            if d is not None:
                branch.list.append(d)

        all_data[i] = branch

    return all_data


def list_to_data_tree(input, root_count=0):
    """Transforms nested of lists or tuples to a Grasshopper DataTree"""

    def proc(input, tree, track):
        for i, item in enumerate(input):
            if isinstance(item, (list, tuple)):  # don't count iterables like colors
                track.append(i)
                proc(item, tree, track)
                track.pop()
            else:
                tree.Add(item, Path(*track))

    if input is not None:
        t = DataTree[object]()
        proc(input, t, [root_count])
        return t


def flatten_data_tree(input):
    """Flatten and clean a grasshopper DataTree into a single list and a pattern.

    Args:
        input: A Grasshopper DataTree.

    Returns:
        A tuple with two elements

        -   all_data -- All data in DataTree as a flattened list.

        -   pattern -- A dictionary of patterns as namedtuple(path, index of last item
            on this path, path Count). Pattern is useful to un-flatten the list
            back to a DataTree.
    """
    Pattern = collections.namedtuple('Pattern', 'path index count')
    pattern = dict()
    all_data = []
    index = 0  # Global counter for all the data
    for i, path in enumerate(input.Paths):
        count = 0
        data = input.Branch(path)

        for d in data:
            if d is not None:
                count += 1
                index += 1
                all_data.append(d)

        pattern[i] = Pattern(path, index, count)

    return all_data, pattern


def unflatten_to_data_tree(all_data, pattern):
    """Create DataTree from a single flattened list and a pattern.

    Args:
        all_data: A flattened list of all data
        pattern: A dictionary of patterns
            Pattern = namedtuple('Pattern', 'path index count')

    Returns:
        data_tree -- A Grasshopper DataTree.
    """
    data_tree = DataTree[Object]()
    for branch in range(len(pattern)):
        path, index, count = pattern[branch]
        data_tree.AddRange(all_data[index - count:index], path)

    return data_tree
