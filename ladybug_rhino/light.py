"""Functions for setting lights within the Rhino scene."""
from ladybug.location import Location
from ladybug.dt import DateTime

try:
    import System
except ImportError as e:  # No .NET; We are really screwed
    raise ImportError("Failed to import System.\n{}".format(e))

try:
    import Rhino.Render.Sun as sun
    import Rhino.RhinoDoc as rhdoc
    doc = rhdoc.ActiveDoc
except ImportError as e:
    raise ImportError("Failed to import Rhino document attributes.\n{}".format(e))


def set_sun(location, hoy, north=0):
    """Set the sun in the Rhino scene to correspond to a given location and DateTime.

    Args:
        location: A Ladybug Location object to set the latitude, longitude and
            time zone of the Rhino sun path.
        hoy: A number between 0 and 8760 that represent the hour of the year at
            which to evaluate the sun position. Note that this does not need to
            be an integer and decimal values can be used to specify date times
            that are not on the hour mark.
        north: A number between -360 and 360 for the counterclockwise
            difference between the North and the positive Y-axis in degrees.
            90 is West and 270 is East. (Default: 0).

    Returns:
        The Rhino sun object.
    """
    # process the hoy into a .NET date/time
    lb_dt = DateTime.from_hoy(hoy)
    rh_dt = System.DateTime(
        lb_dt.year, lb_dt.month, lb_dt.day, lb_dt.hour, lb_dt.minute, 0)

    # enable the sun and set its position based on the location and date/time
    sun_position = doc.Lights.Sun
    sun.Enabled.SetValue(sun_position, True)
    sun.TimeZone.SetValue(sun_position, location.time_zone)
    sun.SetPosition(sun_position, rh_dt, location.latitude, location.longitude)

    # set the north of the sun, ensuring the the y-axis is North
    sun.North.SetValue(sun_position, 90 + north)
    return sun


def disable_sun():
    """Disable the sun in the Rhino scene so it does not interfere with other lights."""
    doc.Lights.Sun.Enabled = False
