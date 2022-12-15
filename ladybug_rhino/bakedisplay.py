"""Functions to add text to the Rhino scene and create Grasshopper text objects."""
from ladybug_display.altnumber import Default

from .color import color_to_color, argb_color_to_color
from .fromgeometry import from_plane
from .bakegeometry import _get_attributes, bake_point2d, bake_vector2d, bake_ray2d, \
    bake_linesegment2d, bake_arc2d, bake_polygon2d, bake_polyline2d, bake_mesh2d, \
    bake_point3d, bake_vector3d, bake_ray3d, bake_linesegment3d, bake_plane, \
    bake_arc3d, bake_polyline3d, bake_mesh3d, bake_face3d, bake_polyface3d, \
    bake_sphere, bake_cone, bake_cylinder

try:
    import Rhino.Display as rd
    import Rhino.DocObjects as docobj
    import Rhino.RhinoDoc as rhdoc
    doc = rhdoc.ActiveDoc
except ImportError as e:
    raise ImportError("Failed to import Rhino document attributes.\n{}".format(e))

TEXT_HORIZ = {
    'Left': docobj.TextHorizontalAlignment.Left,
    'Center': docobj.TextHorizontalAlignment.Center,
    'Right': docobj.TextHorizontalAlignment.Right
}
TEXT_VERT = {
    'Top': docobj.TextVerticalAlignment.Top,
    'Middle': docobj.TextVerticalAlignment.Middle,
    'Bottom': docobj.TextVerticalAlignment.Bottom
}
LINE_WIDTH_FACTOR = 3.779528  # factor to translate pixel width to millimeters
LINE_TYPES = {
    'Continuous': -1,
    'Dashed': -1,
    'Dotted': -1,
    'DashDot': -1
}
_display_lts = ('Continuous', 'Dashed', 'Dots', 'DashDot')
for i, lt in enumerate(doc.Linetypes):
    lt_name = lt.Name
    for dlt in _display_lts:
        if lt_name == dlt:
            dlt = dlt if dlt != 'Dots' else 'Dotted'
            LINE_TYPES[dlt] = i
            break


"""____________BAKE 2D DISPLAY GEOMETRY TO THE RHINO SCENE____________"""


def bake_display_vector2d(vector, z=0, layer_name=None, attributes=None):
    """Add DisplayVector2D to the Rhino scene as a Line with an Arrowhead."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, vector)
    return bake_vector2d(vector.geometry, z, attributes=attrib)


def bake_display_point2d(point, z=0, layer_name=None, attributes=None):
    """Add ladybug Point2D to the Rhino scene as a Point."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, point)
    return bake_point2d(point.geometry, z, attributes=attrib)


def bake_display_ray2d(ray, z=0, layer_name=None, attributes=None):
    """Add DisplayRay2D to the Rhino scene as a Line with an Arrowhead."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, ray)
    return bake_ray2d(ray.geometry, z, attributes=attrib)


def bake_display_linesegment2d(line, z=0, layer_name=None, attributes=None):
    """Add DisplayLineSegment2D to the Rhino scene as a Line."""
    attrib = _get_attributes(layer_name, attributes)
    _line_like_attributes(attrib, line)
    return bake_linesegment2d(line.geometry, z, attributes=attrib)


def bake_display_polygon2d(polygon, z=0, layer_name=None, attributes=None):
    """Add DisplayPolygon2D to the Rhino scene as a Polyline."""
    attrib = _get_attributes(layer_name, attributes)
    _line_like_attributes(attrib, polygon)
    return bake_polygon2d(polygon.geometry, z, attributes=attrib)


def bake_display_arc2d(arc, z=0, layer_name=None, attributes=None):
    """Add DisplayArc2D to the Rhino scene as an Arc or a Circle."""
    attrib = _get_attributes(layer_name, attributes)
    _line_like_attributes(attrib, arc)
    return bake_arc2d(arc.geometry, z, attributes=attrib)


def bake_display_polyline2d(polyline, z=0, layer_name=None, attributes=None):
    """Add DisplayPolyline2D to the Rhino scene as a Curve."""
    attrib = _get_attributes(layer_name, attributes)
    _line_like_attributes(attrib, polyline)
    return bake_polyline2d(polyline.geometry, z, attributes=attrib)


def bake_display_mesh2d(mesh, z=0, layer_name=None, attributes=None):
    """Add DisplayMesh2D to the Rhino scene as a Mesh."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, mesh)
    return bake_mesh2d(mesh.geometry, z, attributes=attrib)


"""____________BAKE 3D DISPLAY GEOMETRY TO THE RHINO SCENE____________"""


def bake_display_vector3d(vector, layer_name=None, attributes=None):
    """Add DisplayVector3D to the Rhino scene as a Line with an Arrowhead."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, vector)
    return bake_vector3d(vector.geometry, attributes=attrib)


def bake_display_point3d(point, layer_name=None, attributes=None):
    """Add ladybug Point3D to the Rhino scene as a Point."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, point)
    return bake_point3d(point.geometry, attributes=attrib)


