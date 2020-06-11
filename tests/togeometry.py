import rhinoinside
rhinoinside.load()
import Rhino
from ladybug_rhino.togeometry import to_point3d
from ladybug_geometry.geometry3d.pointvector import Point3D


def test_to_point3d():
    """Test the to_point3d method."""
    test_pt = Rhino.Geometry.Point3d(5.0, 10.0, 3.0)
    assert to_point3d(test_pt) == Point3D(5, 10, 3)
