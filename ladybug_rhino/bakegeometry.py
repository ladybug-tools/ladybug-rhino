"""Functions to bake from Ladybug geomtries into a Rhino document."""
from .fromgeometry import from_point2d, from_mesh2d, from_point3d, from_mesh3d, \
    from_face3d, from_polyface3d
from .color import color_to_color, gray

try:
    from System.Drawing import Color
except ImportError as e:
    raise ImportError("Failed to import Windows/.NET libraries\n{}".format(e))

try:
    import Rhino.Geometry as rg
    import Rhino.RhinoDoc as rhdoc
    import Rhino.DocObjects as docobj
    doc = rhdoc.ActiveDoc
except ImportError as e:
    raise ImportError("Failed to import Rhino document attributes.\n{}".format(e))


"""____________ADD GEOMETRY TO THE RHINO SCENE____________"""


def add_point2d_to_scene(point, z=0, layer_name=None, attributes=None):
    """Add ladybug Point2D to the Rhino scene."""
    pt = from_point2d(point, z)
    return doc.Objects.AddPoint(pt, _get_attributes(layer_name, attributes))


def add_linesegment2d_to_scene(line, z=0, layer_name=None, attributes=None):
    """Add ladybug LineSegment2D to the Rhino scene."""
    seg = (from_point2d(line.p1, z), from_point2d(line.p2, z))
    return doc.Objects.AddLine(seg[0], seg[1], _get_attributes(layer_name, attributes))


def add_polygon2d_to_scene(polygon, z=0, layer_name=None, attributes=None):
    """Add ladybug Polygon2D to the Rhino scene."""
    pgon = [from_point2d(pt, z) for pt in polygon.vertices] + \
        [from_point2d(polygon[0], z)]
    return doc.Objects.AddPolyline(pgon, _get_attributes(layer_name, attributes))


def add_mesh2d_to_scene(mesh, z=0, layer_name=None, attributes=None):
    """Add ladybug Mesh2D to the Rhino scene."""
    _mesh = from_mesh2d(mesh, z)
    return doc.Objects.AddMesh(_mesh, _get_attributes(layer_name, attributes))


def add_point3d_to_scene(point, layer_name=None, attributes=None):
    """Add ladybug Point3D to the Rhino scene."""
    pt = from_point3d(point)
    return doc.Objects.AddPoint(pt, _get_attributes(layer_name, attributes))


def add_linesegment3d_to_scene(line, layer_name=None, attributes=None):
    """Add ladybug LineSegment3D to the Rhino scene."""
    seg = (from_point3d(line.p1), from_point3d(line.p2))
    return doc.Objects.AddLine(seg[0], seg[1], _get_attributes(layer_name, attributes))


def add_mesh3d_to_scene(mesh, layer_name=None, attributes=None):
    """Add ladybug Mesh3D to the Rhino scene."""
    _mesh = from_mesh3d(mesh)
    return doc.Objects.AddMesh(_mesh, _get_attributes(layer_name, attributes))


def add_face3d_to_scene(face, layer_name=None, attributes=None):
    """Add ladybug Face3D to the Rhino scene."""
    _face = from_face3d(face)
    return doc.Objects.AddBrep(_face, _get_attributes(layer_name, attributes))


def add_polyface3d_to_scene(polyface, layer_name=None, attributes=None):
    """Add ladybug Polyface3D to the Rhino scene."""
    _pface = from_polyface3d(polyface)
    return doc.Objects.AddBrep(_pface, _get_attributes(layer_name, attributes))


"""________ADDITIONAL 3D GEOMETRY TRANSLATORS________"""


def add_mesh3d_as_hatch_to_scene(mesh, layer_name=None, attributes=None):
    """Add ladybug Mesh3D to the Rhino scene as a colored hatch."""
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
    attributes = doc.CreateDefaultAttributes() if attributes is None else attributes
    if layer_name is not None:
        attributes.LayerIndex = _get_layer(layer_name)
    return attributes


def _get_layer(layer_name):
    """Get a layer index from the Rhino document from the layer name."""
    layer_table = doc.Layers  # layer table
    layer_index = layer_table.FindByFullPath(layer_name, True)
    if layer_index < 0:
        all_layers = layer_name.split('::')
        parent_name = all_layers[0]
        layer_index = layer_table.FindByFullPath(parent_name, True)
        if layer_index < 0:
            parent_layer = docobj.Layer()
            parent_layer.Name = parent_name
            layer_index = layer_table.Add(parent_layer)
        for lay in all_layers[1:]:
            parent_name = '{}::{}'.format(parent_name, lay)
            parent_index = layer_index
            layer_index = layer_table.FindByFullPath(parent_name, True)
            if layer_index < 0:
                parent_layer = docobj.Layer()
                parent_layer.Name = lay
                parent_layer.ParentLayerId = layer_table[parent_index].Id 
                layer_index = layer_table.Add(parent_layer)
    return layer_index
