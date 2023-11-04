"""Functions to bake from Ladybug geometries into a Rhino document."""
from .fromgeometry import from_point2d, from_arc2d, from_polyline2d, from_mesh2d, \
    from_point3d, from_plane, from_arc3d, from_polyline3d, \
    from_mesh3d, from_face3d, from_polyface3d, from_sphere, from_cone, from_cylinder
from .color import color_to_color, gray

try:
    from System.Drawing import Color
except ImportError as e:
    raise ImportError("Failed to import Windows/.NET libraries\n{}".format(e))

try:
    import Rhino.Geometry as rg
    from Rhino import RhinoMath
    import Rhino.DocObjects as docobj
    from Rhino import RhinoDoc as rhdoc
except ImportError as e:
    raise ImportError("Failed to import Rhino document attributes.\n{}".format(e))

"""____________BAKE 2D GEOMETRY TO THE RHINO SCENE____________"""


def bake_vector2d(vector, z=0, layer_name=None, attributes=None):
    """Add ladybug Ray2D to the Rhino scene as a Line with an Arrowhead."""
    doc = rhdoc.ActiveDoc
    seg = (rg.Point3d(0, 0, z), rg.Point3d(vector.x, vector.y, z))
    attrib = _get_attributes(layer_name, attributes)
    attrib.ObjectDecoration = docobj.ObjectDecoration.EndArrowhead
    return doc.Objects.AddLine(seg[0], seg[1], attrib)


def bake_point2d(point, z=0, layer_name=None, attributes=None):
    """Add ladybug Point2D to the Rhino scene as a Point."""
    doc = rhdoc.ActiveDoc
    pt = from_point2d(point, z)
    return doc.Objects.AddPoint(pt, _get_attributes(layer_name, attributes))


def bake_ray2d(ray, z=0, layer_name=None, attributes=None):
    """Add ladybug Ray2D to the Rhino scene as a Line with an Arrowhead."""
    doc = rhdoc.ActiveDoc
    seg = (from_point2d(ray.p, z), from_point2d(ray.p + ray.v, z))
    attrib = _get_attributes(layer_name, attributes)
    attrib.ObjectDecoration = docobj.ObjectDecoration.EndArrowhead
    return doc.Objects.AddLine(seg[0], seg[1], attrib)


def bake_linesegment2d(line, z=0, layer_name=None, attributes=None):
    """Add ladybug LineSegment2D to the Rhino scene as a Line."""
    doc = rhdoc.ActiveDoc
    seg = (from_point2d(line.p1, z), from_point2d(line.p2, z))
    return doc.Objects.AddLine(seg[0], seg[1], _get_attributes(layer_name, attributes))


def bake_polygon2d(polygon, z=0, layer_name=None, attributes=None):
    """Add ladybug Polygon2D to the Rhino scene as a Polyline."""
    doc = rhdoc.ActiveDoc
    pgon = [from_point2d(pt, z) for pt in polygon.vertices] + \
        [from_point2d(polygon[0], z)]
    return doc.Objects.AddPolyline(pgon, _get_attributes(layer_name, attributes))


def bake_arc2d(arc, z=0, layer_name=None, attributes=None):
    """Add ladybug Arc2D to the Rhino scene as an Arc or a Circle."""
    doc = rhdoc.ActiveDoc
    rh_arc = from_arc2d(arc, z)
    if arc.is_circle:
        return doc.Objects.AddCircle(rh_arc, _get_attributes(layer_name, attributes))
    else:
        return doc.Objects.AddArc(rh_arc, _get_attributes(layer_name, attributes))


def bake_polyline2d(polyline, z=0, layer_name=None, attributes=None):
    """Add ladybug Polyline2D to the Rhino scene as a Curve."""
    doc = rhdoc.ActiveDoc
    rh_crv = from_polyline2d(polyline, z)
    return doc.Objects.AddCurve(rh_crv, _get_attributes(layer_name, attributes))


def bake_mesh2d(mesh, z=0, layer_name=None, attributes=None):
    """Add ladybug Mesh2D to the Rhino scene as a Mesh."""
    doc = rhdoc.ActiveDoc
    _mesh = from_mesh2d(mesh, z)
    return doc.Objects.AddMesh(_mesh, _get_attributes(layer_name, attributes))


"""____________BAKE 3D GEOMETRY TO THE RHINO SCENE____________"""


