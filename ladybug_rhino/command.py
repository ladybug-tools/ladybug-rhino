"""Functions for dealing assisting with Rhino plugin commands."""
from __future__ import division
import os
import sys
import json

try:
    import clr
    import System
except ImportError as e:  # No .NET being used
    print('Failed to import CLR. Cannot access Pollination DLLs.\n{}'.format(e))

try:
    import Rhino
except ImportError as e:
    raise ImportError("Failed to import Rhino.\n{}".format(e))

try:
    import scriptcontext as sc
except ImportError:  # No Rhino doc is available.
    print('Failed to import Rhino scriptcontext. Unable to access sticky.')

try:
    from ladybug_geometry.geometry3d import Mesh3D
    from ladybug.futil import unzip_file
    from ladybug.config import folders
    from ladybug.ddy import DDY
    from ladybug.wea import Wea
    from ladybug.epw import EPW
    from ladybug.stat import STAT
    from ladybug_display.visualization import AnalysisGeometry
except ImportError as e:
    raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))

from .config import rhino_version, conversion_to_meters
from .download import download_file
from .fromgeometry import from_mesh3d
from .bakegeometry import _get_attributes
from .bakeobjects import bake_analysis, bake_context


def _pollination_rhino_dll_dir():
    """Get the directory in which the DLLs are installed."""
    install_dir = os.path.dirname(folders.ladybug_tools_folder)
    rh_ver = str(rhino_version[0]) + '.0'
    dll_dir = os.path.join(install_dir, 'pollination', 'plugin', rh_ver, 'Pollination')
    if not os.path.isdir:
        msg = 'No Pollination installation could be found for Rhino {}.'.format(rh_ver)
        print(msg)
        return None
    return dll_dir


def import_pollination_core():
    """Import Pollination.Core from the dll or give a message if it is not found."""
    try:
        import Core
    except ImportError:  # the dll has not yet been added
        # add the Pollination.Core DLL to the Common Language Runtime (CLR)
        dll_dir = _pollination_rhino_dll_dir()
        if dll_dir is None:
            return None
        pol_dll = os.path.join(dll_dir, 'Pollination.Core.dll')
        clr.AddReferenceToFileAndPath(pol_dll)
        if pol_dll not in sys.path:
            sys.path.append(pol_dll)
        import Core
    return Core


def import_ladybug_display_schema():
    """Import LadybugDisplaySchema from the dll or give a message if it is not found."""
    try:
        import LadybugDisplaySchema
    except ImportError:  # the dll has not yet been added
        # add the LadybugDisplaySchema DLL to the Common Language Runtime (CLR)
        dll_dir = _pollination_rhino_dll_dir()
        if dll_dir is None:
            return None
        pol_dll = os.path.join(dll_dir, 'LadybugDisplaySchema.dll')
        clr.AddReferenceToFileAndPath(pol_dll)
        if pol_dll not in sys.path:
            sys.path.append(pol_dll)
        import LadybugDisplaySchema
    return LadybugDisplaySchema


def import_honeybee_ui():
    """Import Honeybee.UI.Rhino from the dll or give a message if it is not found."""
    try:
        import Honeybee
    except ImportError:  # the dll has not yet been added
        # add the Honeybee.UI.Rhino DLL to the Common Language Runtime (CLR)
        dll_dir = _pollination_rhino_dll_dir()
        if dll_dir is None:
            return None
        pol_dll = os.path.join(dll_dir, 'Honeybee.UI.Rhino.dll')
        clr.AddReferenceToFileAndPath(pol_dll)
        if pol_dll not in sys.path:
            sys.path.append(pol_dll)
        import Honeybee
    return Honeybee


def is_pollination_licensed():
    """Check if the installation of Pollination has an active license."""
    Core = import_pollination_core()
    if not Core:
        return False
    # use the utility to check whether there is an active license
    is_licensed, msg = Core.Utility.CheckIfLicensed()
    if not is_licensed:
        print(msg)
    return is_licensed


def project_information():
    """Check if the installation of Pollination has an active license."""
    Core = import_pollination_core()
    if not Core:
        return None
    return Core.ModelEntity.CurrentModel.ProjectInfo


