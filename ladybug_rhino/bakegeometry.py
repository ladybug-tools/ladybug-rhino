"""Functions to bake from Ladybug geomtries into a Rhino document."""

from .fromgeometry import from_point2d, from_mesh2d, from_point3d, from_mesh3d, \
    from_face3d, from_polyface3d

try:
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


"""________________EXTRA HELPER FUNCTIONS________________"""


def _get_attributes(layer_name=None, attributes=None):
    """Get Rhino object attributes."""
    attributes = doc.CreateDefaultAttributes() if attributes is None else attributes
    if layer_name is not None:
        attributes.LayerIndex = _get_layer(layer_name)
    return attributes


def _get_layer(layer_name):
    """Get a layer index from the Rhino document from the ladyer name."""
    layer_table = doc.Layers  # layer table
    layer_index = layer_table.Find(layer_name, True)
    if layer_index < 0:
        parent_layer = docobj.Layer()
        parent_layer.Name = layer_name
        layer_index = layer_table.Add(parent_layer)
    return layer_index
