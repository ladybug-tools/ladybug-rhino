"""Class for a bake-able version of the ladybug-display VisualizationSet."""
from ladybug_display.visualization import VisualizationSet
from .bakeobjects import bake_visualization_set

try:
    import System
except ImportError as e:
    raise ImportError("Failed to import Windows/.NET libraries\n{}".format(e))

try:
    import Grasshopper as gh
except ImportError:
    print('Failed to import Grasshopper.Grasshopper Baking disabled.')
    gh = None


class VisSetGoo(gh.Kernel.IGH_BakeAwareData):
    """A Bake-able version of the VisualizationSet for Grasshopper.

    Args:
        visualization_set: A Ladybug Display VisualizationSet object to be bake-able
            in the Rhino scene.
    """

    def __init__(self, visualization_set):
        self.vis_set = visualization_set

    def BakeGeometry(self, doc, att, id):
        try:
            if self.vis_set is not None:
                guids = bake_visualization_set(self.vis_set, True)
                return True, guids
        except Exception as e:
            System.Windows.Forms.MessageBox.Show(str(e), 'script error')
            return False, System.Guid.Empty

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        return str(self.vis_set)


def process_vis_set(vis_set):
    """Process various different types of VisualizationSet inputs.

    This includes VisualizationSet files, classes that have to_vis_set methods
    on them, and objects containing arguments for to_vis_set methods.
    """
    if isinstance(vis_set, VisualizationSet):
        return vis_set
    elif isinstance(vis_set, VisSetGoo):
        return vis_set.vis_set
    elif isinstance(vis_set, str):  # assume that it's a file
        return VisualizationSet.from_file(vis_set)
    elif hasattr(vis_set, 'to_vis_set'):  # an object with a method to be called
        return vis_set.to_vis_set()
    elif hasattr(vis_set, 'data'):  # an object to be decoded
        args_list = vis_set.data
        if isinstance(args_list[0], (list, tuple)):  # a list of VisualizationSets
            base_set = args_list[0][0].to_vis_set(*args_list[0][1:])
            for next_vis_args in args_list[1:]:
                for geo_obj in next_vis_args[0].to_vis_set(*next_vis_args[1:]):
                    base_set.add_geometry(geo_obj)
            return base_set
        else:  # a single list of arguments for to_vis_set
            return args_list[0].to_vis_set(*args_list[1:])
    else:
        msg = 'Input _vis_set was not recognized as a valid input.'
        raise ValueError(msg)