def current_units(lbt_data_type):
    """Get the currently-assigned units for a given data type."""
    Honeybee = import_honeybee_ui()
    from Honeybee.UI import Units
    unit_map = {
        'm': Units.UnitType.Length,
        'm2': Units.UnitType.Area,
        'm3': Units.UnitType.Volume,
        'C': Units.UnitType.Temperature,
        'dC': Units.UnitType.TemperatureDelta,
        'W': Units.UnitType.Power,
        'W/m2': Units.UnitType.PowerDensity,
        'kWh': Units.UnitType.Energy,
        'kWh/m2': Units.UnitType.EnergyIntensity,
        'm3/s': Units.UnitType.AirFlowRate,
        'm3/s-m2': Units.UnitType.AirFlowRateArea,
        'm/s': Units.UnitType.Speed,
        'lux': Units.UnitType.Illuminance,
        'Pa': Units.UnitType.Pressure
    }
    try:
        dot_net_units = unit_map[lbt_data_type.units[0]]
    except KeyError:  # the data type does not exist in .NET
        return lbt_data_type.units[0]
    current_settings = Units.CustomUnitSettings
    unit = Units.ToUnitsNetEnum(current_settings[dot_net_units])
    unit_str = Units.GetAbbreviation(unit)
    unit_str = _convert_unit_abbrev(unit_str)
    return unit_str if unit_str in lbt_data_type.units else lbt_data_type.units[0]


def local_processor_count():
    """Get an integer for the number of processors on this machine.

    If, for whatever reason, the number of processors could not be sensed,
    None will be returned.
    """
    return System.Environment.ProcessorCount


def recommended_processor_count():
    """Get an integer for the recommended number of processors for parallel calculation.

    This should be one less than the number of processors available on this machine
    unless the machine has only one processor, in which case 1 will be returned.
    If, for whatever reason, the number of processors could not be sensed, a value
    of 1 will be returned.
    """
    cpu_count = local_processor_count()
    return 1 if cpu_count is None or cpu_count <= 1 else cpu_count - 1


def _download_weather(weather_URL):
    """Download a weather URL with a check if it's already in the default folder."""
    _def_folder = folders.default_epw_folder
    if weather_URL.lower().endswith('.zip'):  # onebuilding URL type
        _folder_name = weather_URL.split('/')[-1][:-4]
    else:  # dept of energy URL type
        _folder_name = weather_URL.split('/')[-2]
    epw_path = os.path.join(_def_folder, _folder_name, _folder_name + '.epw')
    if not os.path.isfile(epw_path):
        zip_file_path = os.path.join(
            _def_folder, _folder_name, _folder_name + '.zip')
        download_file(weather_URL, zip_file_path, True)
        unzip_file(zip_file_path)
    return epw_path


def setup_epw_input():
    """Setup the request for an EPW input and check for any previously set EPW."""
    epw_input_request = Rhino.Input.Custom.GetString()
    epw_input_request.SetCommandPrompt('Select an EPW file path or URL')
    epw_input_request.AcceptNothing(True)
    if 'lbt_epw' in sc.sticky:
        epw_input_request.SetDefaultString(sc.sticky['lbt_epw'])
    else:  # check if the project information has an EPW associated with it
        proj_info = project_information()
        if proj_info is not None and proj_info.WeatherUrls is not None \
                and len(proj_info.WeatherUrls) > 0:
            epw_path = _download_weather(proj_info.WeatherUrls[0])
            epw_input_request.SetDefaultString(os.path.basename(epw_path))
    return epw_input_request


