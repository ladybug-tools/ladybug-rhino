"""Ladybug_rhino configurations.
Global variables such as tolerances are stored here.
"""

try:  # try to import tolerance from the active Rhino document
    import scriptcontext
    tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    angle_tolerance = scriptcontext.doc.ModelAngleToleranceRadians
except ImportError:  # no Rhino doc is available. Default to Rhino' default.
    tolerance = 0.01
    angle_tolerance = 0.01745  # default is 1 degree
    print('Failed to import Rhino scriptcontext. Default tolerance of {} '
          'and angle tolerance of {} will be used.'.format(tolerance, angle_tolerance))
