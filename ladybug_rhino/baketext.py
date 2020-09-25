"""Functions to add text to the Rhino scene and create Grasshopper text objects."""

from .fromgeometry import from_plane
from .bakegeometry import _get_attributes
from .text import AlignmentTypes

try:
    import Rhino as rh
except ImportError as e:
    raise ImportError("Failed to import Rhino.\n{}".format(e))


def add_text_to_scene(text, plane, height, font='Arial',
                      horizontal_alignment=0, vertical_alignment=5,
                      layer_name=None, attributes=None):
    """Add text to the Rhino sceneusing a text string and ladybug Plane.

    Args:
        text: A text string to be added to the Rhino scene.
        plane: A Ladybug Plane object to locate and orient the text in the Rhino scene.
        height: A number for the height of the text in the Rhino scene.
        font: An optional text string for the font in which to draw the text.
        horizontal_alignment: An optional integer to specify the horizontal alignment
             of the text. Choose from: (0 = Left, 1 = Center, 2 = Right)
        vertical_alignment: An optional integer to specify the vertical alignment
             of the text. Choose from: (0 = Top, 1 = MiddleOfTop, 2 = BottomOfTop,
             3 = Middle, 4 = MiddleOfBottom, 5 = Bottom, 6 = BottomOfBoundingBox)
        layer_name: Optional text string for the layer name on which to place the
            text. If None, text will be added to the current layer.
        attributes: Optional Rhino attributes for adding to the Rhino scene.
    """
    txt = rh.Display.Text3d(text, from_plane(plane), height)
    txt.FontFace = font
    txt.HorizontalAlignment = AlignmentTypes.horizontal(horizontal_alignment)
    txt.VerticalAlignment = AlignmentTypes.vertical(vertical_alignment)
    doc = rh.RhinoDoc.ActiveDoc
    return doc.Objects.AddText(txt, _get_attributes(layer_name, attributes))