def retrieve_epw_input(epw_input_request, command_options, option_values):
    """Retrieve an EPW input from the command line.

    Args:
        epw_input_request: The Rhino.Input.Custom.GetString object that was used
            to setup the EPW input request.
        command_options: A list of Rhino.Input.Custom.Option objects for the
            options that were included with the EPW request. The values for these
            options will be retrieved along with the EPW.
        option_values: A list of values for each option, which will be updated
            based on the user input.

    Returns:
        The file path to the EPW as a text string.
    """
    # separate the list options from the others
    list_opt_indices = [i + 1 for i, opt in enumerate(command_options)
                        if isinstance(opt, (tuple, list))]

    # get the weather file and all options
    epw_path = None
    while True:
        # This will prompt the user to input an EPW and visualization options
        get_epw = epw_input_request.Get()
        if get_epw == Rhino.Input.GetResult.String:
            epw_path = epw_input_request.StringResult()
            for i, opt in enumerate(command_options):
                if not isinstance(opt, (tuple, list)):
                    option_values[i] = opt.CurrentValue
        elif get_epw == Rhino.Input.GetResult.Option:
            opt_ind = epw_input_request.OptionIndex()
            if opt_ind in list_opt_indices:
                option_values[opt_ind - 1] = \
                    epw_input_request.Option().CurrentListOptionIndex
            continue
        elif get_epw == Rhino.Input.GetResult.Cancel:
            return None
        break

    # process the EPW file path or URL
    if not epw_path:
        print('No EPW file was selected')
        return None
    _def_folder = folders.default_epw_folder
    if epw_path.startswith('http'):  # download the EPW file
        epw_path = _download_weather(epw_path)
        sc.sticky['lbt_epw'] = os.path.basename(epw_path)
    elif not os.path.isfile(epw_path):
        possible_file = os.path.basename(epw_path)[:-4] \
            if epw_path.lower().endswith('.epw') else epw_path
        epw_path = os.path.join(_def_folder, possible_file, possible_file + '.epw')
        if not os.path.isfile(epw_path):
            print('Selected EPW file at does not exist at: {}'.format(epw_path))
            return
        sc.sticky['lbt_epw'] = possible_file + '.epw'
    else:
        sc.sticky['lbt_epw'] = epw_path
    return epw_path


def setup_design_day_input():
    """Setup the request for a DDY, STAT, or EPW to get a design day."""
    url_input_request = Rhino.Input.Custom.GetString()
    url_input_request.SetCommandPrompt(
        'Select a weather URL or DDY/STAT/EPW file path '
        'from which a design day will be derived.')
    url_input_request.AcceptNothing(True)
    if 'lbt_url' in sc.sticky:
        url_input_request.SetDefaultString(sc.sticky['lbt_url'])
    else:  # check if the project information has an EPW associated with it
        proj_info = project_information()
        if proj_info is not None and proj_info.WeatherUrls is not None \
                and len(proj_info.WeatherUrls) > 0:
            epw_path = _download_weather(proj_info.WeatherUrls[0])
            url_input_request.SetDefaultString(
                os.path.basename(epw_path).replace('.epw', ''))
    return url_input_request


