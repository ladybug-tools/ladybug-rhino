"""Collection of methods for downloading files securely using .NET libraries."""
import os
import json

try:
    from ladybug.config import folders
    from ladybug.futil import preparedir, unzip_file
    from ladybug.epw import EPW
    from ladybug.stat import STAT
    from ladybug.climatezone import ashrae_climate_zone
except ImportError as e:
    raise ImportError("Failed to import ladybug.\n{}".format(e))

try:
    import System.Net
except ImportError as e:
    print("Failed to import Windows/.NET libraries\n{}".format(e))


def download_file_by_name(url, target_folder, file_name, mkdir=False):
    """Download a file to a directory.

    Args:
        url: A string to a valid URL.
        target_folder: Target folder for download (e.g. c:/ladybug)
        file_name: File name (e.g. testPts.zip).
        mkdir: Set to True to create the directory if doesn't exist (Default: False)
    """
    # create the target directory.
    if not os.path.isdir(target_folder):
        if mkdir:
            preparedir(target_folder)
        else:
            created = preparedir(target_folder, False)
            if not created:
                raise ValueError("Failed to find %s." % target_folder)
    file_path = os.path.join(target_folder, file_name)

    # set the security protocol to the most recent version
    try:
        # TLS 1.2 is needed to download over https
        System.Net.ServicePointManager.SecurityProtocol = \
            System.Net.SecurityProtocolType.Tls12
    except AttributeError:
        # TLS 1.2 is not provided by MacOS .NET in Rhino 5
        if url.lower().startswith('https'):
            print('This system lacks the necessary security'
                  ' libraries to download over https.')

    # attempt to download the file
    client = System.Net.WebClient()
    try:
        client.DownloadFile(url, file_path)
    except Exception as e:
        raise Exception(' Download failed with the error:\n{}'.format(e))


def download_file(url, file_path, mkdir=False):
    """Write a string of data to file.

    Args:
        url: A string to a valid URL.
        file_path: Full path to intended download location (e.g. c:/ladybug/testPts.pts)
        mkdir: Set to True to create the directory if doesn't exist (Default: False)
    """
    folder, fname = os.path.split(file_path)
    return download_file_by_name(url, folder, fname, mkdir)


def extract_project_info(project_info_json):
    """Extract relevant project information from project info JSON containing URLs.

    Args:
        project_info_json: A JSON string of a ProjectInfo object, which
            contains at least one Weather URL. If the ProjectInfo does not
            contain information that resides in the weather file, this info
            will be extracted and put into the returned object.

    Returns:
        A tuple with two values.

        -   project_info_json: A JSON string of project information containing
            information extracted from the EPW URL.

        -   epw_path: The local file path to the downloaded EPW.
    """
    #convert the JSON into a dictionary and extract the EPW URL
    project_info = json.loads(project_info_json)
    if 'weather_urls' not in project_info or len(project_info['weather_urls']) == 0:
        return project_info_json
    weather_url = project_info['weather_urls'][0]

    # download the EPW file to the user folder
    _def_folder = folders.default_epw_folder
    if weather_url.lower().endswith('.zip'):  # onebuilding URL type
        _folder_name = weather_url.split('/')[-1][:-4]
    else:  # dept of energy URL type
        _folder_name = weather_url.split('/')[-2]
    epw_path = os.path.join(_def_folder, _folder_name, _folder_name + '.epw')
    if not os.path.isfile(epw_path):
        zip_file_path = os.path.join(
            _def_folder, _folder_name, _folder_name + '.zip')
        download_file(weather_url, zip_file_path, True)
        unzip_file(zip_file_path)

    # add the location to the project_info dictionary
    epw_obj = None
    if 'location' not in project_info or project_info['location'] is None:
        epw_obj = EPW(epw_path)
        project_info['location'] = epw_obj.location.to_dict()
    else:
        loc_dict = project_info['location']
        loc_props = (loc_dict['latitude'], loc_dict['longitude'], loc_dict['elevation'])
        if all(prop == 0 for prop in loc_props):
            epw_obj = EPW(epw_path)
            project_info['location'] = epw_obj.location.to_dict()

    # add the climate zone to the project_info dictionary
    if 'ashrae_climate_zone' not in project_info or \
            project_info['ashrae_climate_zone'] is None:
        zone_set = False
        stat_path = os.path.join(_def_folder, _folder_name, _folder_name + '.stat')
        if os.path.isfile(stat_path):
            stat_obj = STAT(stat_path)
            if stat_obj.ashrae_climate_zone is not None:
                project_info['ashrae_climate_zone'] = stat_obj.ashrae_climate_zone
                zone_set = True
        if not zone_set:  # get it from the EPW data
            epw_obj = EPW(epw_path) if epw_obj is None else epw_obj
            project_info['ashrae_climate_zone'] = \
                ashrae_climate_zone(epw_obj.dry_bulb_temperature)
    
    # convert the dictionary to a JSON
    project_info_json = json.dumps(project_info)
    return project_info_json, epw_path
