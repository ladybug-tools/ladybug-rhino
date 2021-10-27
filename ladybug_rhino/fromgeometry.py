"""Functions to translate from Ladybug geomtries to Rhino geometries."""
from .config import tolerance
from .color import color_to_color, gray

try:
    import Rhino.Geometry as rg
except ImportError as e:
    raise ImportError('Failed to import Rhino Geometry.\n{}'.format(e))

try:
    from ladybug_geometry.geometry2d.line import LineSegment2D
except ImportError as e:
    raise ImportError('Failed to import ladybug_geometry.\n{}'.format(e))


"""____________2D GEOMETRY TRANSLATORS____________"""


def from_vector2d(vector):
    """Rhino Vector3d from ladybug Vector2D."""
    return rg.Vector3d(vector.x, vector.y, 0)


def from_point2d(point, z=0):
    """Rhino Point3d from ladybug Point2D."""
    return rg.Point3d(point.x, point.y, z)


def from_ray2d(ray, z=0):
    """Rhino Ray3d from ladybug Ray2D."""
    return rg.Ray3d(from_point2d(ray.p, z), from_vector2d(ray.v))


def from_linesegment2d(line, z=0):
    """Rhino LineCurve from ladybug LineSegment2D."""
    return rg.LineCurve(from_point2d(line.p1, z), from_point2d(line.p2, z))


def from_arc2d(arc, z=0):
    """Rhino Arc from ladybug Arc2D."""
    circle = rg.Circle(from_point2d(arc.c, z), arc.r)
    return rg.Arc(circle, rg.Interval(arc.a1, arc.a2))


def from_polygon2d(polygon, z=0):
    """Rhino closed PolyLineCurve from ladybug Polygon2D."""
    return rg.PolylineCurve(
        [from_point2d(pt, z) for pt in polygon.vertices] + [from_point2d(polygon[0], z)])


def from_polyline2d(polyline, z=0):
    """Rhino closed PolyLineCurve from ladybug Polyline2D."""
    rhino_pts = [from_point2d(pt, z) for pt in polyline.vertices]
    if polyline.interpolated:
        return rg.Curve.CreateInterpolatedCurve(
            rhino_pts, 3, rg.CurveKnotStyle.UniformPeriodic)
    else:
        return rg.PolylineCurve(rhino_pts)


def from_mesh2d(mesh, z=0):
    """Rhino Mesh from ladybug Mesh2D."""
    pt_function = _get_point2d_function(z)
    return _translate_mesh(mesh, pt_function)


def _get_point2d_function(z_val):
    def point2d_function(pt):
        return from_point2d(pt, z_val)
    return point2d_function


"""____________3D GEOMETRY TRANSLATORS____________"""


def from_vector3d(vector):
    """Rhino Vector3d from ladybug Vector3D."""
    return rg.Vector3d(vector.x, vector.y, vector.z)


def from_point3d(point):
    """Rhino Point3d from ladybug Point3D."""
    return rg.Point3d(point.x, point.y, point.z)


def from_ray3d(ray):
    """Rhino Ray3d from ladybug Ray3D."""
    return rg.Ray3d(from_point3d(ray.p), from_vector3d(ray.v))


def from_linesegment3d(line):
    """Rhino LineCurve from ladybug LineSegment3D."""
    return rg.LineCurve(from_point3d(line.p1), from_point3d(line.p2))


def from_plane(pl):
    """Rhino Plane from ladybug Plane."""
    return rg.Plane(from_point3d(pl.o), from_vector3d(pl.x), from_vector3d(pl.y))


def from_arc3d(arc):
    """Rhino Arc from ladybug Arc3D."""
    if arc.is_circle:
        return rg.Circle(from_plane(arc.plane), from_point3d(arc.c), arc.radius)
    else:
        pts = (arc.p1, arc.midpoint, arc.p2)
        return rg.Arc(*(from_point3d(pt) for pt in pts))


