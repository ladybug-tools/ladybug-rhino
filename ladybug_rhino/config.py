"""Ladybug_rhino configurations.

Global variables such as tolerances, units and Rhino versions are stored here.
"""
import os

try:
    from ladybug.config import folders as lb_folders
except ImportError as e:
    raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))

try:
    import Rhino
    rhino_version_str = str(Rhino.RhinoApp.Version)
    rhino_version = tuple(int(n) for n in rhino_version_str.split('.'))
except Exception:  # Rhino is unavailable; just use a placeholder
    rhino_version = (7, 0)

try:  # Try to import tolerance from the active Rhino document
    import scriptcontext
    tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    angle_tolerance = scriptcontext.doc.ModelAngleToleranceDegrees
except ImportError:  # No Rhino doc is available. Use Rhino's default.
    tolerance = 0.01
    angle_tolerance = 1.0  # default is 1 degree


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


class Folders(object):
    """Ladybug-rhino folders.

    Properties:
        * uo_folder
        * gha_folder
        * lbt_grasshopper_version
        * lbt_grasshopper_version_str
    """

    def __init__(self):
        # find the location where the Grasshopper user objects are stored
        app_folder = os.getenv('APPDATA')
        if app_folder is not None:
            self._uo_folder = os.path.join(app_folder, 'Grasshopper', 'UserObjects')
            self._gha_folder = os.path.join(app_folder, 'Grasshopper', 'Libraries')
        else:
            home_folder = os.getenv('HOME') or os.path.expanduser('~')
            gh_folder = os.path.join(home_folder, 'AppData', 'Roaming', 'Grasshopper')
            self._uo_folder = os.path.join(gh_folder, 'UserObjects')
            self._gha_folder = os.path.join(gh_folder, 'Libraries')
        if os.name == 'nt':
            # test to see if components live in the core installation
            lbt_components = os.path.join(lb_folders.ladybug_tools_folder, 'grasshopper')
            if os.path.isdir(lbt_components):
                user_dir = os.path.join(self._uo_folder, 'ladybug_grasshopper')
                if not os.path.isdir(user_dir):
                    self._uo_folder = lbt_components
                    self._gha_folder = lbt_components
        self._lbt_grasshopper_version = None
        self._lbt_grasshopper_version_str = None

    @property
    def uo_folder(self):
        """Get the path to the user object folder."""
        return self._uo_folder

    @property
    def gha_folder(self):
        """Get the path to the GHA Grasshopper component folder."""
        return self._gha_folder

    @property
    def lbt_grasshopper_version(self):
        """Get a tuple for the version of lbt-grasshopper (eg. (3, 8, 2)).

        This will be None if the version could not be sensed.
        """
        if self._lbt_grasshopper_version is None:
            self._lbt_grasshopper_version_from_txt()
        return self._lbt_grasshopper_version

    @property
    def lbt_grasshopper_version_str(self):
        """Get text for the full version of python (eg."3.8.2").

        This will be None if the version could not be sensed.
        """
        if self._lbt_grasshopper_version_str is None:
            self._lbt_grasshopper_version_from_txt()
        return self._lbt_grasshopper_version_str

    def _lbt_grasshopper_version_from_txt(self):
        """Get the LBT-Grasshopper version from the requirements.txt file in uo_folder.
        """
        req_file = os.path.join(self._uo_folder, 'requirements.txt')
        if os.path.isfile(req_file):
            with open(req_file) as rf:
                for row in rf:
                    if row.startswith('lbt-grasshopper=='):
                        lbt_ver = row.split('==')[-1].strip()
                        try:
                            self._lbt_grasshopper_version = \
                                tuple(int(i) for i in lbt_ver.split('.'))
                            self._lbt_grasshopper_version_str = lbt_ver
                        except Exception:
                            pass  # failed to parse the version into values
                        break


"""Object possessing all key folders within the configuration."""
folders = Folders()
