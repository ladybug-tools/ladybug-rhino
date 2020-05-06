"""Functions to add text to the Rhino scene and create Grasshopper text objects."""

from .fromgeometry import from_plane

try:
    import Rhino as rh
    import System.Guid as guid
except ImportError as e:
    raise ImportError(
        "Failed to import Rhino.\n{}".format(e))
try:
    import Grasshopper as gh
except ImportError:
    print('Failed to import Grasshopper.\n'
          'Only functions for adding text to Rhino will be availabe.')
try:
    from ladybug_dotnet.color import black
except ImportError as e:
    black = None
    print("Failed to import ladybug_dotnet.\n{}".format(e))

from math import sqrt


def text_objects(text, plane, height, font='Arial',
                 horizontal_alignment=0, vertical_alignment=5):
    """Generate a Bake-able Grasshopper text object from a text string and ladybug Plane.

    Args:
        text: A text string to be converted to a a Grasshopper text object.
        plane: A Ladybug Plane object to locate and orient the text in the Rhino scene.
        height: A number for the height of the text in the Rhino scene.
        font: An optional text string for the font in which to draw the text.
        horizontal_alignment: An optional integer to specify the horizontal alignment
             of the text. Choose from: (0 = Left, 1 = Center, 2 = Right)
        vertical_alignment: An optional integer to specify the vertical alignment
             of the text. Choose from: (0 = Top, 1 = MiddleOfTop, 2 = BottomOfTop,
             3 = Middle, 4 = MiddleOfBottom, 5 = Bottom, 6 = BottomOfBoundingBox)
    """
    txt = rh.Display.Text3d(text, from_plane(plane), height)
    txt.FontFace = font
    txt.HorizontalAlignment = AlignmentTypes.horizontal(horizontal_alignment)
    txt.VerticalAlignment = AlignmentTypes.vertical(vertical_alignment)
    return TextGoo(txt)


"""____________EXTRA HELPER OBJECTS____________"""


class TextGoo(gh.Kernel.Types.GH_GeometricGoo[rh.Display.Text3d],
              gh.Kernel.IGH_BakeAwareData, gh.Kernel.IGH_PreviewData):
    """A Text object that can be baked and transformed in Grasshopper.

    The code for this entire class was taken from David Rutten and Giulio Piacentino's
    script described here:
    https://discourse.mcneel.com/t/creating-text-objects-and-outputting-them-as-normal-rhino-geometry/47834/7

    Args:
        text: A Rhino Text3d object.
    """

    def __init__(self, text):
        """Initialize Bake-able text."""
        self.m_value = text

    @staticmethod
    def DuplicateText3d(original):
        if original is None:
            return None
        text = rh.Display.Text3d(original.Text, original.TextPlane, original.Height)
        text.Bold = original.Bold,
        text.Italic = original.Italic,
        text.FontFace = original.FontFace
        return text

    def DuplicateGeometry(self):
        return TextGoo(TextGoo.DuplicateText3d(self.m_value))

    def get_TypeName(self):
        return "3D Text"

    def get_TypeDescription(self):
        return "3D Text"

    def ToString(self):
        if self.m_value is None:
            return "<null>"
        return self.m_value.Text

    def get_Boundingbox(self):
        if self.m_value is None:
            return rh.Geometry.BoundingBox.Empty
        return self.m_value.BoundingBox

    def GetBoundingBox(self, xform):
        if self.m_value is None:
            return rh.Geometry.BoundingBox.Empty
        box = self.m_value.BoundingBox
        corners = xform.TransformList(box.GetCorners())
        return rh.Geometry.BoundingBox(corners)

    def Transform(self, xform):
        text = TextGoo.DuplicateText3d(self.m_value)
        if text is None:
            return TextGoo(None)

        plane = text.TextPlane
        point = plane.PointAt(1, 1)

        plane.Transform(xform)
        point.Transform(xform)
        dd = point.DistanceTo(plane.Origin)

        text.TextPlane = plane
        text.Height *= dd / sqrt(2)
        new_text = TextGoo(text)

        new_text.m_value.Bold = self.m_value.Bold
        new_text.m_value.Italic = self.m_value.Italic
        new_text.m_value.FontFace = self.m_value.FontFace
        return new_text

    def Morph(self, xmorph):
        return self.DuplicateGeometry()

    def get_ClippingBox(self):
        return self.get_Boundingbox()

    def DrawViewportWires(self, args):
        if self.m_value is None:
            return
        color = black() if black is not None else args.Color
        args.Pipeline.Draw3dText(self.m_value, color)

    def DrawViewportMeshes(self, args):
        # Do not draw in meshing layer.
        pass

    def BakeGeometry(self, doc, att, id):
        id = guid.Empty
        if self.m_value is None:
            return False, id
        if att is None:
            att = doc.CreateDefaultAttributes()
        id = doc.Objects.AddText(self.m_value, att)
        return True, id


class AlignmentTypes(object):
    """Enumeration of text alignment types."""

    HORIZONTAL = {0: rh.DocObjects.TextHorizontalAlignment.Left,
                  1: rh.DocObjects.TextHorizontalAlignment.Center,
                  2: rh.DocObjects.TextHorizontalAlignment.Right}

    VERTICAL = {0: rh.DocObjects.TextVerticalAlignment.Top,
                1: rh.DocObjects.TextVerticalAlignment.MiddleOfTop,
                2: rh.DocObjects.TextVerticalAlignment.BottomOfTop,
                3: rh.DocObjects.TextVerticalAlignment.Middle,
                4: rh.DocObjects.TextVerticalAlignment.MiddleOfBottom,
                5: rh.DocObjects.TextVerticalAlignment.Bottom,
                6: rh.DocObjects.TextVerticalAlignment.BottomOfBoundingBox}

    @classmethod
    def horizontal(cls, field_number):
        return cls.HORIZONTAL[field_number]

    @classmethod
    def vertical(cls, field_number):
        return cls.VERTICAL[field_number]
