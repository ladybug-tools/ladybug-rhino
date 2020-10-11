"""Functions for getting viewport properties, creating new viewports, and editing them."""
import math

try:
    import System
except ImportError as e:  # No .NET; We are really screwed
    raise ImportError("Failed to import System.\n{}".format(e))

try:
    import Rhino.Geometry as rg
    import Rhino.Display as rd
    import Rhino.RhinoDoc as rhdoc
except ImportError as e:  # No RhinoCommon doc is available. This module is useless.
    raise ImportError("Failed to import Rhino.\n{}".format(e))

try:
    import scriptcontext as sc
except ImportError as e:  # No Rhino doc is available. This module is useless.
    raise ImportError("Failed to import Rhino scriptcontext.\n{}".format(e))

from .text import TextGoo


def camera_oriented_plane(origin):
    """Get a Rhino Plane that is oriented facing the camera.

    Args:
        origin: A Rhino Point for the origin of the plane.
    """
    active_view = sc.doc.Views.ActiveView.ActiveViewport
    camera_x = active_view.CameraX
    camera_y = active_view.CameraY
    return rg.Plane(origin, camera_x, camera_y)


def orient_to_camera(geometry, position=None):
    """Orient an array of Rhino geometry objects to the camera of the active viewport.

    Args:
        geometry: An array of Rhino Geometry objects (or TextGoo objects) to
            the camera of the active Rhino viewport.
        position: A point to be used as the origin around which the the geometry
            will be oriented. If None, the lower left corner of the bounding box
            around the geometry will be used.
    """
    # set the default position if it is None
    origin = _bounding_box_origin(geometry)
    pt = origin if position is None else position

    # get a plane oriented to the camera
    oriented_plane = camera_oriented_plane(pt)

    # orient the input geometry to the plane facing the camera
    base_plane = rg.Plane(origin, rg.Vector3d(0, 0, 1))
    xform = rg.Transform.PlaneToPlane(base_plane, oriented_plane)
    geo = []
    for rh_geo in geometry:
        if isinstance(rh_geo, TextGoo):
            geo.append(rh_geo.Transform(xform))
        else:
            new_geo = rh_geo.Duplicate()
            new_geo.Transform(xform)
            geo.append(new_geo)
    return geo


def viewport_by_name(view_name=None):
    """Get a Rhino Viewport object using the name of the viewport.

    Args:
        view_name: Text for the name of the Rhino Viewport. If None, the
            current Rhino viewport will be used.
    """
    try:
        return sc.doc.Views.Find(view_name, False).ActiveViewport \
            if view_name is not None else sc.doc.Views.ActiveView.ActiveViewport
    except Exception:
        raise ValueError('Viewport "{}" was not found in the Rhino '
                         'document.'.format(view_name))


def open_viewport(view_name, width=None, height=None):
    """Create a new Viewport in the active Rhino document at specified dimensions.

    This will also set the newly-created view to be tha active Viewport.

    Args:
        view_name: Text for the name of the new Rhino Viewport that will be created.
        width: Optional positive integer for the width of the view in pixels. If None,
            the width of the currently active viewport will be used.
        height: Optional positive integer for the height of the view in pixels. If
            None, the height of the currently active viewport will be used.
    """
    # close the view if it already exists
    if sc.doc.Views.Find(view_name, False):
        sc.doc.Views.Find(view_name, False).Close()

    # get the width and the height if it was not specified
    w = sc.doc.Views.ActiveView.ActiveViewport.Size.Width if not width else width
    h = sc.doc.Views.ActiveView.ActiveViewport.Size.Height if not height else height

    # compute the X,Y screen coordinates where the new viewport will be placed
    x = round((System.Windows.Forms.Screen.PrimaryScreen.Bounds.Width - w) / 2)
    y = round((System.Windows.Forms.Screen.PrimaryScreen.Bounds.Height - h) / 2)
    rec = System.Drawing.Rectangle(System.Drawing.Point(x, y), System.Drawing.Size(w, h))

    # add the new view to the rhino document
    rhdoc.ActiveDoc.Views.Add(
        view_name, rd.DefinedViewportProjection.Perspective, rec, True)
    return viewport_by_name(view_name)


def set_view_display_mode(viewport, display_mode):
    """Set the display mode of a Rhino Viewport.

    Args:
        viewport: A Rhino ViewPort object, which will have its display mode set.
        display_mode: Text for the display mode to which the Rhino viewport will be
            set. For example: Wireframe, Shaded, Rendered, etc.
    """
    mode_obj = rd.DisplayModeDescription.FindByName(display_mode)
    viewport.DisplayMode = mode_obj


