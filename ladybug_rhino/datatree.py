"""Functions for dealing with DataTrees in Grasshopper."""
from collections import namedtuple
try:
    from Grasshopper import DataTree
    from Grasshopper.Kernel.Data import GH_Path as Path
except ImportError:
    raise ImportError(
        "Failed to import Grasshopper. Make sure the path is added to sys.path.")
try:
    from System import Object
except ImportError:
    print "Failed to import System."


def flatten_data_tree(input):
    """Flatten and clean a grasshopper DataTree.

    Args:
        input: A Grasshopper DataTree.

    Returns:
        all_data: All data in DataTree as a flattened list.
        pattern: A dictonary of patterns as namedtuple(path, index of last item
        on this path, path Count). Pattern is useful to unflatten the list back
        to DataTree.
    """
    Pattern = namedtuple('Pattern', 'path index count')
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
    """Create DataTree from a flattrn list based on the pattern.

    Args:
        all_data: A flattened list of all data
        pattern: A dictonary of patterns
            Pattern = namedtuple('Pattern', 'path index count')

    Returns:
        data_tree: A Grasshopper DataTree.
    """
    data_tree = DataTree[Object]()
    for branch in xrange(len(pattern)):
        path, index, count = pattern[branch]
        data_tree.AddRange(all_data[index - count:index], path)

    return data_tree


def data_tree_to_list(input):
    """Convert a grasshopper DataTree to nested lists of lists.

    Args:
        input: A Grasshopper DataTree.

    Returns:
        listData: A list of namedtuples (path, dataList)
    """
    all_data = range(len(input.Paths))
    Pattern = namedtuple('Pattern', 'path list')

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
            if hasattr(item, '__iter__'):  # if list or tuple
                track.append(i)
                proc(item, tree, track)
                track.pop()
            else:
                tree.Add(item, Path(*track))

    if input is not None:
        t = DataTree[object]()
        proc(input, t, [root_count])
        return t