def from_polyline3d(polyline):
    """Rhino closed PolyLineCurve from ladybug Polyline3D."""
    rhino_pts = [from_point3d(pt) for pt in polyline.vertices]
    if polyline.interpolated:
        return rg.Curve.CreateInterpolatedCurve(
            rhino_pts, 3, rg.CurveKnotStyle.UniformPeriodic)
    else:
        return rg.PolylineCurve(rhino_pts)


def from_mesh3d(mesh):
    """Rhino Mesh from ladybug Mesh3D."""
    return _translate_mesh(mesh, from_point3d)


def from_face3d(face):
    """Rhino Brep from ladybug Face3D."""
    segs = [from_linesegment3d(seg) for seg in face.boundary_segments]
    try:
        brep = rg.Brep.CreatePlanarBreps(segs, tolerance)[0]
    except TypeError:  # not planar in Rhino model tolerance; maybe from another model
        print('Brep not planar in Rhino model tolerance. Ignoring tolerance.')
        try:
            brep = rg.Brep.CreatePlanarBreps(segs, 1e6)[0]
        except TypeError:  # it must be a zero-area geometry
            return None
    if face.has_holes:
        for hole in face.hole_segments:
            trim_crvs = [from_linesegment3d(seg) for seg in hole]
            brep.Loops.AddPlanarFaceLoop(0, rg.BrepLoopType.Inner, trim_crvs)
    return brep


def from_polyface3d(polyface):
    """Rhino Brep from ladybug Polyface3D."""
    rh_faces = [from_face3d(face) for face in polyface.faces]
    brep = rg.Brep.JoinBreps(rh_faces, tolerance)
    if len(brep) == 1:
        return brep[0]


"""________ADDITIONAL 3D GEOMETRY TRANSLATORS________"""


def from_polyline2d_to_joined_polyline(polylines, z=0):
    """Rhino PolylineCurve made by joining list of Polyline2D.

    Args:
        polylines: An array of Ladybug Polyline2D or LineSegment2D to be joined
            into a polyline.
        z: A number for the Z-coordinate. (Default: 0).

    Returns:
        A Rhino brep constructed from the polygon and the offset distance. If offset
        is unsuccessful, just the polyline will be returned.
    """
    line_crv = []
    for pl in polylines:
        if isinstance(pl, LineSegment2D):
            line_crv.append(from_linesegment2d(pl))
        else:
            line_crv.append(from_polyline2d(pl))
    return rg.Curve.JoinCurves(line_crv)[0]


def from_polyline2d_to_offset_brep(polylines, offset, z=0):
    """Rhino Brep made by offsetting a joined list of Polyline2D inward.

    Args:
        polylines: An array of Ladybug Polyline2D or LineSegment2D to be joined
            and translated to an offset Brep.
        offset: A number for the distance to offset the Polygon inward.
        z: A number for the Z-coordinate. (Default: 0).

    Returns:
        A Rhino brep constructed from the polygon and the offset distance. If offset
        is unsuccessful, just the polyline will be returned.
    """
    curve = from_polyline2d_to_joined_polyline(polylines, z)
    crv_style = rg.CurveOffsetCornerStyle.Sharp
    all_curves = [curve]
    off_curves = curve.Offset(rg.Plane.WorldXY, -offset, tolerance, crv_style)
    if off_curves is not None:
        all_curves.extend(off_curves)
        offset_brep = rg.Brep.CreatePlanarBreps(all_curves)
        if len(offset_brep) == 1:
            if offset_brep[0].Loops.Count == 2:
                return offset_brep[0]
    return curve


def from_face3d_to_wireframe(face):
    """Rhino PolyLineCurves from ladybug Face3D.

    Args:
        face: A Ladybug Face3D object to be translated to a wireframe.

    Returns:
        A list of Rhino polyline curves for the boundary and holes in the face.
    """
    boundary = [_polyline_points(face.boundary)]
    if face.has_holes:
        return boundary + [_polyline_points(tup) for tup in face.holes]
    return boundary