def retrieve_cooling_design_day_input(url_input_request, command_options, option_values):
    """Retrieve the best cooling design day from what is available from a URL.

    Args:
        url_input_request: The Rhino.Input.Custom.GetString object that was used
            to setup the URL input request. This input can be the file path to
            an DDY, STAT or EPW file in which case the design day is taken directly
            from the file. When a URL is used, the STAT file will first be searched
            as it typically contains values for the most accurate solar model.
            If no values are found there, the design day will be pulled from the
            DDY. If there is no clear best design day in the DDY, it will be
            derived from the EPW data.
        command_options: A list of Rhino.Input.Custom.Option objects for the
            options that were included with the URL request. The values for these
            options will be retrieved along with the design day.
        option_values: A list of values for each option, which will be updated
            based on the user input.

    Returns:
        A tuple with two values.

        -   design_day: A ladybug DesignDay object for the best cooling design
            day that was determined from the input.

        -   wea: A Wea object with annual hourly data collection of clear sky
            radiation that represents design days throughout the year.
    """
    # separate the list options from the others
    list_opt_indices = [i + 1 for i, opt in enumerate(command_options)
                        if isinstance(opt, (tuple, list))]

    # get the weather file and all options
    url_path = None
    while True:
        # This will prompt the user to input an EPW and visualization options
        get_url = url_input_request.Get()
        if get_url == Rhino.Input.GetResult.String:
            url_path = url_input_request.StringResult()
            for i, opt in enumerate(command_options):
                if not isinstance(opt, (tuple, list)):
                    option_values[i] = opt.CurrentValue
        elif get_url == Rhino.Input.GetResult.Option:
            opt_ind = url_input_request.OptionIndex()
            if opt_ind in list_opt_indices:
                option_values[opt_ind - 1] = \
                    url_input_request.Option().CurrentListOptionIndex
            continue
        elif get_url == Rhino.Input.GetResult.Cancel:
            return None, None
        break

    # process the file path or URL
    if not url_path:
        print('No URL or file was selected')
        return None, None
    epw_path, stat_path, ddy_path = None, None, None
    _def_folder = folders.default_epw_folder
    if url_path.startswith('http'):  # download the EPW file
        epw_path = _download_weather(url_path)
        stat_path = epw_path.replace('.epw', '.stat')
        ddy_path = epw_path.replace('.epw', '.ddy')
        sc.sticky['lbt_url'] = os.path.basename(epw_path.replace('.epw', ''))
    elif not os.path.isfile(url_path):
        epw_path = os.path.join(_def_folder, url_path, url_path + '.epw')
        stat_path = epw_path.replace('.epw', '.stat')
        ddy_path = epw_path.replace('.epw', '.ddy')
        if not os.path.isfile(epw_path):
            print('Selected EPW file at does not exist at: {}'.format(epw_path))
            return
        sc.sticky['lbt_url'] = url_path
    elif url_path.endswith('.ddy'):
        ddy_path = url_path
    elif url_path.endswith('.epw'):
        epw_path = url_path
    elif url_path.endswith('.stat'):
        stat_path = url_path
    else:
        return None, None

    # process the possible files into the best design day
    if stat_path is not None:
        stat_obj = STAT(stat_path)
        des_day = stat_obj.annual_cooling_design_day_004
        try:  # first see if we can get the values from monthly optical depths
            wea = Wea.from_stat_file(stat_path)
        except Exception:  # no optical data was found; use the original clear sky
            wea = Wea.from_ashrae_clear_sky(stat_obj.location)
        return des_day, wea
    if ddy_path is not None:
        ddy_obj = DDY.from_ddy_file(ddy_path)
        des_days = []
        for dday in ddy_obj:
            if '.4%' in dday.name:
                des_days.append(dday)
        if len(des_days) != 0:
            des_days.sort(key=lambda x: x.dry_bulb_condition, reverse=True)
            des_day = des_days[0]
            wea = Wea.from_ashrae_clear_sky(ddy_obj.location)
            return des_day, wea
    if epw_path is not None:
        epw_obj = EPW(epw_path)
        des_day = stat_obj.annual_cooling_design_day_004
        if des_day is None:
            des_day = epw_obj.approximate_design_day()
        wea = Wea.from_ashrae_clear_sky(epw_obj.location)
        return des_day, wea
    return None, None


def add_north_option(input_request):
    """Add a North option to an input request.

    Args:
        input_request: A Rhino Command Input such as that obtained from the
            setup_epw_input function or the Rhino.Input.Custom.GetString
            constructor.

    Returns:
        A tuple with two values.

        -   north_option: The Option object for the North input.

        -   north_value: The value of the north.
    """
    if 'lbt_north' in sc.sticky:
        north_value = sc.sticky['lbt_north']
    else:
        proj_info = project_information()
        if proj_info is not None and proj_info.North is not None:
            north_value = float(proj_info.North)
        else:
            north_value = 0
    north_option = Rhino.Input.Custom.OptionDouble(north_value, -360, 360)
    description = 'North - the counterclockwise difference between true North and the ' \
        'Y-axis in degrees (90:West, -90:East)'
    input_request.AddOptionDouble('North', north_option, description)
    return north_option, north_value


