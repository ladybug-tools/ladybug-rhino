"""Class for a bake-able version of the ladybug-display VisualizationSet."""
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