def from_polyface3d_to_wireframe(polyface):
    """Rhino PolyLineCurve from ladybug Polyface3D."""
    return [f for face in polyface.faces for f in from_face3d_to_wireframe(face)]


def from_face3d_to_solid(face, offset):
    """Rhino Solid Brep from a ladybug Face3D and an offset from the base face.

    Args:
        face: Ladybug geometry Face3D object.
        offset: Number for the offset distance from the base face.
    """
    srf_brep = from_face3d(face)
    return rg.Brep.CreateFromOffsetFace(
        srf_brep.Faces[0], offset, tolerance, False, True)


def from_face3ds_to_joined_brep(faces):
    """A list of joined Breps from an array of ladybug Face3D."""
    return rg.Brep.JoinBreps([from_face3d(face) for face in faces], tolerance)


def from_face3ds_to_colored_mesh(faces, color):
    """Colored Rhino mesh from an array of ladybug Face3D and ladybug Color.

    This is used in workflows such as coloring Model geometry with results.
    """
    joined_mesh = rg.Mesh()
    for face in faces:
        try:
            joined_mesh.Append(from_mesh3d(face.triangulated_mesh3d))
        except Exception:
            pass  # failed to create a Rhino Mesh from the Face3D
    joined_mesh.VertexColors.CreateMonotoneMesh(color_to_color(color))
    return joined_mesh


def from_mesh2d_to_outline(mesh, z=0):
    """Rhino Polylines from the faces of ladybug Mesh2D."""
    pt_function = _get_point2d_function(z)
    verts = [pt_function(pt) for pt in mesh.vertices]
    face_plines = []
    for face in mesh.faces:
        outline = [verts[f] for f in face] + [verts[face[0]]]
        face_plines.append(rg.PolylineCurve(outline))
    return face_plines


"""________________EXTRA HELPER FUNCTIONS________________"""


def _translate_mesh(mesh, pt_function):
    """Translates both 2D and 3D meshes to Rhino"""
    rhino_mesh = rg.Mesh()
    if mesh.is_color_by_face:  # Mesh is constructed face-by-face
        _f_num = 0
        for face in mesh.faces:
            for pt in tuple(mesh[i] for i in face):
                rhino_mesh.Vertices.Add(pt_function(pt))
            if len(face) == 4:
                rhino_mesh.Faces.AddFace(
                    _f_num, _f_num + 1, _f_num + 2, _f_num + 3)
                _f_num += 4
            else:
                rhino_mesh.Faces.AddFace(_f_num, _f_num + 1, _f_num + 2)
                _f_num += 3
        if mesh.colors is not None:
            rhino_mesh.VertexColors.CreateMonotoneMesh(gray())
            _f_num = 0
            for i, face in enumerate(mesh.faces):
                col = color_to_color(mesh.colors[i])
                rhino_mesh.VertexColors[_f_num] = col
                rhino_mesh.VertexColors[_f_num + 1] = col
                rhino_mesh.VertexColors[_f_num + 2] = col
                if len(face) == 4:
                    rhino_mesh.VertexColors[_f_num + 3] = col
                    _f_num += 4
                else:
                    _f_num += 3
    else:  # Mesh is constructed vertex-by-vertex
        for pt in mesh.vertices:
            rhino_mesh.Vertices.Add(pt_function(pt))
        for face in mesh.faces:
            rhino_mesh.Faces.AddFace(*face)
        if mesh.colors is not None:
            rhino_mesh.VertexColors.CreateMonotoneMesh(gray())
            for i, col in enumerate(mesh.colors):
                rhino_mesh.VertexColors[i] = color_to_color(col)
    return rhino_mesh


def _polyline_points(tup):
    """Convert a tuple of Ladybug Geometry points to a Rhino Polyline."""
    return rg.PolylineCurve([from_point3d(pt) for pt in tup] + [from_point3d(tup[0])])
