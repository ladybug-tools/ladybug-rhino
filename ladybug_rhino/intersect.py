"""Functions to handle intersection of Rhino geometries.

These represent geometry computation methods  that are either not supported by
ladybug_geometry or there are much more efficient versions of them in Rhino.
"""

try:
    import System.Threading.Tasks as tasks
except ImportError as e:
    print('Failed to import Windows/.NET libraries\nParallel processing functionality '
          'will not be available\n{}'.format(e))
try:
    import Rhino.Geometry as rg
except ImportError as e:
    raise ImportError("Failed to import Rhino.\n{}".format(e))
from .config import tolerance


def intersect_solids_parallel(solids, bound_boxes):
    """Intersect the co-planar faces of an array of solids using parallel processing.

    Args:
        original_solids: An array of closed Rhino breps (polysurfaces) that do
            not have perfectly matching surfaces between adjacent Faces.
        bound_boxes: An array of Rhino bounding boxes that parellels the input
            solids and will be used to check whether two Breps have any potential
            for intersection before the actual intersection is performed.

    Returns:
        int_solids -- The input array of solids, which have all been intersected
        with one another.
    """
    int_solids = solids[:]  # copy the input list to avoid editing it

    def intersect_each_solid(i):
        bb_1 = bound_boxes[i]
        # intersect the solids that come after this one
        for j, bb_2 in enumerate(bound_boxes[i + 1:]):
            if not overlapping_bounding_boxes(bb_1, bb_2):
                continue  # no overlap in bounding box; intersection impossible
            split_brep1, int_exists = intersect_solid(int_solids[i], int_solids[i + j + 1])
            if int_exists:
                int_solids[i] = split_brep1
        # intersect the solids that come before this one
        for j, bb_2 in enumerate(bound_boxes[:i]):
            if not overlapping_bounding_boxes(bb_1, bb_2):
                continue  # no overlap in bounding box; intersection impossible
            split_brep2, int_exists = intersect_solid(int_solids[i], int_solids[j])
            if int_exists:
                int_solids[i] = split_brep2

    tasks.Parallel.ForEach(range(len(solids)), intersect_each_solid)

    return int_solids


def intersect_solids(solids, bound_boxes):
    """Intersect the co-planar faces of an array of solids.

    Args:
        original_solids: An array of closed Rhino breps (polysurfaces) that do
            not have perfectly matching surfaces between adjacent Faces.
        bound_boxes: An array of Rhino bounding boxes that parellels the input
            solids and will be used to check whether two Breps have any potential
            for intersection before the actual intersection is performed.

    Returns:
        int_solids -- The input array of solids, which have all been intersected
        with one another.
    """
    int_solids = solids[:]  # copy the input list to avoid editing it

    for i, bb_1 in enumerate(bound_boxes):
        for j, bb_2 in enumerate(bound_boxes[i + 1:]):
            if not overlapping_bounding_boxes(bb_1, bb_2):
                continue  # no overlap in bounding box; intersection impossible

            # split the first solid with the second one
            split_brep1, int_exists = intersect_solid(
                int_solids[i], int_solids[i + j + 1])
            int_solids[i] = split_brep1

            # split the second solid with the first one if an intersection was found
            if int_exists:
                split_brep2, int_exists = intersect_solid(
                    int_solids[i + j + 1], int_solids[i])
                int_solids[i + j + 1] = split_brep2

    return int_solids


