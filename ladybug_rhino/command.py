"""Functions for dealing assisting with Rhino plugin commands."""
from __future__ import division
import os
import sys

try:
    import clr
    from System import Environment
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
    from ladybug.futil import unzip_file
    from ladybug.config import folders
except ImportError as e:
    raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))

from .download import download_file
from .config import rhino_version


def is_pollination_licensed():
    """Check if the installation of Pollination has an active license."""
    try:
        import Core
    except ImportError:  # the dll has not yet been added
        # add the OpenStudio DLL to the Common Language Runtime (CLR)
        install_dir = os.path.dirname(folders.ladybug_tools_folder)
        rh_ver_str = str(rhino_version[0]) + '.0'
        dll_dir = os.path.join(
            install_dir, 'pollination', 'plugin', rh_ver_str, 'Pollination')
        pol_dll = os.path.join(dll_dir, 'Pollination.Core.dll')
        if not os.path.isfile:
            msg = 'No Pollination installation could be found ' \
                'for Rhino {}.'.format(rh_ver_str)
            return False
        clr.AddReferenceToFileAndPath(pol_dll)
        if pol_dll not in sys.path:
            sys.path.append(pol_dll)
        import Core
    # use the utility to check whether there is an active license
    is_licensed, msg = Core.Utility.CheckIfLicensed()
    if not is_licensed:
        print(msg)
    return is_licensed


def local_processor_count():
    """Get an integer for the number of processors on this machine.

    If, for whatever reason, the number of processors could not be sensed,
    None will be returned.
    """
    return Environment.ProcessorCount


def recommended_processor_count():
    """Get an integer for the recommended number of processors for parallel calculation.

    This should be one less than the number of processors available on this machine
    unless the machine has only one processor, in which case 1 will be returned.
    If, for whatever reason, the number of processors could not be sensed, a value
    of 1 will be returned.
    """
    cpu_count = local_processor_count()
    return 1 if cpu_count is None or cpu_count <= 1 else cpu_count - 1


def setup_epw_input():
    """Setup the request for an EPW input and check for any previously set EPW."""
    epw_input_request = Rhino.Input.Custom.GetString()
    epw_input_request.SetCommandPrompt('Select an EPW file path or URL')
    epw_path = None
    if 'lbt_epw' in sc.sticky:
        epw_path = sc.sticky['lbt_epw']
        epw_input_request.SetDefaultString(epw_path)
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
        break

    # process the EPW file path or URL
    if not epw_path:
        return None
    _def_folder = folders.default_epw_folder
    if epw_path.startswith('http'):  # download the EPW file
        _weather_URL = epw_path
        if _weather_URL.lower().endswith('.zip'):  # onebuilding URL type
            _folder_name = _weather_URL.split('/')[-1][:-4]
        else:  # dept of energy URL type
            _folder_name = _weather_URL.split('/')[-2]
        epw_path = os.path.join(_def_folder, _folder_name, _folder_name + '.epw')
        if not os.path.isfile(epw_path):
            zip_file_path = os.path.join(
                _def_folder, _folder_name, _folder_name + '.zip')
            download_file(_weather_URL, zip_file_path, True)
            unzip_file(zip_file_path)
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
    north_value = sc.sticky['lbt_north'] if 'lbt_north' in sc.sticky else 0
    north_option = Rhino.Input.Custom.OptionDouble(north_value, -360, 360)
    description = 'North - the counterclockwise difference between true North and the ' \
        'Y-axis in degrees (90:West, -90:East)'
    input_request.AddOptionDouble('North', north_option, description)
    return north_option, north_value


def add_month_day_hour_options(input_request, default_inputs=(12, 21, 12), sticky_key=None):
    """Add a options for Month, Day, and Hour to an input request.

    Args:
        input_request: A Rhino Command Input such as that obtained from the
            setup_epw_input function or the Rhino.Input.Custom.GetString
            constructor.
        default_inputs: The default input month, day and hour. A negative
            number denotes all values of a given month, day and hour are used.
            In the case of month and dy, 0 can also be used to denote all
            values. (Default: (12, 21, -1)).
        sticky_key: An optional sticky key, which will be used to to pull
            previously set values from sticky. (eg. sunpath).

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
        hour_key = 'lbt_{}_hour'.format(sticky_key)
        hour_ =  sc.sticky[hour_key] if hour_key in sc.sticky else default_inputs[2]
    else:
        month_i_, day_, hour_ = default_inputs

    month_i_ = 0 if month_i_ < 0 else month_i_
    month_option = ('All', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
    month_list = input_request.AddOptionList('Month', month_option, month_i_)

    day_option = Rhino.Input.Custom.OptionInteger(day_, -1, 31)
    description = 'Day - day of the month. Use -1 to specify all days.'
    input_request.AddOptionInteger('Day', day_option, description)

    hour_option = Rhino.Input.Custom.OptionInteger(hour_, -1, 22)
    description = 'Hour - hour of the day. Use -1 to specify all hours.'
    input_request.AddOptionInteger('Hour', hour_option, description)

    return [month_option, day_option, hour_option], [month_i_, day_, hour_]


def add_to_document_request(geometry_name=None):
    """Prompt the user for whether geometry should be added to the Rhino document.

    Returns:
        A boolean value for whether the geometry should be added to the document (True)
        or not (False).
    """
    gres = Rhino.Input.Custom.GetString()
    geo_name = geometry_name + ' ' if geometry_name is not None else ''
    msg = 'Would you like to add the {}Geometry to the Document? ' \
        'Hit ENTER when done.'.format(geo_name)
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