def add_month_day_hour_options(
        input_request, default_inputs=(12, 21, 0, 23), sticky_key=None):
    """Add a options for Month, Day, and Hour to an input request.

    Args:
        input_request: A Rhino Command Input such as that obtained from the
            setup_epw_input function or the Rhino.Input.Custom.GetString
            constructor.
        default_inputs: The default input month, day, start_hour and end_hour.
            A value of 0 for month or day denotes that all values of a given
            month, day and hour are used. For the start_hour and end_hour,
            the values should be between 0 and 23 where 0 denotes
            midnight. (Default: (12, 21, 0, 23)).
        sticky_key: An optional sticky key, which will be used to to pull
            previously set values from sticky. (eg. direct_sun).

    Returns:
        A tuple with two values.

        -   mdh_options: A tuple of the Option objects for the month, day and
            hour inputs.

        -   mdh_values: The value associated with each month, day and hour.
    """
    if sticky_key is not None:
        month_key = 'lbt_{}_month'.format(sticky_key)
        month_i_ = sc.sticky[month_key] if month_key in sc.sticky else default_inputs[0]
        day_key = 'lbt_{}_day'.format(sticky_key)
        day_ = sc.sticky[day_key] if day_key in sc.sticky else default_inputs[1]
        sthr_key = 'lbt_{}_start_hour'.format(sticky_key)
        st_hr_ = sc.sticky[sthr_key] if sthr_key in sc.sticky else default_inputs[2]
        endhr_key = 'lbt_{}_end_hour'.format(sticky_key)
        end_hr_ = sc.sticky[endhr_key] if endhr_key in sc.sticky else default_inputs[3]
    else:
        month_i_, day_, st_hr_, end_hr_ = default_inputs

    month_i_ = 0 if month_i_ < 0 else month_i_
    month_option = ('All', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'DecMarJun')
    input_request.AddOptionList('Month', month_option, month_i_)

    day_option = Rhino.Input.Custom.OptionInteger(day_, 0, 31)
    description = 'Day - day of the month [1-31]. Use 0 to specify all days'
    input_request.AddOptionInteger('Day', day_option, description)

    start_hr_option = Rhino.Input.Custom.OptionDouble(st_hr_, 0, 23)
    description = 'StartHour - start hour of the day [0-23]. Decimals accepted.'
    input_request.AddOptionDouble('StartHour', start_hr_option, description)

    end_hr_option = Rhino.Input.Custom.OptionDouble(end_hr_, 0, 23)
    description = 'EndHour - start hour of the day [0-23]. Decimals accepted.'
    input_request.AddOptionDouble('EndHour', end_hr_option, description)

    return [month_option, day_option, start_hr_option, end_hr_option], \
        [month_i_, day_, st_hr_, end_hr_]


def add_legend_min_max_options(input_request):
    """Add legend min and max outputs to an input request.

    Args:
        input_request: A Rhino Command Input such as that obtained from the
            setup_epw_input function or the Rhino.Input.Custom.GetString
            constructor.

    Returns:
        A tuple with two values.

        -   options: The two Option objects for the legend min and max inputs.

        -   values: The two values of the min and max.
    """
    min_val, max_val = float('-inf'), float('+inf')
    min_option = Rhino.Input.Custom.OptionDouble(min_val)
    input_request.AddOptionDouble('MinLegend', min_option)
    max_option = Rhino.Input.Custom.OptionDouble(max_val)
    input_request.AddOptionDouble('MaxLegend', max_option)
    return [min_option, max_option], [min_val, max_val]


