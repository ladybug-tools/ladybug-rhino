"""Functions for exporting all content from Grasshopper component objects."""
import os

try:
    import Grasshopper.Kernel as gh
except ImportError:
    raise ImportError("Failed to import Grasshopper.")

from .diff import current_userobject_version, validate_version
from .userobject import create_userobject
from .component import Component


def export_component(folder, component, change_type='fix'):
    """Export a Grasshopper component object to a package folder.

    This method writes the following files:

    * A .ghuser into the user_objects subfolder
    * A .py file into the src subfolder
    * A .json into the json subfolder
    # A .png into the icon subfolder

    Args:
        folder: Path to a folder into which the component files will be exported.
            Typically, this is the package folder of a grasshopper plugin repo.
            (eg. ladybug-grasshopper/ladybug_grasshopper).
        component: The Grasshopper component object to be exported to the folder.
        change_type: Text for the change type of the export. Valid change types
            can be seen under the CHANGE_TAGS property of the userobject module.
    """
    # process the component into a user object
    current_version = current_userobject_version(component)
    validate_version(current_version, component.Message, change_type)
    uo = create_userobject(component)

    # create subfolders in the folder if they are not already created
    uo_folder = os.path.join(folder, 'user_objects')
    src_folder = os.path.join(folder, 'src')
    json_folder = os.path.join(folder, 'json')
    icon_folder = os.path.join(folder, 'icon')
    for f in (folder, uo_folder, src_folder, json_folder, icon_folder):
        if not os.path.isdir(f):
            os.mkdir(f)

    # get the paths to the where the files will be written
    uo_fp = os.path.join(uo_folder, '%s.ghuser' % uo.Description.Name)
    src_fp = os.path.join(src_folder, '%s.py' % uo.Description.Name)
    json_fp = os.path.join(json_folder, '%s.json' % uo.Description.Name)
    icon_fp = os.path.join(icon_folder, '%s.png' % uo.Description.Name)

    # export the userobject to the user_objects subfolder
    if os.path.isfile(uo_fp):
        os.remove(uo_fp)
    uo.Path = uo_fp
    uo.SaveToFile()

    # export the .py file to the src subfolder
    code = uo.InstantiateObject().Code
    if isinstance(code, unicode):
        code = code.encode('utf8', 'ignore').replace("\r", "")
    with open(src_fp, 'w') as outf:
        outf.write(code)

    # export the .json file to the json subfolder
    if os.path.isfile(json_fp):
        os.remove(json_fp)
    component_obj = Component.from_gh_component(component)
    component_obj.to_json(json_folder)

    # export the icon file
    icon = component.Icon_24x24
    icon.Save(icon_fp)

    print('    UserObject, source code, icon and JSON are copied to folder.')


def refresh_toolbar():
    """Try to refresh the Grasshopper toolbar after exporting a component."""
    gh.GH_ComponentServer.UpdateRibbonUI()
