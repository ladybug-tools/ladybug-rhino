"""Ladybug_rhino configurations.
Global variables such as tolerances and units are stored here.
"""

try:  # Try to import tolerance from the active Rhino document
    import scriptcontext
    tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    angle_tolerance = scriptcontext.doc.ModelAngleToleranceDegrees
except ImportError:  # No Rhino doc is available. Use Rhino's default.
    tolerance = 0.01
    angle_tolerance = 1.0  # default is 1 degree
    print('Failed to import Rhino scriptcontext. Default tolerance of {} '
          'and angle tolerance of {} degrees will be used.'.format(
              tolerance, angle_tolerance))


def conversion_to_meters():
    """Get the conversion factor to meters based on the current Rhino doc units system.

    Returns:
        A number for the conversion factor, which should be multiplied by all distance
        units taken from Rhino geometry in order to convert them to meters.
    """
    try:  # Try to import units from the active Rhino document
        import scriptcontext
        units = str(scriptcontext.doc.ModelUnitSystem).split('.')[-1]
    except ImportError:  # No Rhino doc available. Default to the greatest of all units
        units = 'Meters'

    if units == 'Meters':
        return 1.0
    elif units == 'Millimeters':
        return 0.001
    elif units == 'Feet':
        return 0.305
    elif units == 'Inches':
        return 0.0254
    elif units == 'Centimeters':
        return 0.01
    else:
        raise ValueError(
            "You're kidding me! What units are you using?" + units + "?\n"
            "Please use Meters, Millimeters, Centimeters, Feet or Inches.")


def units_system():
    """Get text for the current Rhino doc units system. (eg. 'Meters', 'Feet')"""
    try:  # Try to import units from the active Rhino document
        import scriptcontext
        return str(scriptcontext.doc.ModelUnitSystem).split('.')[-1]
    except ImportError:  # No Rhino doc available. Default to the greatest of all units
        return 'Meters'


def units_abbreviation():
    """Get text for the current Rhino doc units abbreviation (eg. 'm', 'ft')"""
    try:  # Try to import units from the active Rhino document
        import scriptcontext
        units = str(scriptcontext.doc.ModelUnitSystem).split('.')[-1]
    except ImportError:  # No Rhino doc available. Default to the greatest of all units
        units = 'Meters'

    if units == 'Meters':
        return 'm'
    elif units == 'Millimeters':
        return 'mm'
    elif units == 'Feet':
        return 'ft'
    elif units == 'Inches':
        return 'in'
    elif units == 'Centimeters':
        return 'cm'
    else:
        raise ValueError(
            "You're kidding me! What units are you using?" + units + "?\n"
            "Please use Meters, Millimeters, Centimeters, Feet or Inches.")