def retrieve_geometry_input(geo_input_request, command_options, option_values):
    """Retrieve a geometry input from the command line.

    Args:
        geo_input_request: The Rhino.Input.Custom.GetObject object that was used
            to setup the geometry input request. Note that this input does not
            need any filters set on it as this method will assign them.
        command_options: A list of Rhino.Input.Custom.Option objects for the
            options that were included with the geometry request. The values for
            these options will be retrieved along with the geometry.
        option_values: A list of values for each option, which will be updated
            based on the user input.

    Returns:
        A list of geometry objects. Will be None if the operation was canceled.
    """
    # add the filters and  attributes related to geometry selection
    geo_filter = Rhino.DocObjects.ObjectType.Surface | \
        Rhino.DocObjects.ObjectType.PolysrfFilter | \
        Rhino.DocObjects.ObjectType.Mesh
    geo_input_request.GeometryFilter = geo_filter
    geo_input_request.GroupSelect = True
    geo_input_request.SubObjectSelect = False
    geo_input_request.EnableClearObjectsOnEntry(False)
    geo_input_request.EnableUnselectObjectsOnExit(False)
    geo_input_request.DeselectAllBeforePostSelect = False
    geo_input_request.AcceptNothing(True)

    # request the analysis geometries from the user
    have_preselected_objects = False
    while True:
        res = geo_input_request.GetMultiple(1, 0)
        if res == Rhino.Input.GetResult.Option:
            geo_input_request.EnablePreSelect(False, True)
            continue
        elif res != Rhino.Input.GetResult.Object:
            if res == Rhino.Input.GetResult.Cancel:
                return None
            return []
        if geo_input_request.ObjectsWerePreselected:
            have_preselected_objects = True
            geo_input_request.EnablePreSelect(False, True)
            continue
        for i, opt in enumerate(command_options):
            option_values[i] = opt.CurrentValue
        break

    # process any preselected objects before the command ran
    if have_preselected_objects:
        # Normally, pre-selected objects will remain selected, when a
        # command finishes, and post-selected objects will be unselected.
        # This this way of picking, it is possible to have a combination
        # of pre-selected and post-selected. So, to make sure everything
        # "looks the same", lets unselect everything before finishing
        # the command.
        for i in range(0, geo_input_request.ObjectCount):
            rhino_obj = geo_input_request.Object(i).Object()
            if rhino_obj is not None:
                rhino_obj.Select(False)
        sc.doc.Views.Redraw()

    # get the actual geometry from the selection
    obj_table = Rhino.RhinoDoc.ActiveDoc.Objects
    geometry = []
    for get_obj in geo_input_request.Objects():
        geometry.append(obj_table.Find(get_obj.ObjectId).Geometry)
    return geometry


def study_geometry_request(study_name=None):
    """Prompt the user for study geometry that requires a grid size and offset.

    Args:
        study_name: An optional text string for the name of the study (eg. Direct Sun).

    Returns:
        A tuple with three values.

        -   geometry: The Rhino Surfaces, Polysurfaces and/or Meshes that were selected.

        -   grid_size: A number for the grid size that the user selected.

        -   offset: A number for the offset that the user selected.
    """
    # setup the request to get the analysis geometry from the scene
    get_geo = Rhino.Input.Custom.GetObject()
    base_msg = 'Select surfaces, polysurfaces, or meshes'
    msg = '{} on which {} will be studied'.format(base_msg, study_name) \
        if study_name is not None else '{} to study.'.format(base_msg)
    get_geo.SetCommandPrompt(msg)

    # add the options for the geometry
    grid_size = sc.sticky['lbt_study_grid_size'] if 'lbt_study_grid_size' in sc.sticky \
        else int(1 / conversion_to_meters())
    gs_option = Rhino.Input.Custom.OptionDouble(grid_size, True, 0)
    description = 'GridSize - distance value for the size of grid cells at which ' \
        ' geometry will be subdivided'
    get_geo.AddOptionDouble('GridSize', gs_option, description)

    offset_dist = sc.sticky['lbt_study_offset'] if 'lbt_study_offset' in sc.sticky \
        else round((0.1 / conversion_to_meters()), 2)
    off_option = Rhino.Input.Custom.OptionDouble(offset_dist, True, 0)
    description = 'Offset - distance value from the input geometry at which the ' \
        'analysis will occur'
    get_geo.AddOptionDouble('Offset', off_option, description)

    # request the geometry from the user
    command_options = [gs_option, off_option]
    option_values = [grid_size, offset_dist]
    geometry = retrieve_geometry_input(get_geo, command_options, option_values)
    grid_size, offset_dist = option_values

    # update the sticky values for grid size and offset
    sc.sticky['lbt_study_grid_size'] = grid_size
    sc.sticky['lbt_study_offset'] = offset_dist

    return geometry, grid_size, offset_dist


