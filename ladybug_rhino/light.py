"""Functions for setting lights within the Rhino scene."""
from __future__ import division

from ladybug.dt import DateTime
from ladybug.sunpath import Sunpath

try:
    import System
except ImportError as e:  # No .NET; We are really screwed
    raise ImportError("Failed to import System.\n{}".format(e))

try:
    import Rhino.Geometry as rg
    import Rhino.Render.Sun as sun
    from Rhino import RhinoDoc as rhdoc
except ImportError as e:
    raise ImportError("Failed to import Rhino document attributes.\n{}".format(e))


def set_sun(location, hoy, north=0):
    """Set the sun in the Rhino scene to correspond to a given location and DateTime.

    The resulting sun objects will have color rendering that mimics the sun at
    the particular hoy specified.

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
    doc = rhdoc.ActiveDoc
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


def set_suns(location, hoys, north=0):
    """Setup multiple light objects for several sun positions.

    Note that the resulting lights will not have any color rendering associated
    with them and all lights will be white.

    Args:
        location: A Ladybug Location object to set the latitude, longitude and
            time zone of the Rhino sun path.
        hoys: A list of numbers between 0 and 8760 that represent the hours of
            the year at which to evaluate the sun position. Note that this does
            not need to be an integer and decimal values can be used to specify
            date times that are not on the hour mark.
        north: A number between -360 and 360 for the counterclockwise
            difference between the North and the positive Y-axis in degrees.
            90 is West and 270 is East. (Default: 0).

    Returns:
        An array of lights representing sun positions.
    """
    doc_lights = rhdoc.ActiveDoc.Lights

    # initialize the Sunpath and get the relevant LB Suns
    sp = Sunpath.from_location(location, north)
    sun_vecs = []
    for hoy in hoys:
        lb_sun = sp.calculate_sun_from_hoy(hoy)
        if lb_sun.is_during_day:
            sun_vecs.append(lb_sun.sun_vector)
    
    # create Rhino Light objects for each sun
    sli = (1 / len(sun_vecs)) * 1.75
    sun_lights = []
    for sun_vec in sun_vecs:
        sun_light = rg.Light()
        sun_light.LightStyle = rg.LightStyle(7)
        sun_light.Direction = rg.Vector3d(sun_vec.x, sun_vec.y, sun_vec.z)
        sun_light.Intensity = sli
        sun_light.Name = 'LB_Sun'
        doc_lights.Add(sun_light)
        sun_lights.append(sun_light)

    return sun_lights


def disable_sun():
    """Disable all suns in the Rhino scene so it does not interfere with other lights."""
    doc_lights = rhdoc.ActiveDoc.Lights
    doc_lights.Sun.Enabled = False
    for i, light in enumerate(doc_lights):
        if light.Name =='LB_Sun':
            doc_lights.Delete(i, True)
