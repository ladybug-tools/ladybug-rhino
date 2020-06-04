"""Functions for getting viewport properties, creating new viewports, and editing them."""
import math

try:
    import Rhino.Geometry as rg
except ImportError as e:
    raise ImportError("Failed to import Rhino.\n{}".format(e))

try:  # Try to import tolerance from the active Rhino document
    import scriptcontext as sc
except ImportError as e:  # No Rhino doc is available. This module is useless.
    raise ImportError("Failed to import Rhino scriptcontext.\n{}".format(e))


def camera_oriented_plane(origin):
    """Get a Rhino Plane that is oriented facing the camera.

    Args:
        origin: A Rhino Point for the origin of the plane.
    """
    active_view = sc.doc.Views.ActiveView.ActiveViewport
    camera_x = active_view.CameraX
    camera_y = active_view.CameraY
    return rg.Plane(origin, camera_x, camera_y)


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