def bake_vector3d(vector, layer_name=None, attributes=None):
    """Add ladybug Ray2D to the Rhino scene as a Line with an Arrowhead."""
    doc = rhdoc.ActiveDoc
    seg = (rg.Point3d(0, 0, 0), rg.Point3d(vector.x, vector.y, vector.z))
    attrib = _get_attributes(layer_name, attributes)
    attrib.ObjectDecoration = docobj.ObjectDecoration.EndArrowhead
    return doc.Objects.AddLine(seg[0], seg[1], attrib)


def bake_point3d(point, layer_name=None, attributes=None):
    """Add ladybug Point3D to the Rhino scene as a Point."""
    doc = rhdoc.ActiveDoc
    pt = from_point3d(point)
    return doc.Objects.AddPoint(pt, _get_attributes(layer_name, attributes))


def bake_ray3d(ray, layer_name=None, attributes=None):
    """Add ladybug Ray2D to the Rhino scene as a Line with an Arrowhead."""
    doc = rhdoc.ActiveDoc
    seg = (from_point3d(ray.p), from_point3d(ray.p + ray.v))
    attrib = _get_attributes(layer_name, attributes)
    attrib.ObjectDecoration = docobj.ObjectDecoration.EndArrowhead
    return doc.Objects.AddLine(seg[0], seg[1], attrib)


def bake_plane(plane, layer_name=None, attributes=None):
    """Add ladybug Plane to the Rhino scene as a Rectangle."""
    doc = rhdoc.ActiveDoc
    rh_pln = from_plane(plane)
    r = 10  # default radius for a plane object in rhino model units
    interval = rg.Interval(-r / 2, r / 2)
    rect = rg.Rectangle3d(rh_pln, interval, interval)
    return doc.Objects.AddRectangle(rect, _get_attributes(layer_name, attributes))


def bake_linesegment3d(line, layer_name=None, attributes=None):
    """Add ladybug LineSegment3D to the Rhino scene as a Line."""
    doc = rhdoc.ActiveDoc
    seg = (from_point3d(line.p1), from_point3d(line.p2))
    return doc.Objects.AddLine(seg[0], seg[1], _get_attributes(layer_name, attributes))


def bake_arc3d(arc, layer_name=None, attributes=None):
    """Add ladybug Arc3D to the Rhino scene as an Arc or Circle."""
    doc = rhdoc.ActiveDoc
    rh_arc = from_arc3d(arc)
    if arc.is_circle:
        return doc.Objects.AddCircle(rh_arc, _get_attributes(layer_name, attributes))
    else:
        return doc.Objects.AddArc(rh_arc, _get_attributes(layer_name, attributes))


def bake_polyline3d(polyline, layer_name=None, attributes=None):
    """Add ladybug Polyline3D to the Rhino scene as a Curve."""
    doc = rhdoc.ActiveDoc
    rh_crv = from_polyline3d(polyline)
    return doc.Objects.AddCurve(rh_crv, _get_attributes(layer_name, attributes))


def bake_mesh3d(mesh, layer_name=None, attributes=None):
    """Add ladybug Mesh3D to the Rhino scene as a Mesh."""
    doc = rhdoc.ActiveDoc
    _mesh = from_mesh3d(mesh)
    return doc.Objects.AddMesh(_mesh, _get_attributes(layer_name, attributes))


def bake_face3d(face, layer_name=None, attributes=None):
    """Add ladybug Face3D to the Rhino scene as a Brep."""
    doc = rhdoc.ActiveDoc
    _face = from_face3d(face)
    return doc.Objects.AddBrep(_face, _get_attributes(layer_name, attributes))


def bake_polyface3d(polyface, layer_name=None, attributes=None):
    """Add ladybug Polyface3D to the Rhino scene as a Brep."""
    doc = rhdoc.ActiveDoc
    rh_polyface = from_polyface3d(polyface)
    return doc.Objects.AddBrep(rh_polyface, _get_attributes(layer_name, attributes))


def bake_sphere(sphere, layer_name=None, attributes=None):
    """Add ladybug Sphere to the Rhino scene as a Brep."""
    doc = rhdoc.ActiveDoc
    rh_sphere = from_sphere(sphere).ToBrep()
    return doc.Objects.AddBrep(rh_sphere, _get_attributes(layer_name, attributes))


def bake_cone(cone, layer_name=None, attributes=None):
    """Add ladybug Cone to the Rhino scene as a Brep."""
    doc = rhdoc.ActiveDoc
    rh_cone = from_cone(cone).ToBrep()
    return doc.Objects.AddBrep(rh_cone, _get_attributes(layer_name, attributes))