def set_iso_view_direction(viewport, direction, center_point=None):
    """Set a Rhino Viewport to have an isometric view in a specific direction.

    Args:
        viewport: A Rhino ViewPort object, which will have its direction set.
        direction: A Rhino vector that will be used to set the direction of
            the isomateric view.
        center_point: Optional Rhino point for the target of the camera. If no point
            is provided, the Rhino origin will be used (0, 0, 0).
    """
    viewport.ChangeToParallelProjection(True)
    center_point = center_point if center_point is not None else rg.Point3d.Origin
    viewport.SetCameraLocation(rg.Point3d.Add(center_point, direction), False)
    viewport.SetCameraTarget(center_point, False)
    viewport.SetCameraDirection(direction, False)


def viewport_vh_vv(viewport, view_type):
    """Get the horizontal angle (vh) and the vertical angle (vv) from a viewport.

    Args:
        viewport: A Rhino ViewPort object for which properties will be extracted.
        view_type: An integer to set the view type (-vt). Choose from the
            choices below.

            * 0 Perspective (v)
            * 1 Hemispherical fisheye (h)
            * 2 Parallel (l)
            * 3 Cylindrical panorama (c)
            * 4 Angular fisheye (a)
            * 5 Planisphere [stereographic] projection (s)
    """
    if view_type == 0:  # perspective
        right_vec = viewport.GetFrustumRightPlane()[1][1]
        left_vec = viewport.GetFrustumLeftPlane()[1][1]
        h_angle = 180 - math.degrees(rg.Vector3d.VectorAngle(right_vec, left_vec))
        bottom_vec = viewport.GetFrustumBottomPlane()[1][1]
        top_vec = viewport.GetFrustumTopPlane()[1][1]
        v_angle = 180 - math.degrees(rg.Vector3d.VectorAngle(bottom_vec, top_vec))
        return h_angle, v_angle
    if view_type == 1 or view_type == 5:
        return 180, 180
    if view_type == 2:
        v_rect = viewport.GetNearRect()
        return int(v_rect[0].DistanceTo(v_rect[1])), int(v_rect[0].DistanceTo(v_rect[2]))
    if view_type == 3:
        return 360, 180
    if view_type == 4:
        return 60, 60


def viewport_properties(viewport, view_type=None):
    """Get a dictionary of properties of a Rhino viewport.

    Args:
        viewport: A Rhino ViewPort object for which properties will be extracted.
        view_type: An integer to set the view type (-vt). Choose from the
            choices below or set to None to have it derived from the viewport.

            * 0 Perspective (v)
            * 1 Hemispherical fisheye (h)
            * 2 Parallel (l)
            * 3 Cylindrical panorama (c)
            * 4 Angular fisheye (a)
            * 5 Planisphere [stereographic] projection (s)

    Returns:
        A dictionary with the following keys: 'view_type', 'position', 'direction',
        'up_vector', 'h_angle', 'v_angle'
    """
    # ensure that we have an integer for the view_type
    if view_type is None:
        view_type = 2 if viewport.IsParallelProjection else 0

    # get the position, direction and up vectors
    pos = viewport.CameraLocation
    direct = viewport.CameraDirection
    up_vec = viewport.CameraUp
    direct.Unitize()
    up_vec.Unitize()

    # get the h_angle and v_angle from the viewport
    h_angle, v_angle = viewport_vh_vv(viewport, view_type)

    return {
        'view_type': view_type,
        'position': (pos.X, pos.Y, pos.Z),
        'direction': (direct.X, direct.Y, direct.Z),
        'up_vector': (up_vec.X, up_vec.Y, up_vec.Z),
        'h_angle': h_angle,
        'v_angle': v_angle
    }


def _bounding_box_origin(geometry):
    """Get the origin of a bounding box around a list of geometry.

    Args:
        geometry: A list of geometry for which the bounding box origin will
            be computed.
    """
    first_geo = geometry[0]
    b_box = first_geo.GetBoundingBox(False) if not isinstance(first_geo, TextGoo) \
        else first_geo.get_Boundingbox()
    for geo in geometry[1:]:
        if isinstance(geo, TextGoo):
            b_box = rg.BoundingBox.Union(b_box, geo.get_Boundingbox())
        else:
            b_box = rg.BoundingBox.Union(b_box, geo.GetBoundingBox(False))
    return b_box.Corner(True, True, True)