def bake_display_ray3d(ray, layer_name=None, attributes=None):
    """Add DisplayRay3D to the Rhino scene as a Line with an Arrowhead."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, ray)
    return bake_ray3d(ray.geometry, attributes=attrib)


def bake_display_plane(plane, layer_name=None, attributes=None):
    """Add DisplayPlane to the Rhino scene as a Rectangle."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, plane)
    return bake_plane(plane.geometry, attributes=attrib)


def bake_display_linesegment3d(line, layer_name=None, attributes=None):
    """Add DisplayLineSegment3D to the Rhino scene as a Line."""
    attrib = _get_attributes(layer_name, attributes)
    _line_like_attributes(attrib, line)
    return bake_linesegment3d(line.geometry, attributes=attrib)


def bake_display_arc3d(arc, layer_name=None, attributes=None):
    """Add DisplayArc3D to the Rhino scene as an Arc or a Circle."""
    attrib = _get_attributes(layer_name, attributes)
    _line_like_attributes(attrib, arc)
    return bake_arc3d(arc.geometry, attributes=attrib)


def bake_display_polyline3d(polyline, layer_name=None, attributes=None):
    """Add DisplayPolyline3D to the Rhino scene as a Curve."""
    attrib = _get_attributes(layer_name, attributes)
    _line_like_attributes(attrib, polyline)
    return bake_polyline3d(polyline.geometry, attributes=attrib)


def bake_display_mesh3d(mesh, layer_name=None, attributes=None):
    """Add DisplayMesh3D to the Rhino scene as a Mesh."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, mesh)
    return bake_mesh3d(mesh.geometry, attributes=attrib)


def bake_display_face3d(face, layer_name=None, attributes=None):
    """Add DisplayFace3D to the Rhino scene as a Brep."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, face)
    return bake_face3d(face.geometry, attributes=attrib)


def bake_display_polyface3d(polyface, layer_name=None, attributes=None):
    """Add DisplayPolyface3D to the Rhino scene as a Brep."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, polyface)
    return bake_polyface3d(polyface.geometry, attributes=attrib)


def bake_display_sphere(sphere, layer_name=None, attributes=None):
    """Add DisplaySphere to the Rhino scene as a Brep."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, sphere)
    return bake_sphere(sphere.geometry, attributes=attrib)


def bake_display_cone(cone, layer_name=None, attributes=None):
    """Add DisplayCone to the Rhino scene as a Brep."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, cone)
    return bake_cone(cone.geometry, attributes=attrib)


def bake_display_cylinder(cylinder, layer_name=None, attributes=None):
    """Add DisplayCylinder to the Rhino scene as a Brep."""
    attrib = _get_attributes(layer_name, attributes)
    _color_attribute(attrib, cylinder)
    return bake_cylinder(cylinder.geometry, attributes=attrib)


def bake_display_text3d(display_text, layer_name=None, attributes=None):
    """Add DisplayText3D to the Rhino scene.

    Args:
        display_text: A DisplayText3D object to be added to the Rhino scene.
        layer_name: Optional text string for the layer name on which to place the
            text. If None, text will be added to the current layer.
        attributes: Optional Rhino attributes for adding to the Rhino scene.
    """
    d_txt = display_text.text
    nl_count = len(d_txt.split('\n')) - 1
    if nl_count > 1:
        m_vec = display_text.plane.y * (nl_count * display_text.height * -1.5)
        t_pln = display_text.plane.move(m_vec)
    else:
        t_pln = display_text.plane
    txt_h = display_text.height * 0.666
    txt = rd.Text3d(d_txt, from_plane(t_pln), txt_h)
    txt.FontFace = display_text.font
    txt.HorizontalAlignment = TEXT_HORIZ[display_text.horizontal_alignment]
    txt.VerticalAlignment = TEXT_VERT[display_text.vertical_alignment]
    attrib = _get_attributes(layer_name, attributes)
    attrib.ObjectColor = color_to_color(display_text.color)
    return doc.Objects.AddText(txt, attrib)


"""________________EXTRA HELPER FUNCTIONS________________"""


def _color_attribute(attrib, display_obj):
    """Process the attributes of a colored display object."""
    attrib.ColorSource = docobj.ObjectColorSource.ColorFromObject
    attrib.ObjectColor = argb_color_to_color(display_obj.color)


def _line_like_attributes(attrib, display_obj):
    """Process the attributes of a line-like display object."""
    _color_attribute(attrib, display_obj)
    if not isinstance(display_obj.line_width, Default):
        attrib.PlotWeightSource = docobj.ObjectPlotWeightSource.PlotWeightFromObject
        attrib.PlotWeight = display_obj.line_width / LINE_WIDTH_FACTOR
    attrib.LinetypeSource = docobj.ObjectLinetypeSource.LinetypeFromObject
    attrib.LinetypeIndex = LINE_TYPES[display_obj.line_type]