def intersect_solid(solid, other_solid):
    """Intersect the co-planar faces of one solid Brep using another.

    Args:
        solid: The solid Brep which will be split with intersections.
        other_solid: The other Brep, which will be used to split.
        tolerance: Distance within which two points are considered to be co-located.

    Returns:
        A tuple with two elements

        -   solid -- The input solid, which has been split.

        -   intersection_exists -- Boolean to note whether an intersection was found
            between the solid and the other_solid. If False, there's no need to
            split the other_solid with the input solid.
    """
    # variables to track the splitting process
    intersection_exists = False  # boolean to note whether an intersection exists
    done = False  # value to note when there are no more intersections

    while(not done):  # loop will break when no more intersections are detected
        num_faces_start = solid.Faces.Count  # track faces to detect intersections

        for face in solid.Faces:
            # get the intersection curves between the face and the other_brep
            if face.IsSurface:  # untrimmed surface
                intersect_lines = rg.Intersect.Intersection.BrepSurface(
                    other_solid, face.DuplicateSurface(), tolerance)[1]
            else:  # trimmed surfaces
                edges_idx = face.AdjacentEdges()
                edges = []
                for ix in edges_idx:
                    edges.append(solid.Edges.Item[ix])
                crv = rg.Curve.JoinCurves(edges, tolerance)
                int_brep = rg.Brep.CreatePlanarBreps(crv)
                if not int_brep:  # non-planar surface
                    continue
                intersect_lines = rg.Intersect.Intersection.BrepBrep(
                    int_brep[0], other_solid, tolerance)[1]

            # clean the intersection curves
            temp_int = rg.Curve.JoinCurves(intersect_lines, tolerance)
            joinedLines = [crv for crv in temp_int if rg.Brep.CreatePlanarBreps(crv)]

            # split the brep face with the intersection curves if they exist
            if len(joinedLines) > 0:
                intersection_exists = True
                new_brep = face.Split(joinedLines, tolerance)  # returns None on failure
                if new_brep and new_brep.Faces.Count > solid.Faces.Count:
                    solid = new_brep
                    break

        # detect whether any intersections were found in this while loop iteration
        if solid.Faces.Count == num_faces_start:
            done = True  # no intersections were found in this iteration of the loop

    return solid, intersection_exists


def overlapping_bounding_boxes(bound_box1, bound_box2):
    """Check if two Rhino bounding boxes overlap within the tolerance.

    This is particularly useful as a check before performing computationally
    intense processes between two bounding boxes like intersection. Checking the
    overlap of the bounding boxes is extremely quick given this method's use
    of the Separating Axis Theorem.

    Args:
        bound_box1: The first bound_box to check.
        bound_box2: The second bound_box to check.
    """
    # Bounding box check using the Separating Axis Theorem
    bb1_width = bound_box1.Max.X - bound_box1.Min.X
    bb2_width = bound_box2.Max.X - bound_box2.Min.X
    dist_btwn_x = abs(bound_box1.Center.X - bound_box2.Center.X)
    x_gap_btwn_box = dist_btwn_x - (0.5 * bb1_width) - (0.5 * bb2_width)

    bb1_depth = bound_box1.Max.Y - bound_box1.Min.Y
    bb2_depth = bound_box2.Max.Y - bound_box2.Min.Y
    dist_btwn_y = abs(bound_box1.Center.Y - bound_box2.Center.Y)
    y_gap_btwn_box = dist_btwn_y - (0.5 * bb1_depth) - (0.5 * bb2_depth)

    bb1_height = bound_box1.Max.Z - bound_box1.Min.Z
    bb2_height = bound_box2.Max.Z - bound_box2.Min.Z
    dist_btwn_z = abs(bound_box1.Center.Z - bound_box2.Center.Z)
    z_gap_btwn_box = dist_btwn_z - (0.5 * bb1_height) - (0.5 * bb2_height)

    if x_gap_btwn_box > tolerance or y_gap_btwn_box > tolerance or \
            z_gap_btwn_box > tolerance:
        return False  # no overlap
    return True  # overlap exists


def split_solid_to_floors(building_solid, floor_heights):
    """Extract a series of planar floor surfaces from solid building massing.

    Args:
        building_solid: A closed brep representing a building massing.
        floor_heights: An array of float values for the floor heights, which
            will be used to generate planes that subdivide the building solid.

    Returns:
        floor_breps -- A list of planar, horizontal breps representing the floors
        of the building.
    """
    # get the floor brep at each of the floor heights.
    floor_breps = []
    for hgt in floor_heights:
        story_breps = []
        floor_base_pt = rg.Point3d(0, 0, hgt)
        section_plane = rg.Plane(floor_base_pt, rg.Vector3d.ZAxis)
        floor_crvs = rg.Brep.CreateContourCurves(building_solid, section_plane)
        try:  # Assume a single countour curve has been found
            floor_brep = rg.Brep.CreatePlanarBreps(floor_crvs, tolerance)
        except TypeError:  # An array of contour curves has been found
            floor_brep = rg.Brep.CreatePlanarBreps(floor_crvs)
        if floor_brep is not None:
            story_breps.extend(floor_brep)
        floor_breps.append(story_breps)

    return floor_breps


def geo_min_max_height(geometry):
    """Get the min and max Z values of any input object."""
    bound_box = geometry.GetBoundingBox(rg.Plane.WorldXY)
    return bound_box.Min.Z, bound_box.Max.Z
