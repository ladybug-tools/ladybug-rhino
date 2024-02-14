"""Classes to preview things in the Rhino Display Pipeline."""
from __future__ import division

from ladybug_geometry.geometry2d import Vector2D, Point2D, Ray2D, LineSegment2D, \
    Polyline2D, Arc2D, Polygon2D, Mesh2D
from ladybug_geometry.geometry3d import Vector3D, Point3D, Ray3D, Plane, LineSegment3D, \
    Polyline3D, Arc3D, Face3D, Mesh3D, Polyface3D, Sphere, Cone, Cylinder

from ladybug.graphic import GraphicContainer
from ladybug_display.altnumber import Default
from ladybug_display.geometry3d import DisplayText3D
from ladybug_display.visualization import AnalysisGeometry

from .config import units_system
from .color import color_to_color, argb_color_to_color, black
from .fromgeometry import from_point2d, from_vector2d, from_ray2d, \
    from_arc2d, from_polygon2d, from_polyline2d, from_mesh2d, \
    from_point3d, from_vector3d, from_ray3d, from_plane, \
    from_arc3d, from_polyline3d, from_mesh3d, from_face3d, from_polyface3d, \
    from_sphere, from_cone, from_cylinder

try:
    import System
except ImportError as e:
    raise ImportError("Failed to import Windows/.NET libraries\n{}".format(e))

try:
    import Rhino.Geometry as rg
    import Rhino.Display as rd
    import Rhino.DocObjects as ro
except ImportError as e:
    raise ImportError('Failed to import Rhino.\n{}'.format(e))

try:
    import scriptcontext as sc
except ImportError:
    pass  # previewing 2D legends will not be available


class VisualizationSetConduit(rd.DisplayConduit):
    """Class to preview VisualizationSet in the Rhino Display pipeline.
    
    Args:
        visualization_set: A Ladybug Display VisualizationSet object to be translated
            into arguments for the Rhino display pipeline.
        render_3d_legend: A Boolean to note whether the VisualizationSet should be
            rendered with 3D legends for any AnalysisGeometries it
            includes. (Default: False).
        render_2d_legend: A Boolean to note whether the VisualizationSet should be
            rendered with 2D screen-oriented legends for any AnalysisGeometries it
            includes. (Default: False).
    """

    def __init__(self, visualization_set, render_3d_legend=False, render_2d_legend=False):
        """Initialize VisualizationSetConduit."""
        # set the primary properties
        self.vis_con = VisualizationSetConverter(
            visualization_set, render_3d_legend, render_2d_legend)

    def CalculateBoundingBox(self, calculateBoundingBoxEventArgs):
        """Overwrite the method that passes the bounding box to the display."""
        calculateBoundingBoxEventArgs.IncludeBoundingBox(self.vis_con.bbox)

    def DrawForeground(self, drawEventArgs):
        """Overwrite the method that draws the objects in the display."""
        # get the DisplayPipeline from the event arguments
        display = drawEventArgs.Display

        # for each object to be rendered, pass the drawing arguments
        for draw_args in self.vis_con.draw_2d_text:
            display.Draw2dText(*draw_args)
        for draw_args in self.vis_con.draw_sprite:
            display.DrawSprite(*draw_args)

    def PreDrawObjects(self, drawEventArgs):
        """Overwrite the method that draws the objects in the display."""
        # get the DisplayPipeline from the event arguments
        display = drawEventArgs.Display

        # for each object to be rendered, pass the drawing arguments
        for draw_args in self.vis_con.draw_mesh_false_colors:
            display.DrawMeshFalseColors(draw_args)
        for draw_args in self.vis_con.draw_mesh_shaded:
            display.DrawMeshFalseColors(draw_args[0])
        for draw_args in self.vis_con.draw_brep_shaded:
            display.DrawBrepShaded(*draw_args)

    def PostDrawObjects(self, drawEventArgs):
        """Overwrite the method that draws the objects in the display."""
        # get the DisplayPipeline from the event arguments
        display = drawEventArgs.Display

        # for each object to be rendered, pass the drawing arguments
        for draw_args in self.vis_con.draw_3d_text:
            display.Draw3dText(*draw_args)
        for draw_args in self.vis_con.draw_mesh_wires:
            display.DrawMeshWires(*draw_args)
        for draw_args in self.vis_con.draw_mesh_vertices:
            display.DrawMeshVertices(*draw_args)
        for draw_args in self.vis_con.draw_point:
            display.DrawPoint(*draw_args)
        for draw_args in self.vis_con.draw_arrow:
            display.DrawArrow(*draw_args)
        for draw_args in self.vis_con.draw_brep_wires:
            display.DrawBrepWires(*draw_args)
        for draw_args in self.vis_con.draw_line:
            display.DrawLine(*draw_args)
        for draw_args in self.vis_con.draw_patterned_line:
            display.DrawPatternedLine(*draw_args)
        for draw_args in self.vis_con.draw_patterned_polyline:
            display.DrawPatternedPolyline(*draw_args)
        for draw_args in self.vis_con.draw_curve:
            display.DrawCurve(*draw_args)
        for draw_args in self.vis_con.draw_circle:
            display.DrawCircle(*draw_args)
        for draw_args in self.vis_con.draw_arc:
            display.DrawArc(*draw_args)
        for draw_args in self.vis_con.draw_sphere:
            display.DrawSphere(*draw_args)
        for draw_args in self.vis_con.draw_cone:
            display.DrawCone(*draw_args)
        for draw_args in self.vis_con.draw_cylinder:
            display.DrawCylinder(*draw_args)


