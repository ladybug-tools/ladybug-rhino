"""Functions to convert curved Rhino geometries into planar ladybug ones."""
from .config import tolerance

try:
    from ladybug_geometry.geometry3d.pointvector import Point3D
    from ladybug_geometry.geometry3d.face import Face3D
except ImportError as e:
    raise ImportError("Failed to import ladybug_geometry.\n{}".format(e))

try:
    import Rhino.Geometry as rg
except ImportError as e:
    raise ImportError(
        "Failed to import Rhino.\n{}".format(e))

import sys
if (sys.version_info > (3, 0)):  # python 3
    xrange = range


"""____________INDIVIDUAL SURFACES TO PLANAR____________"""


def planar_face_curved_edge_vertices(b_face, count, meshing_parameters):
    """Extract vertices from a planar brep face loop that has one or more curved edges.

    This method ensures vertices along the curved edge are generated in a way that
    they align with an extrusion of that edge. Alignment may not be possible when
    the adjoining curved surface is not an extrusion.

    Args:
        b_face: A brep face with the curved edge.
        count: An integer for the index of the loop to extract.
        meshing_parameters: Rhino Meshing Parameters to describe how
            curved edge should be converted into planar elements.

    Returns:
        A list of ladybug Point3D objects representing the input planar face.
    """
    loop_pcrv = b_face.Loops.Item[count].To3dCurve()
    f_norm = b_face.NormalAt(0, 0)
    if f_norm.Z < 0:
        loop_pcrv.Reverse()
    loop_verts = []
    try:
        loop_pcrvs = [loop_pcrv.SegmentCurve(i)
                      for i in xrange(loop_pcrv.SegmentCount)]
    except Exception:
        try:
            loop_pcrvs = [loop_pcrv[0]]
        except Exception:
            loop_pcrvs = [loop_pcrv]
    for seg in loop_pcrvs:
        if seg.Degree == 1:
            loop_verts.append(_point3d(seg.PointAtStart))
        else:
            # Ensure curve subdivisions align with adjacent curved faces
            seg_mesh = rg.Mesh.CreateFromSurface(
                rg.Surface.CreateExtrusion(seg, f_norm),
                meshing_parameters)
            for i in xrange(seg_mesh.Vertices.Count / 2 - 1):
                loop_verts.append(_point3d(seg_mesh.Vertices[i]))
    return loop_verts


def curved_surface_faces(b_face, meshing_parameters):
    """Extract Face3D objects from a curved brep face.

    Args:
        b_face: A curved brep face.
        meshing_parameters: Rhino Meshing Parameters to describe how
            curved edge should be converted into planar elements.

    Returns:
        A list of ladybug Face3D objects that together approximate the input
        curved surface.
    """
    if b_face.OrientationIsReversed:
        b_face.Reverse(0, True)
    face_brep = b_face.DuplicateFace(True)
    meshed_brep = rg.Mesh.CreateFromBrep(face_brep, meshing_parameters)[0]
    return mesh_faces_to_face3d(meshed_brep)


"""____________SOLID BREPS TO PLANAR____________"""


def curved_solid_faces(brep, meshing_parameters):
    """Extract Face3D objects from a curved solid brep.

    This methods ensures that the resulting Face3Ds form a closed solid by
    meshing the solid Brep alltogether.

    Args:
        brep: A curved solid brep.
        meshing_parameters: Rhino Meshing Parameters to describe how
            curved edge should be converted into planar elements.

    Returns:
        A list of ladybug Face3D objects that together approximate the input brep.
    """
    # mesh the geometry as a solid
    meshed_geo = rg.Mesh.CreateFromBrep(brep, meshing_parameters)

    # evaluate each mesh face to see what larger brep face it is a part of
    faces = []
    for mesh, b_face in zip(meshed_geo, brep.Faces):
        if b_face.IsPlanar(tolerance):  # only take the naked vertices of planar faces
            naked_edges = mesh.GetNakedEdges()
            all_verts = []
            for loop_pline in naked_edges:  # each loop_pline is a boundary/hole
                all_verts.append([_point3d(loop_pline.Item[i])
                                  for i in xrange(loop_pline.Count - 1)])
            if len(all_verts) == 1:  # No holes in the shape
                faces.append(Face3D(all_verts[0]))
            else:  # There's at least one hole in the shape
                faces.append(
                    Face3D(boundary=all_verts[0], holes=all_verts[1:]))
        else:
            faces.extend(mesh_faces_to_face3d(mesh))
    # remove colinear vertices as the meshing process makes a lot of them
    return [face.remove_colinear_vertices(tolerance) for face in faces]


"""________________EXTRA HELPER FUNCTIONS________________"""


def has_curved_face(brep):
    """Test if a Rhino Brep has a curved face.

    Args:
        brep: A Rhino Brep to test whether it has a curved face.
    """
    for b_face in brep.Faces:
        if not b_face.IsPlanar(tolerance):
            return True
    return False


def mesh_faces_to_face3d(mesh):
    """Convert a curved Rhino mesh faces into planar ladybug_geometry Face3D.

    Args:
        mesh: A curved Rhino mesh.

    Returns:
        A list of ladybug Face3D objects derived from the input mesh faces.
    """
    faces = []
    for m_face in mesh.Faces:
        if m_face.IsQuad:
            lb_face = Face3D(
                tuple(_point3d(mesh.Vertices[i]) for i in
                      (m_face.A, m_face.B, m_face.C, m_face.D)))
            if lb_face.check_planar(tolerance, False):
                faces.append(lb_face)
            else:
                lb_face_1 = Face3D(
                    tuple(_point3d(mesh.Vertices[i]) for i in
                          (m_face.A, m_face.B, m_face.C)))
                lb_face_2 = Face3D(
                    tuple(_point3d(mesh.Vertices[i]) for i in
                          (m_face.C, m_face.D, m_face.A)))
                faces.extend([lb_face_1, lb_face_2])
        else:
            lb_face = Face3D(
                tuple(_point3d(mesh.Vertices[i]) for i in
                      (m_face.A, m_face.B, m_face.C)))
            faces.append(lb_face)
    return faces


def _point3d(point):
    """Ladybug Point3D from Rhino Point3d."""
    return Point3D(point.X, point.Y, point.Z)