def bake_cylinder(cylinder, layer_name=None, attributes=None):
    """Add ladybug Cylinder to the Rhino scene as a Brep."""
    doc = rhdoc.ActiveDoc
    rh_cylinder = from_cylinder(cylinder).ToBrep()
    return doc.Objects.AddBrep(rh_cylinder, _get_attributes(layer_name, attributes))


"""________ADDITIONAL 3D GEOMETRY TRANSLATORS________"""


def bake_mesh3d_as_hatch(mesh, layer_name=None, attributes=None):
    """Add ladybug Mesh3D to the Rhino scene as a colored hatch."""
    doc = rhdoc.ActiveDoc
    # get a list of colors that align with the mesh faces
    if mesh.colors is not None:
        if mesh.is_color_by_face:
            colors = [color_to_color(col) for col in mesh.colors]
        else:  # compute the average color across the vertices
            colors, v_cols = [], mesh.colors
            for face in mesh.faces:
                red = int(sum(v_cols[f].r for f in face) / len(face))
                green = int(sum(v_cols[f].g for f in face) / len(face))
                blue = int(sum(v_cols[f].b for f in face) / len(face))
                colors.append(Color.FromArgb(255, red, green, blue))
    else:
        colors = [gray()] * len(mesh.faces)

    # create hatches from each of the faces and get an aligned list of colors
    hatches, hatch_colors = [], []
    vertices = mesh.vertices
    for face, color in zip(mesh.faces, colors):
        f_verts = [from_point3d(vertices[f]) for f in face]
        f_verts.append(f_verts[0])
        p_line = rg.PolylineCurve(f_verts)
        if p_line.IsPlanar():
            hatches.append(rg.Hatch.Create(p_line, 0, 0, 0)[0])
            hatch_colors.append(color)
        elif len(face) == 4:
            p_line_1 = rg.PolylineCurve(f_verts[:3] + [f_verts[0]])
            p_line_2 = rg.PolylineCurve(f_verts[-3:] + [f_verts[-3]])
            hatches.append(rg.Hatch.Create(p_line_1, 0, 0, 0)[0])
            hatches.append(rg.Hatch.Create(p_line_2, 0, 0, 0)[0])
            hatch_colors.extend((color, color))

    # bake the hatches into the scene
    guids = []
    for hatch, color in zip(hatches, hatch_colors):
        attribs = _get_attributes(layer_name, attributes)
        attribs.ColorSource = docobj.ObjectColorSource.ColorFromObject
        attribs.ObjectColor = color
        guids.append(doc.Objects.AddHatch(hatch, attribs))

    # group the hatches so that they are easy to handle in the Rhino scene
    group_t = doc.Groups
    docobj.Tables.GroupTable.Add(group_t, guids)
    return guids


"""________________EXTRA HELPER FUNCTIONS________________"""


def _get_attributes(layer_name=None, attributes=None):
    """Get Rhino object attributes."""
    doc = rhdoc.ActiveDoc
    attributes = doc.CreateDefaultAttributes() if attributes is None else attributes
    if layer_name is None:
        return attributes
    elif isinstance(layer_name, int):
        attributes.LayerIndex = layer_name
    elif layer_name is not None:
        attributes.LayerIndex = _get_layer(layer_name)
    return attributes


def _get_layer(layer_name):
    """Get a layer index from the Rhino document from the layer name."""
    doc = rhdoc.ActiveDoc
    layer_table = doc.Layers  # layer table
    layer_index = layer_table.FindByFullPath(layer_name, RhinoMath.UnsetIntIndex)
    if layer_index == RhinoMath.UnsetIntIndex:
        all_layers = layer_name.split('::')
        parent_name = all_layers[0]
        layer_index = layer_table.FindByFullPath(parent_name, RhinoMath.UnsetIntIndex)
        if layer_index == RhinoMath.UnsetIntIndex:
            parent_layer = docobj.Layer()
            parent_layer.Name = parent_name
            layer_index = layer_table.Add(parent_layer)
        for lay in all_layers[1:]:
            parent_name = '{}::{}'.format(parent_name, lay)
            parent_index = layer_index
            layer_index = layer_table.FindByFullPath(
                parent_name, RhinoMath.UnsetIntIndex)
            if layer_index == RhinoMath.UnsetIntIndex:
                parent_layer = docobj.Layer()
                parent_layer.Name = lay
                parent_layer.ParentLayerId = layer_table[parent_index].Id
                layer_index = layer_table.Add(parent_layer)

    return layer_index