class VisualizationSetConverter(object):
    """Class to translate VisualizationSets to arguments for the Rhino display pipeline.

    Args:
        visualization_set: A Ladybug Display VisualizationSet object to be translated
            into arguments for the Rhino display pipeline.
        render_3d_legend: A Boolean to note whether the VisualizationSet should be
            rendered with 3D legends for any AnalysisGeometries it
            includes. (Default: False).
        render_2d_legend: A Boolean to note whether the VisualizationSet should be
            rendered with 2D screen-oriented legends for any AnalysisGeometries it
            includes. (Default: False).

    Properties:
        * vis_set
        * render_3d_legend
        * render_2d_legend
        * min_pt
        * max_pt
        * bbox
        * draw_sprite
        * draw_2d_text
        * draw_3d_text
        * draw_mesh_false_colors
        * draw_mesh_shaded
        * draw_mesh_wires
        * draw_mesh_vertices
        * draw_brep_shaded
        * draw_brep_wires
        * draw_point
        * draw_arrow
        * draw_line
        * draw_patterned_line
        * draw_patterned_polyline
        * draw_curve
        * draw_circle
        * draw_arc
        * draw_sphere
        * draw_cone
        * draw_cylinder
    """
    TEXT_HORIZ = {
        'Left': ro.TextHorizontalAlignment.Left,
        'Center': ro.TextHorizontalAlignment.Center,
        'Right': ro.TextHorizontalAlignment.Right
    }
    TEXT_VERT = {
        'Top': ro.TextVerticalAlignment.Top,
        'Middle': ro.TextVerticalAlignment.Middle,
        'Bottom': ro.TextVerticalAlignment.Bottom
    }
    LINE_TYPE = {
        'Dashed': int('0x1C7', base=16),
        'Dotted': int('0x00001111', base=16),
        'DashDot': int('0x1F11F1', base=16)
    }

    def __init__(
            self, visualization_set, render_3d_legend=False, render_2d_legend=False):
        """Initialize VisualizationSetConverter."""
        # set the primary properties
        self.vis_set = visualization_set
        self.render_3d_legend = bool(render_3d_legend)
        self.render_2d_legend = bool(render_2d_legend)

        # get the active viewport width and height if 2D legends are requested
        if self.render_2d_legend:
            active_view = sc.doc.Views.ActiveView.ActiveViewport
            v_size = active_view.Size
            self.view_width = v_size.Width
            self.view_height = v_size.Height
        else:  # just use some defaults as it's probably not critical
            self.view_width, self.view_height = 800, 600

        # ensure the visualization set is in Rhino model units
        units_sys = units_system()
        if self.vis_set.units is not None and units_sys is not None \
                and self.vis_set.units != units_sys:
            self.vis_set.convert_to_units(units_sys)

        # set up the bounding box and min/max point
        self.min_pt = self.vis_set.min_point
        self.max_pt = self.vis_set.max_point
        if self.render_3d_legend:  # leave extra room for legend
            center = Point3D(
                (self.min_pt.x + self.max_pt.x) / 2,
                (self.min_pt.y + self.max_pt.y) / 2,
                (self.min_pt.z + self.max_pt.z) / 2)
            self.bbox = rg.BoundingBox(
                from_point3d(self.min_pt.scale(2, center)),
                from_point3d(self.max_pt.scale(2, center)))
        else:
            self.bbox = rg.BoundingBox(
                from_point3d(self.min_pt), from_point3d(self.max_pt))

        # translate all of the rhino objects to be rendered in the scene
        self.translate_objects()
        self.sort_shaded_objects()

    def translate_objects(self):
        """Translate all of the objects in the VisualizationSet into a Rhino equivalent.

        This is a necessary pre-step before frames of the visualization set
        can be rendered in the display pipeline.
        """
        # initialize all of the lists to hold the drawing arguments
        self.draw_sprite = []
        self.draw_2d_text = []
        self.draw_3d_text = []
        self.draw_mesh_false_colors = []
        self.draw_mesh_shaded = []
        self.draw_mesh_wires = []
        self.draw_mesh_vertices = []
        self.draw_brep_shaded = []
        self.draw_brep_wires = []
        self.draw_point = []
        self.draw_arrow = []
        self.draw_line = []
        self.draw_patterned_line = []
        self.draw_patterned_polyline = []
        self.draw_curve = []
        self.draw_circle = []
        self.draw_arc = []
        self.draw_sphere = []
        self.draw_cone = []
        self.draw_cylinder = []

        # loop through visualization geometry objects and draw them
        default_leg_x3d, default_leg_x2d, default_leg_y2d = 0, 10, 50
        for geo in self.vis_set.geometry:
            if geo.hidden:
                continue
            # translate it as AnalysisGeometry if specified
            if isinstance(geo, AnalysisGeometry):
                # generate the colors that correspond to the values
                data = geo.data_sets[geo.active_data]
                graphic = GraphicContainer(
                    data.values, self.min_pt, self.max_pt,
                    data.legend_parameters, data.data_type, data.unit)
                colors = graphic.value_colors
                # translate the analysis geometry using the matching method
                if geo.matching_method == 'faces':
                    c_count = 0
                    for mesh in geo.geometry:
                        mesh.colors = colors[c_count:c_count + len(mesh.faces)]
                        c_count += len(mesh.faces)
                        self.translate_analysis_mesh(mesh, geo.display_mode)
                elif geo.matching_method == 'vertices':
                    c_count = 0
                    for mesh in geo.geometry:
                        mesh.colors = colors[c_count:c_count + len(mesh.vertices)]
                        c_count += len(mesh.vertices)
                        self.translate_analysis_mesh(mesh, geo.display_mode)
                else:  # one color per geometry object
                    for geo_obj, col in zip(geo.geometry, colors):
                        self.translate_analysis_geometry(
                            geo_obj, col, geo.display_mode)
                # if the object is set to translate 3D legends, then display it
                if self.render_3d_legend:
                    # ensure multiple legends are not on top of each other
                    if graphic.legend_parameters.is_base_plane_default:
                        l_par = graphic.legend_parameters
                        m_vec = Vector3D(default_leg_x3d, 0, 0)
                        l_par.base_plane = l_par.base_plane.move(m_vec)
                        l_par.properties_3d._is_base_plane_default = True
                        leg_width = l_par.segment_width + 6 * l_par.text_height \
                            if l_par.vertical else \
                            l_par.segment_width * (l_par.segment_count + 2)
                        default_leg_x3d += leg_width
                    self.translate_legend3d(graphic.legend)
                # if the object is set to translate 2D legends, then display it
                if self.render_2d_legend:
                    # ensure multiple legends are not on top of each other
                    l_par = graphic.legend_parameters
                    if l_par.vertical and l_par.is_origin_x_default:
                        l_par.origin_x = '{}px'.format(default_leg_x2d)
                        l_par.properties_2d._is_origin_x_default = True
                        sw = graphic.legend.parse_dim_2d(
                            l_par.segment_width_2d, self.view_width)
                        th = graphic.legend.parse_dim_2d(
                            l_par.text_height_2d, self.view_height)
                        leg_width = sw + 6 * th
                        default_leg_x2d += leg_width
                    elif not l_par.vertical and l_par.is_origin_y_default:
                        l_par.origin_y = '{}px'.format(default_leg_y2d)
                        l_par.properties_2d._is_origin_y_default = True
                        sh = graphic.legend.parse_dim_2d(
                            l_par.segment_height_2d, self.view_height)
                        th = graphic.legend.parse_dim_2d(
                            l_par.text_height_2d, self.view_height)
                        leg_height = sh + 4 * th
                        default_leg_y2d += leg_height
                    self.translate_legend2d(graphic.legend)
            else:  # it's a ContextGeometry object
                for display_obj in geo.geometry:
                    if isinstance(display_obj, DisplayText3D):
                        self.translate_display_text3d(display_obj)
                    else:
                        self.translate_context_geometry(display_obj)

    def translate_display_text3d(self, text_obj):
        """Translate ladybug DisplayText3D into arguments for drawing in the scene.

        Args:
            text_obj: The ladybug DisplayText3D to be translated.
        """
        self.draw_3d_text.append((
            text_obj.text, color_to_color(text_obj.color), from_plane(text_obj.plane),
            text_obj.height, text_obj.font, False, False,
            self.TEXT_HORIZ[text_obj.horizontal_alignment],
            self.TEXT_VERT[text_obj.vertical_alignment]))

    def translate_legend3d(self, legend):
        """Translate a ladybug Legend into arguments for drawing in the scene.

        Args:
            legend: A Ladybug Legend object to be converted to Rhino geometry.
        """
        # translate the legend mesh
        rh_mesh = from_mesh3d(legend.segment_mesh)
        self.draw_mesh_false_colors.append(rh_mesh)
        self.draw_mesh_wires.append((rh_mesh, black()))

        # translate the legend text
        _height = legend.legend_parameters.text_height
        _font = legend.legend_parameters.font
        if legend.legend_parameters.continuous_legend is False:
            legend_text = [
                DisplayText3D(txt, loc, _height, None, _font, 'Left', 'Bottom')
                for txt, loc in zip(legend.segment_text, legend.segment_text_location)]
        elif legend.legend_parameters.vertical is True:
            legend_text = [
                DisplayText3D(txt, loc, _height, None, _font, 'Left', 'Middle')
                for txt, loc in zip(legend.segment_text, legend.segment_text_location)]
        else:
            legend_text = [
                DisplayText3D(txt, loc, _height, None, _font, 'Center', 'Bottom')
                for txt, loc in zip(legend.segment_text, legend.segment_text_location)]
        legend_title = DisplayText3D(
            legend.title, legend.title_location, _height, None, _font)
        legend_text.insert(0, legend_title)
        for txt_obj in legend_text:
            self.translate_display_text3d(txt_obj)

    def translate_legend2d(self, legend):
        """Translate a ladybug Legend into arguments for drawing in the scene.

        Args:
            legend: A Ladybug Legend object to be converted to 2D
                screen-oriented geometry.
        """
        d_sprite, d_2d_text = self.convert_legend2d(
            legend, self.view_width, self.view_height)
        self.draw_sprite.append(d_sprite)
        self.draw_2d_text.extend(d_2d_text)

    def translate_analysis_mesh(self, mesh, display_mode):
        """Translate an analysis mesh into arguments for drawing in the scene.

        Args:
            mesh: The Ladybug Mesh3D or Mesh2D object to be translated.
            display_mode: Text for the display mode in which to translate the mesh.
        """
        if display_mode in ('Surface', 'SurfaceWithEdges'):
            rh_mesh = from_mesh3d(mesh) if isinstance(mesh, Mesh3D) \
                else from_mesh2d(mesh)
            self.draw_mesh_false_colors.append(rh_mesh)
            if display_mode == 'SurfaceWithEdges':
                self.draw_mesh_wires.append((rh_mesh, black()))
        elif display_mode == 'Wireframe':
            rh_mesh = from_mesh3d(mesh) if isinstance(mesh, Mesh3D) \
                else from_mesh2d(mesh)
            self.draw_mesh_wires.append((rh_mesh, black()))
        elif display_mode == 'Points':
            if isinstance(mesh, Mesh3D):
                points = [from_point3d(pt) for pt in mesh.face_centroids] \
                    if mesh.is_color_by_face else \
                    [from_point3d(pt) for pt in mesh.vertices]
            else:
                points = [from_point2d(pt) for pt in mesh.face_centroids] \
                    if mesh.is_color_by_face else \
                    [from_point2d(pt) for pt in mesh.vertices]
            colors = [color_to_color(col) for col in mesh.colors]
            for col, pt in zip(colors, points):
                self.draw_point.append((pt, rd.PointStyle.RoundSimple, 3, col))

    def translate_analysis_geometry(self, geo_obj, color, display_mode):
        """Translate analysis geometry objects into arguments for drawing in the scene.

        Args:
            geo_obj: The Ladybug Geometry object to be translated.
            color: The Ladybug Color object with which the object will be translated.
            display_mode: Text for the display mode in which to translate the mesh.
        """
        # translate the color
        col = color_to_color(color)

        if isinstance(geo_obj, (Point3D, Point2D)):
            # translate analysis point
            pt = from_point3d(geo_obj) if isinstance(geo_obj, Point3D) \
                else from_point2d(geo_obj)
            self.draw_point.append((pt, rd.PointStyle.RoundSimple, 5, col))

        elif isinstance(geo_obj, (LineSegment3D, LineSegment2D)):
            # translate analysis line segment
            if isinstance(geo_obj, LineSegment3D):
                pt1, pt2 = from_point3d(geo_obj.p1), from_point3d(geo_obj.p2)
            else:
                pt1, pt2 = from_point2d(geo_obj.p1), from_point2d(geo_obj.p2)
            self.draw_line.append((pt1, pt2, col, 3))

        elif isinstance(geo_obj, (Polyline3D, Polyline2D)):
            # translate analysis polyline
            crv = from_polyline3d(geo_obj) if isinstance(geo_obj, Polyline3D) \
                else from_polyline2d(geo_obj)
            self.draw_curve.append((crv, col, 3))

        elif isinstance(geo_obj, (Face3D, Polyface3D)):
            # translate analysis Face3D and Polyface3D
            if display_mode in ('Surface', 'SurfaceWithEdges'):
                mat = rd.DisplayMaterial(col)
                rh_obj = from_face3d(geo_obj) if isinstance(geo_obj, Face3D) \
                    else from_polyface3d(geo_obj)
                self.draw_brep_shaded.append((rh_obj, mat))
                if display_mode == 'SurfaceWithEdges':
                    self.draw_brep_wires.append((rh_obj, black(), -1))
            elif display_mode == 'Wireframe':
                rh_obj = from_face3d(geo_obj) if isinstance(geo_obj, Face3D) \
                    else from_polyface3d(geo_obj)
                self.draw_brep_wires.append((rh_obj, col, 1))
            elif display_mode == 'Points':
                for pt in geo_obj.vertices:
                    self.draw_point.append(
                        (from_point3d(pt), rd.PointStyle.RoundSimple, 3, col))

        elif isinstance(geo_obj, (Mesh3D, Mesh2D)):
            # translate analysis mesh
            rh_obj = from_mesh3d(geo_obj) if isinstance(geo_obj, Mesh3D) \
                else from_mesh2d(geo_obj)
            if display_mode in ('Surface', 'SurfaceWithEdges'):
                mat = rd.DisplayMaterial(col)
                rh_obj.VertexColors.CreateMonotoneMesh(col)
                self.draw_mesh_shaded.append((rh_obj, mat))
                if display_mode == 'SurfaceWithEdges':
                    self.draw_mesh_wires.append((rh_obj, black(), 1))
            elif display_mode == 'Wireframe':
                self.draw_mesh_wires.append((rh_obj, col, 3))
            elif display_mode == 'Points':
                self.draw_mesh_vertices.append((rh_obj, col))

        elif isinstance(geo_obj, (Ray2D, Ray3D)):
            # translate analysis rays
            rh_ray = from_ray3d(geo_obj) if isinstance(geo_obj, Ray3D) \
                else from_ray2d(geo_obj)
            rh_obj = rg.Line(rh_ray.Position, rh_ray.Direction)
            self.draw_arrow.append((rh_obj, col))

        elif isinstance(geo_obj, Sphere):
            # translate analysis sphere
            if display_mode in ('Surface', 'SurfaceWithEdges'):
                rh_obj, mat = from_sphere(geo_obj), rd.DisplayMaterial(col)
                self.draw_brep_shaded.append((rh_obj.ToBrep(), mat))
                if display_mode == 'SurfaceWithEdges':
                    self.draw_sphere.append((rh_obj, black()))
            elif display_mode == 'Wireframe':
                self.draw_sphere.append((from_sphere(geo_obj), col))
            elif display_mode == 'Points':
                pt_arg = (from_point3d(geo_obj.center),
                          rd.PointStyle.RoundSimple, 3, col)
                self.draw_point.append(pt_arg)

        elif isinstance(geo_obj, (Vector2D, Vector3D)):
            # translate analysis vectors
            rh_vec = from_vector3d(geo_obj) if isinstance(geo_obj, Vector3D) \
                else from_vector2d(geo_obj)
            rh_obj = rg.Line(rg.Point3d(0, 0, 0), rh_vec)
            self.draw_arrow.append((rh_obj, col))

        elif isinstance(geo_obj, Polygon2D):
            # translate analysis polygon
            self.draw_curve.append((from_polygon2d(geo_obj), col, 3))

        elif isinstance(geo_obj, (Arc3D, Arc2D)):
            # translate analysis arcs
            crv = from_arc3d(geo_obj) if isinstance(geo_obj, Arc3D) \
                else from_arc2d(geo_obj)
            if geo_obj.is_circle:
                self.draw_circle.append((crv, col, 3))
            else:
                self.draw_arc.append((crv, col, 3))

        elif isinstance(geo_obj, Cone):
            # translate analysis cone
            if display_mode in ('Surface', 'SurfaceWithEdges'):
                rh_obj, mat = from_cone(geo_obj), rd.DisplayMaterial(col)
                self.draw_brep_shaded.append((rh_obj.ToBrep(True), mat))
                if display_mode == 'SurfaceWithEdges':
                    self.draw_cone.append((rh_obj, black()))
            elif display_mode == 'Wireframe':
                self.draw_cone.append((from_cone(geo_obj), col))
            elif display_mode == 'Points':
                pt_arg = (from_point3d(geo_obj.vertex),
                          rd.PointStyle.RoundSimple, 3, col)
                self.draw_point.append(pt_arg)

        elif isinstance(geo_obj, Cylinder):
            # translate analysis cylinder
            if display_mode in ('Surface', 'SurfaceWithEdges'):
                rh_obj, mat = from_cylinder(geo_obj), rd.DisplayMaterial(col)
                self.draw_brep_shaded.append((rh_obj.ToBrep(True, True), mat))
                if display_mode == 'SurfaceWithEdges':
                    self.draw_cylinder.append((rh_obj, black()))
            elif display_mode == 'Wireframe':
                self.draw_cylinder.append((from_cylinder(geo_obj), col))
            elif display_mode == 'Points':
                pt_arg = (from_point3d(geo_obj.center),
                          rd.PointStyle.RoundSimple, 3, col)
                self.draw_point.append(pt_arg)

        elif isinstance(geo_obj, Plane):
            # translate analysis planes
            pln = from_plane(geo_obj)
            r = 10  # default radius for a plane object in rhino model units
            # grid lines
            for j in range(-5, 6):
                i = j / 5
                p0 = pln.PointAt(i * r, -r)
                p1 = pln.PointAt(i * r, r)
                self.draw_line.append((p0, p1, col, 1))
                p0 = pln.PointAt(-r, i * r)
                p1 = pln.PointAt(r, i * r)
                self.draw_line.append((p0, p1, col, 1))
            # axes
            self.draw_line.append((pln.Origin, pln.Origin + pln.XAxis * r, col, 3))
            self.draw_line.append((pln.Origin, pln.Origin + pln.YAxis * r, col, 3))

    def translate_context_geometry(self, dis_obj):
        """Translate a display geometry object into arguments for drawing in the scene.

        Args:
            dis_obj: The Ladybug Display geometry object to be translated.
        """
        # first translate the color and get the geometry object
        col = color_to_color(dis_obj.color)
        geo_obj = dis_obj.geometry

        if isinstance(geo_obj, (Point3D, Point2D)):
            # translate display point
            pt = from_point3d(geo_obj) if isinstance(geo_obj, Point3D) \
                else from_point2d(geo_obj)
            radius = 3 if isinstance(dis_obj.radius, Default) else int(dis_obj.radius)
            self.draw_point.append((pt, rd.PointStyle.RoundSimple, radius, col))

        elif isinstance(geo_obj, (LineSegment3D, LineSegment2D)):
            # translate display line segment
            if isinstance(geo_obj, LineSegment3D):
                pt1, pt2 = from_point3d(geo_obj.p1), from_point3d(geo_obj.p2)
            else:
                pt1, pt2 = from_point2d(geo_obj.p1), from_point2d(geo_obj.p2)
            lw = 1 if isinstance(dis_obj.line_width, Default) \
                else int(dis_obj.line_width)
            if dis_obj.line_type == 'Continuous':
                self.draw_line.append((pt1, pt2, col, lw))
            else:
                self.draw_patterned_line.append(
                    (pt1, pt2, col, self.LINE_TYPE[dis_obj.line_type], lw))

        elif isinstance(geo_obj, (Polyline3D, Polyline2D)):
            # translate display polyline
            lw = 1 if isinstance(dis_obj.line_width, Default) \
                else int(dis_obj.line_width)
            if dis_obj.line_type == 'Continuous':
                crv = from_polyline3d(geo_obj) if isinstance(geo_obj, Polyline3D) \
                    else from_polyline2d(geo_obj)
                self.draw_curve.append((crv, col, lw))
            else:  # ensure the line pattern is respected
                verts = [from_point3d(pt) for pt in geo_obj.vertices] \
                    if isinstance(geo_obj, Polyline3D) else \
                    [from_point2d(pt) for pt in geo_obj.vertices]
                self.draw_patterned_polyline.append(
                    (verts, col, self.LINE_TYPE[dis_obj.line_type], lw, False))

        elif isinstance(geo_obj, (Ray2D, Ray3D)):
            # translate display rays
            rh_ray = from_ray3d(geo_obj) if isinstance(geo_obj, Ray3D) \
                else from_ray2d(geo_obj)
            rh_obj = rg.Line(rh_ray.Position, rh_ray.Direction)
            self.draw_arrow.append((rh_obj, col))

        elif isinstance(geo_obj, (Face3D, Polyface3D)):
            # translate display Face3D and Polyface3D
            if dis_obj.display_mode in ('Surface', 'SurfaceWithEdges'):
                mat = rd.DisplayMaterial(col, 1 - (dis_obj.color.a / 255))
                rh_obj = from_face3d(geo_obj) if isinstance(geo_obj, Face3D) \
                    else from_polyface3d(geo_obj)
                self.draw_brep_shaded.append((rh_obj, mat))
                if dis_obj.display_mode == 'SurfaceWithEdges':
                    self.draw_brep_wires.append((rh_obj, black(), -1))
            elif dis_obj.display_mode == 'Wireframe':
                rh_obj = from_face3d(geo_obj) if isinstance(geo_obj, Face3D) \
                    else from_polyface3d(geo_obj)
                self.draw_brep_wires.append((rh_obj, col, 1))
            elif dis_obj.display_mode == 'Points':
                for pt in geo_obj.vertices:
                    self.draw_point.append(
                        (from_point3d(pt), rd.PointStyle.RoundSimple, 3, col))

        elif isinstance(geo_obj, (Mesh3D, Mesh2D)):
            # translate display mesh
            rh_obj = from_mesh3d(geo_obj) if isinstance(geo_obj, Mesh3D) \
                else from_mesh2d(geo_obj)
            if dis_obj.display_mode in ('Surface', 'SurfaceWithEdges'):
                mat = rd.DisplayMaterial(col, 1 - (dis_obj.color.a / 255))
                t_color = argb_color_to_color(dis_obj.color)
                rh_obj.VertexColors.CreateMonotoneMesh(t_color)
                self.draw_mesh_shaded.append((rh_obj, mat))
                if dis_obj.display_mode == 'SurfaceWithEdges':
                    self.draw_mesh_wires.append((rh_obj, black(), 1))
            elif dis_obj.display_mode == 'Wireframe':
                self.draw_mesh_wires.append((rh_obj, col, 1))
            elif dis_obj.display_mode == 'Points':
                self.draw_mesh_vertices.append((rh_obj, col))

        elif isinstance(geo_obj, Sphere):
            # translate analysis sphere
            if dis_obj.display_mode in ('Surface', 'SurfaceWithEdges'):
                rh_obj = from_sphere(geo_obj)
                mat = rd.DisplayMaterial(col, 1 - (dis_obj.color.a / 255))
                self.draw_brep_shaded.append((rh_obj.ToBrep(), mat))
                if dis_obj.display_mode == 'SurfaceWithEdges':
                    self.draw_sphere.append((rh_obj, black()))
            elif dis_obj.display_mode == 'Wireframe':
                self.draw_sphere.append((from_sphere(geo_obj), col))
            elif dis_obj.display_mode == 'Points':
                pt_arg = (from_point3d(geo_obj.center),
                          rd.PointStyle.RoundSimple, 3, col)
                self.draw_point.append(pt_arg)

        elif isinstance(geo_obj, Polygon2D):
            # translate display polygon
            lw = 1 if isinstance(dis_obj.line_width, Default) \
                else int(dis_obj.line_width)
            if dis_obj.line_type == 'Continuous':
                self.draw_curve.append((from_polygon2d(geo_obj), col, lw))
            else:  # ensure the line pattern is respected
                verts = [from_point2d(pt) for pt in geo_obj.vertices]
                self.draw_patterned_polyline.append(
                    (verts, col, self.LINE_TYPE[dis_obj.line_type], lw, True))

        elif isinstance(geo_obj, (Arc3D, Arc2D)):
            # translate display arc
            lw = 1 if isinstance(dis_obj.line_width, Default) \
                else int(dis_obj.line_width)
            if dis_obj.line_type == 'Continuous':
                crv = from_arc3d(geo_obj) if isinstance(geo_obj, Arc3D) else \
                    from_arc2d(geo_obj)
                if geo_obj.is_circle:
                    self.draw_circle.append((crv, col, lw))
                else:
                    self.draw_arc.append((crv, col, lw))
            else:  # ensure the line pattern is respected
                p_line = geo_obj.to_polyline(
                    int(abs(geo_obj.a2 - geo_obj.a1) / 0.0523599))
                if geo_obj.is_circle:
                    arc_verts, closed = p_line.vertices[:-1], True
                else:
                    arc_verts, closed = p_line.vertices, False
                verts = [from_point3d(pt) for pt in arc_verts] \
                    if isinstance(p_line, Polyline3D) else \
                    [from_point2d(pt) for pt in arc_verts]
                self.draw_patterned_polyline.append(
                    (verts, col, self.LINE_TYPE[dis_obj.line_type], lw, closed))

        elif isinstance(geo_obj, Cone):
            # translate analysis cone
            if dis_obj.display_mode in ('Surface', 'SurfaceWithEdges'):
                rh_obj = from_cone(geo_obj)
                mat = rd.DisplayMaterial(col, 1 - (dis_obj.color.a / 255))
                self.draw_brep_shaded.append((rh_obj.ToBrep(True), mat))
                if dis_obj.display_mode == 'SurfaceWithEdges':
                    self.draw_cone.append((rh_obj, black()))
            elif dis_obj.display_mode == 'Wireframe':
                self.draw_cone.append((from_cone(geo_obj), col))
            elif dis_obj.display_mode == 'Points':
                pt_arg = (from_point3d(geo_obj.vertex),
                          rd.PointStyle.RoundSimple, 3, col)
                self.draw_point.append(pt_arg)

        elif isinstance(geo_obj, Cylinder):
            # translate analysis cylinder
            if dis_obj.display_mode in ('Surface', 'SurfaceWithEdges'):
                rh_obj = from_cylinder(geo_obj)
                mat = rd.DisplayMaterial(col, 1 - (dis_obj.color.a / 255))
                self.draw_brep_shaded.append((rh_obj.ToBrep(True, True), mat))
                if dis_obj.display_mode == 'SurfaceWithEdges':
                    self.draw_cylinder.append((rh_obj, black()))
            elif dis_obj.display_mode == 'Wireframe':
                self.draw_cylinder.append((from_cylinder(geo_obj), col))
            elif dis_obj.display_mode == 'Points':
                pt_arg = (from_point3d(geo_obj.center),
                          rd.PointStyle.RoundSimple, 3, col)
                self.draw_point.append(pt_arg)

        elif isinstance(geo_obj, Plane):
            # translate analysis planes
            pln = from_plane(geo_obj)
            r = 10  # default radius for a plane object in rhino model units
            # grid lines
            if dis_obj.show_grid:
                for j in range(-5, 6):
                    i = j / 5
                    p0 = pln.PointAt(i * r, -r)
                    p1 = pln.PointAt(i * r, r)
                    self.draw_line.append((p0, p1, col, 1))
                    p0 = pln.PointAt(-r, i * r)
                    p1 = pln.PointAt(r, i * r)
                    self.draw_line.append((p0, p1, col, 1))
            # axes
            if dis_obj.show_axes:
                self.draw_line.append((pln.Origin, pln.Origin + pln.XAxis * r, col, 3))
                self.draw_line.append((pln.Origin, pln.Origin + pln.YAxis * r, col, 3))

    def sort_shaded_objects(self):
        """Sort shaded objects according to their transparency.

        This ensures that the resulting display has visible objects behind
        any transparent objects.
        """
        if len(self.draw_brep_shaded) != 0:
            trans = (args[1].Transparency for args in self.draw_brep_shaded)
            self.draw_brep_shaded = \
                [a for _, a in sorted(zip(trans, self.draw_brep_shaded))]
        if len(self.draw_mesh_shaded) != 0:
            trans = (args[1].Transparency for args in self.draw_mesh_shaded)
            self.draw_mesh_shaded = \
                [a for _, a in sorted(zip(trans, self.draw_mesh_shaded))]

    @staticmethod
    def convert_legend2d(legend, vw=None, vh=None):
        """Convert a ladybug Legend into arguments for drawing in 2D on the screen.

        Args:
            legend: A Ladybug Legend object to be converted to 2D screen-oriented
                geometry.
            vw: An integer for the view width in pixels. If None, it will
                be obtained from the active viewport. (Default: None).
            vh: An integer for the view height in pixels. If None, it will
                be obtained from the active viewport. (Default: None).

        Returns:
            A tuple with two values needed to render the legend in the 2D scene:

            -   legend_mesh -- A colored mesh for the legend.

            -   legend_title -- A text object for the legend title.
        """
        # figure out the dimensions of the active viewport
        if vw is None or vh is None:
            active_view = sc.doc.Views.ActiveView.ActiveViewport
            v_size = active_view.Size
            vw = v_size.Width if vw is None else vw
            vh = v_size.Height if vh is None else vh

        # translate the color matrix to a bitmap
        l_par = legend.legend_parameters
        color_mtx = legend.color_map_2d(vw, vh)
        color_mtx = [[color_to_color(c) for c in row] for row in color_mtx]
        net_bm = System.Drawing.Bitmap(len(color_mtx[0]), len(color_mtx))
        for y, row in enumerate(color_mtx):
            for x, col in enumerate(row):
                net_bm.SetPixel(x, y, col)
        rh_bm = rd.DisplayBitmap(net_bm)
        or_x, or_y, sh, sw, th = legend._pixel_dims_2d(vw, vh)
        s_count = l_par.segment_count
        s_count = s_count - 1 if l_par.continuous_legend else s_count
        leg_width = sw if l_par.vertical else sw * s_count
        leg_height = sh if not l_par.vertical else sh * s_count
        cent_pt = rg.Point2d(or_x + (leg_width / 2), or_y + (leg_height / 2))
        draw_sprite = (rh_bm, cent_pt, leg_width, leg_height)

        # translate the legend text
        _height = legend.parse_dim_2d(l_par.text_height_2d, vh)
        _font = l_par.font
        txt_pts = legend.segment_text_location_2d(vw, vh)
        cent_txt = False if l_par.vertical else True
        draw_2d_text = [
            (txt, black(), rg.Point2d(loc.x, loc.y), cent_txt, _height, _font)
            for txt, loc in zip(legend.segment_text, txt_pts)]
        t_pt = legend.title_location_2d(vw, vh)
        legend_title = (legend.title, black(), rg.Point2d(t_pt.x, t_pt.y),
                        False, _height, _font)
        draw_2d_text.insert(0, legend_title)

        return draw_sprite, draw_2d_text

    def ToString(self):
        """Overwrite .NET ToString method."""
        return 'VisualizationSet Converter'


class RhinoPointConduit(rd.DisplayConduit):
    """An optimized class to preview Rhino Point3d in the Rhino Display pipeline.
    
    Args:
        points: A list of Rhino Point3d to be displayed in the pipeline.
    """

    def __init__(self, points):
        """Initialize RhinoPointConduit."""
        self.draw_point_args = []
        col = black()
        for pt in points:
            self.draw_point_args.append((pt, rd.PointStyle.RoundSimple, 5, col))
        self.bbox = rg.BoundingBox(points)

    def CalculateBoundingBox(self, calculateBoundingBoxEventArgs):
        """Overwrite the method that passes the bounding box to the display."""
        calculateBoundingBoxEventArgs.IncludeBoundingBox(self.bbox)

    def PostDrawObjects(self, drawEventArgs):
        """Overwrite the method that draws the objects in the display."""
        # get the DisplayPipeline from the event arguments
        display = drawEventArgs.Display

        # for each object to be rendered, pass the drawing arguments
        for draw_args in self.draw_point_args:
            display.DrawPoint(*draw_args)
