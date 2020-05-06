"""Functions for getting viewport properties, creating new viewports, and editing them."""

try:
    import Rhino.Geometry as rg
    import Rhino.Display as rd
except ImportError as e:
    raise ImportError("Failed to import Rhino.\n{}".format(e))

try:  # Try to import tolerance from the active Rhino document
    import scriptcontext as sc
except ImportError:  # No Rhino doc is available. Use Rhino's default.
    raise ImportError("Failed to import Rhino scriptcontext.\n{}".format(e))


def camera_oriented_plane(origin):
    """Get a Rhino Plane that is oriented facing the camera.

    Args:
        origin: A Rhino Point for the origin of the plane.
    """
    camera_x = sc.doc.Views.ActiveView.ActiveViewport.CameraX
    camera_y = sc.doc.Views.ActiveView.ActiveViewport.CameraY
    return rg.Plane(origin, camera_x, camera_y)
