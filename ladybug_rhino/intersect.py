"""Functions to handle intersection of Rhino geometries.

These represent goemetry computation methods  that are either not supported by
ladybug_geometry or there are much more efficient versions of them in Rhino.
"""

try:
    import Rhino.Geometry as rg
except ImportError as e:
    raise ImportError(
        "Failed to import Rhino.\n{}".format(e))
from .config import tolerance


def split_solid_to_floors(building_solid, floor_heights):
    """Extract a series of planar floor surfaces from solid building massing.

    Args:
        building_solid: A closed brep representing a building massing.
        floor_heights: An array of float values for the floor heights, which
            will be used to generate planes that subdivide the building solid.

    Returns:
        floor_breps: A list of planar, horizontal breps representing the floors
            of the building.
    """
    # get the floor brep at each of the floor heights.
    floor_breps = []
    for hgt in floor_heights:
        floor_base_pt = rg.Point3d(0, 0, hgt)
        section_plane = rg.Plane(floor_base_pt, rg.Vector3d.ZAxis)
        floor_crvs = rg.Brep.CreateContourCurves(building_solid, section_plane)
        try:  # Assume a single countour curve has been found
            floor_brep = rg.Brep.CreatePlanarBreps(floor_crvs, tolerance)
        except TypeError:  # An array of contour curves has been found
            floor_brep = rg.Brep.CreatePlanarBreps(floor_crvs)
        if floor_brep is not None:
            floor_breps.extend(floor_brep)

    return floor_breps


def geo_min_max_height(geometry):
    """Get the min and max Z values of any input object."""
    bound_box = geometry.GetBoundingBox(rg.Plane.WorldXY)
    return bound_box.Min.Z, bound_box.Max.Z