def add_to_document_request(geometry_name=None):
    """Prompt the user for whether geometry should be added to the Rhino document.

    Returns:
        A boolean value for whether the geometry should be added to the document (True)
        or not (False).
    """
    gres = Rhino.Input.Custom.GetString()
    study_name = geometry_name if geometry_name is not None else 'Study'
    msg = '{} complete! Hit ENTER when done. Add the ' \
        'geometry to the document?'.format(study_name)
    gres.SetCommandPrompt(msg)
    gres.SetDefaultString('Add?')
    bake_result = False
    result_option = Rhino.Input.Custom.OptionToggle(False, 'No', 'Yes')
    gres.AddOptionToggle('AddToDoc', result_option)
    while True:
        get_res = gres.Get()
        if get_res == Rhino.Input.GetResult.String:
            bake_result = result_option.CurrentValue
        elif get_res == Rhino.Input.GetResult.Cancel:
            bake_result = False
            break
        else:
            continue
        break
    return bake_result


def bake_pollination_vis_set(vis_set, bake_3d_legend=False):
    """Bake a VisualizationSet using Pollination Rhino libraries for an editable legend.
    """
    Core = import_pollination_core()
    LadybugDisplaySchema = import_ladybug_display_schema()
    if not Core or not LadybugDisplaySchema:
        return
    for geo in vis_set.geometry:
        if isinstance(geo, AnalysisGeometry):
            amsh_typs = ('faces', 'vertices')
            if isinstance(geo.geometry[0], Mesh3D) and geo.matching_method in amsh_typs:
                layer_name = vis_set.display_name if len(vis_set.geometry) == 1 else \
                    '{}::{}'.format(vis_set.display_name, geo.display_name)
                for data in geo.data_sets:
                    # translate Mesh3D into Rhino Mesh
                    if len(geo.geometry) == 1:
                        mesh = from_mesh3d(geo.geometry[0])
                    else:
                        mesh = Rhino.Geometry.Mesh()
                        for mesh_i in geo.geometry:
                            mesh.Append(from_mesh3d(mesh_i))
                    # translate visualization data into .NET VisualizationData
                    data_json = json.dumps(data.to_dict())
                    vis_data = LadybugDisplaySchema.VisualizationData.FromJson(data_json)
                    a_mesh = Core.Objects.AnalysisMeshObject(mesh, vis_data)
                    # add it to the Rhino document
                    doc = Rhino.RhinoDoc.ActiveDoc
                    sub_layer_name = layer_name \
                        if len(geo.data_sets) == 1 or data.data_type is None else \
                        '{}::{}'.format(layer_name, data.data_type.name)
                    a_mesh.Id = doc.Objects.AddMesh(
                        mesh, _get_attributes(sub_layer_name))
                    current_model = Core.ModelEntity.CurrentModel

                    def do_act():
                        pass

                    def undo_act():
                        pass
                    am_list = System.Array[Core.Objects.AnalysisMeshObject]([a_mesh])
                    current_model.Add(doc, am_list, do_act, undo_act)
            else:
                bake_analysis(
                    geo, vis_set.display_name, bake_3d_legend,
                    vis_set.min_point, vis_set.max_point)
        else:
            bake_context(geo, vis_set.display_name)


def _convert_unit_abbrev(unit_str):
    """Replace all superscripts and other crud used in the .NET unit abbreviations."""
    clean_chars = []
    for c in unit_str:
        c_ord = ord(c)
        if c_ord < 128:  # ASCII character
            clean_chars.append(c)
        elif c_ord == 178:  # superscript 2
            clean_chars.append('2')
        elif c_ord == 179:  # superscript 3
            clean_chars.append('3')
        elif c_ord == 183:  # multiplication dot
            clean_chars.append('-')
        elif c_ord == 176:  # unnecessary degree symbol
            pass
        elif c_ord == 8710:  # delta symbol
            clean_chars.append('d')
        else:
            print('Character "{}" with ordinal {} was not decoded.'.format(c, c_ord))
    unit_str = ''.join(clean_chars)
    if unit_str == 'lx':
        return 'lux'
    return unit_str.replace(' ', '').replace('BTU', 'Btu')
