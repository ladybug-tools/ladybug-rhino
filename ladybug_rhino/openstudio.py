"""Functions for importing OpenStudio into the Python environment."""
import os
import shutil
import sys

try:
    import clr
except ImportError as e:  # No .NET being used
    print('Failed to import CLR. OpenStudio SDK is unavailable.\n{}'.format(e))

try:
    from honeybee_energy.config import folders
except ImportError as e:
    print('Failed to import honeybee_energy. '
          'OpenStudio SDK is unavailable.\n{}'.format(e))


def load_osm(osm_path):
    """Load an OSM file to an OpenStudio SDK Model object in the Python environment.

    Args:
        osm_path: The path to an OSM file to be loaded an an OpenStudio Model.

    Returns:
        An OpenStudio Model object derived from the input osm_path.

    Usage:

    .. code-block:: python

        from ladybug_rhino.openstudio import load_osm

        # load an OpenStudio model from an OSM file
        osm_path = 'C:/path/to/model.osm'
        os_model = load_osm(osm_path)

        # get the space types from the model
        os_space_types = os_model.getSpaceTypes()
        for spt in os_space_types:
            print(spt)
    """
    # check that the file exists and OpenStudio is installed
    assert os.path.isfile(osm_path), 'No OSM file was found at "{}".'.format(osm_path)
    ops = import_openstudio()

    # load the model object and return it
    os_path = ops.OpenStudioUtilitiesCore.toPath(osm_path)
    osm_path_obj = ops.Path(os_path)
    exist_os_model = ops.Model.load(osm_path_obj)
    if exist_os_model.is_initialized():
        return exist_os_model.get()
    else:
        raise ValueError(
            'The file at "{}" does not appear to be an OpenStudio model.'.format(
                osm_path
            ))


def dump_osm(model, osm_path):
    """Dump an OpenStudio Model object to an OSM file.

    Args:
        model: An OpenStudio Model to be written to a file.
        osm_path: The path of the .osm file where the OpenStudio Model will be saved.

    Returns:
        The path to the .osm file as a string.

    Usage:

    .. code-block:: python

        from ladybug_rhino.openstudio import load_osm, dump_osm

        # load an OpenStudio model from an OSM file
        osm_path = 'C:/path/to/model.osm'
        model = load_osm(osm_path)

        # get all of the SetpointManagers and set their properties
        setpt_managers = model.getSetpointManagerOutdoorAirResets()
        for setpt in setpt_managers:
            setpt.setSetpointatOutdoorLowTemperature(19)
            setpt.setOutdoorLowTemperature(12)
            setpt.setSetpointatOutdoorHighTemperature(16)
            setpt.setOutdoorHighTemperature(22)

        # save the edited OSM over the original one
        osm = dump_osm(model, osm_path)
    """
    # check that the model is the correct object type
    ops = import_openstudio()
    assert isinstance(model, ops.Model), \
        'Expected OpenStudio Model. Got {}.'.format(type(model))

    # load the model object and return it
    os_path = ops.OpenStudioUtilitiesCore.toPath(osm_path)
    osm_path_obj = ops.Path(os_path)
    model.save(osm_path_obj, True)
    return osm_path


def import_openstudio():
    """Import the OpenStudio SDK into the Python environment.

    Returns:
        The OpenStudio NameSpace with all of the modules, classes and methods
        of the OpenStudio SDK.

    Usage:

    .. code-block:: python

        from ladybug_rhino.openstudio import import_openstudio, dump_osm
        OpenStudio = import_openstudio()

        # create a new OpenStudio model from scratch
        os_model = OpenStudio.Model()
        space_type = OpenStudio.SpaceType(os_model)

        # save the Model to an OSM
        osm_path = 'C:/path/to/model.osm'
        osm = dump_osm(os_model, osm_path)
    """
    try:  # first see if OpenStudio has already been loaded
        import OpenStudio
        return OpenStudio
    except ImportError:
        # check to be sure that the OpenStudio CSharp folder has been installed
        compatibility_url = 'https://github.com/ladybug-tools/lbt-grasshopper/wiki/' \
            '1.4-Compatibility-Matrix'
        in_msg = 'Download and install the version of OpenStudio listed in the ' \
            'Ladybug Tools compatibility matrix\n{}.'.format(compatibility_url)
        assert folders.openstudio_path is not None, \
            'No OpenStudio installation was found on this machine.\n{}'.format(in_msg)
        assert folders.openstudio_csharp_path is not None, \
            'No OpenStudio CSharp folder was found in the OpenStudio installation ' \
            'at:\n{}'.format(os.path.dirname(folders.openstudio_path))
        _copy_openstudio_lib()

        # add the OpenStudio DLL to the Common Language Runtime (CLR)
        os_dll = os.path.join(folders.openstudio_csharp_path, 'OpenStudio.dll')
        clr.AddReferenceToFileAndPath(os_dll)
        if folders.openstudio_csharp_path not in sys.path:
            sys.path.append(folders.openstudio_csharp_path)
        import OpenStudio
        return OpenStudio


def _copy_openstudio_lib():
    """Copy the openstudiolib.dll into the CSharp folder.

    This is a workaround that is necessary because the OpenStudio installer
    does not install the CSharp bindings correctly.
    """
    # see if the CSharp folder already has everything it needs
    dest_file = os.path.join(folders.openstudio_csharp_path, 'openstudiolib.dll')
    if os.path.isfile(dest_file):
        return None

    # if not, see if the openstudio_lib_path has the file that needs to be copied
    base_msg = 'The OpenStudio CSharp path at "{}" lacks the openstudiolib.dll'.format(
        folders.openstudio_csharp_path)
    assert os.path.isdir(folders.openstudio_lib_path), \
        '{}\nand there is no OpenStudio Lib installed.'.format(base_msg)
    src_file = os.path.join(folders.openstudio_lib_path, 'openstudiolib.dll')
    assert os.path.isfile(src_file), \
        '{}\nand this file was not found at "{}".'.format(base_msg, src_file)

    # copy the DLL if it exists
    shutil.copy(src_file, dest_file)
