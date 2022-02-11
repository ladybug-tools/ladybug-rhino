"""Functions for exporting all content from Grasshopper component objects."""
import os
import shutil
import re

try:
    import System.Drawing
except ImportError:
    raise ImportError("Failed to import System.")

try:
    import Grasshopper
except ImportError:
    raise ImportError("Failed to import Grasshopper.")

from .diff import current_userobject_version, validate_version
from .userobject import create_userobject
from .component import Component

# characters that get removed and replaced when generating clean file names
REMOVE_CHARACTERS = ('LB ', 'HB ', 'DF ')
REPLACE_CHARACTERS = (' ', '/', '?', '|')

# map from the exposure category of a component to the order in which it is displayed
REVERSE_EXPOSURE_MAP = {
    'obscure': 100,
    'hidden': 100,
    'primary': 1,
    'secondary': 2,
    'tertiary': 3,
    'quarternary': 4,
    'quinary': 5,
    'senary': 6,
    'septenary': 7
}


def export_component(folder, component, change_type='fix'):
    """Export a Grasshopper component object to a package folder.

    This method writes the following files:

    * A .ghuser into the user_objects subfolder
    * A .py file into the src subfolder
    * A .json into the json subfolder
    * A .png into the icon subfolder

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
    try:
        if isinstance(code, unicode):
            code = code.encode('utf8', 'ignore').replace("\r", "")
    except Exception:
        pass  # we are not in Python 2
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


def export_component_screen_capture(folder, component, x_dim=1000, y_dim=1000):
    """Export a screen capture of a Grasshopper component object to a folder.

    The image will always be centered on the component and at a resolution where
    the inputs and outputs are clearly visible.

    Args:
        folder: Path to a folder into which the image file will be exported.
        component: The Grasshopper component object to be exported to the folder.
        x_dim: Integer for the X dimension of the exported image in
            pixels. (Default: 1000).
        y_dim: Integer for the X dimension of the exported image in
            pixels. (Default: 1000).
    """
    # Get the coordinates of the upper-left corner of the image from the component
    if component.Name == 'LB ImageViewer':
        ul_x = component.Attributes.Pivot.X - int(((x_dim / 2) - 400) / 2)
        ul_y = component.Attributes.Pivot.Y - int(((y_dim / 2) - 400) / 2)
    else:
        ul_x = component.Attributes.Pivot.X - int(((x_dim / 2) - 120) / 2)
        ul_y = component.Attributes.Pivot.Y - int(((y_dim / 2) - 120) / 2)
    rect = System.Drawing.Rectangle(ul_x, ul_y, x_dim, y_dim)

    # set the image zoon/resolution
    image_settings = Grasshopper.GUI.Canvas.GH_Canvas.GH_ImageSettings()
    image_settings.Zoom = 1.95
    canvas = Grasshopper.GH_InstanceServer.ActiveCanvas

    # capture the image of the component
    images_of_canvas = canvas.GenerateHiResImage(rect, image_settings)
    screen_capture = images_of_canvas[0][0]

    # resize the image
    loaded_img = System.Drawing.Bitmap(screen_capture)
    new_img = loaded_img.Clone(System.Drawing.Rectangle(0, 0, x_dim, y_dim),
                               loaded_img.PixelFormat)

    # write the image to a file
    file_name = clean_component_filename(component)
    file_path = os.path.join(folder, '{}.png'.format(file_name))
    new_img.Save(file_path)

    # delete original image
    loaded_img.Dispose()
    path = os.path.split(screen_capture)[0]
    shutil.rmtree(path)
    return file_path


def export_component_icon(folder, component):
    """Export a Grasshopper component icon to a folder.

    Args:
        folder: Path to a folder into which the icon image file will be exported.
        component: The Grasshopper component object to be exported to the folder.
    """
    file_name = clean_component_filename(component)
    file_path = os.path.join(folder, '{}.png'.format(file_name))
    icon = component.Icon_24x24
    icon.Save(file_path)


def export_component_to_markdown(folder, component, github_repo=None):
    """Export a Grasshopper component's description and metadata to a Markdown file.

    Args:
        folder: Path to a folder into which the MArkdown file will be exported.
        component: The Grasshopper component object to be exported to the folder.
        github_repo: Optional URL to a GitHub repo that can be used to link the
            Markdown page to a GitHub repository.
    """
    # get the relevant name information from the component
    b_name = component.Name
    for item in REMOVE_CHARACTERS:
        b_name = b_name.replace(item, '')
    name = clean_component_filename(component)
    lines = []

    # write the lines for the header with the image, icon and source code
    lines.append('## %s\n' % b_name)
    img_text = '![](../../images/components/%s.png)\n' % name
    lines.append(img_text)
    if github_repo:
        source = '![](../../images/icons/%s.png) - [[source code]](%s/%s.py)\n' % (
            name, github_repo, component.Name.replace(' ', '%20'))
        lines.append(source)

    # write the lines for the description
    full_desc = []
    for d_l in component.Description.split('\n'):
        if ('-' in d_l or '_' in d_l or '.' in d_l) and len(d_l) <= 2:
            full_desc.append('\n\n')
        else:
            full_desc.append('{} '.format(d_l.replace('\r', '')))
    lines.append('\n{}'.format(''.join(full_desc)))

    # check to see if there are any inputs and outputs to export
    inputs_outputs_available = True
    try:
        component.Params
    except Exception:  # no inputs and outputs available
        inputs_outputs_available = False

    if inputs_outputs_available:
        # export the inputs
        lines.append('\n#### Inputs')
        for i in range(component.Params.Input.Count):
            i_name = component.Params.Input[i].NickName
            alph = ''.join(re.findall('[a-zA-Z]+', i_name))
            if len(alph) == 0:
                continue

            t = ''
            if i_name.startswith('_') and i_name.endswith('_'):
                i_name = i_name[1:-1]
            elif i_name.startswith('_'):
                i_name = i_name[1:]
                t = '[Required]'
            elif i_name.endswith('_'):
                i_name = i_name[:-1]

            full_desc = []
            for d_l in component.Params.Input[i].Description.split('\n'):
                if ('-' in d_l or '_' in d_l or '.' in d_l) and len(d_l) <= 2:
                    full_desc.append('\n')
                elif d_l.startswith('*') or d_l.startswith('-'):
                    full_desc.append('\n\n    {}'.format(d_l.replace('\r', '')))
                else:
                    full_desc.append('{} '.format(d_l.replace('\r', '')))
            line = '* ##### {} {}\n{}'.format(i_name, t, ''.join(full_desc))
            lines.append(line)

        # export the outputs
        lines.append('\n#### Outputs')
        for i in range(component.Params.Output.Count):
            o_name = component.Params.Output[i].NickName
            alph = ''.join(re.findall('[a-zA-Z]+', o_name))
            if len(alph) == 0:
                continue
            full_desc = []
            for d_l in component.Params.Output[i].Description.split('\n'):
                if ('-' in d_l or '_' in d_l or '.' in d_l) and len(d_l) <= 2:
                    full_desc.append('\n')
                elif d_l.startswith('*') or d_l.startswith('-'):
                    full_desc.append('\n\n    {}'.format(d_l.replace('\r', '')))
                else:
                    full_desc.append('{} '.format(d_l.replace('\r', '')))
            line = '* ##### {}\n{}'.format(o_name, ''.join(full_desc))
            lines.append(line)

    # write the .md file
    file_path = os.path.join(folder, '{}.md'.format(name))
    with open(file_path, 'w') as out_f:
        out_f.write('\n'.join(lines).encode('utf-8'))
    return file_path


def export_plugin_to_markdown(folder, plugin_name):
    """Export a Grasshopper plugin and its subcategories to Markdown files.

    Args:
        folder: Path to a folder into which the icon image file will be exported.
        plugin_name: Text for the name of a particular plugin (aka. insect) to
            place components from (eg. "Ladybug", "Honeybee", "HB-Energy").
    """
    # gather all of the components of a plugin into a dictionary with subcategories
    components = {}
    for proxy in Grasshopper.Instances.ComponentServer.ObjectProxies:
        if proxy.Obsolete:
            continue
        category = proxy.Desc.Category
        subcategory = proxy.Desc.SubCategory
        # check to see if the component is in the plugin
        if category.strip() == plugin_name:  # if so, organize it by sub category
            if subcategory not in components.keys():
                components[subcategory] = {}
            expo = REVERSE_EXPOSURE_MAP[str(proxy.Exposure).split(',')[-1].strip()]
            if expo not in components[subcategory].keys():
                components[subcategory][expo] = []
            name = clean_component_filename(proxy.Desc)
            components[subcategory][expo].append(name)
    sorted_sub_categories = sorted(components.keys())

    # create the summary file header
    lines = []
    read_md = '[%s Primer](README.md)' % plugin_name
    header = '# Summary\n\n* ' + read_md + '\n* [Components](text/categories/README.md)'
    lines.append(header)

    # loop through the subcategories and add them to the index
    for s_category in sorted_sub_categories:
        # write the subcategory into the summary
        clean_cat = ''.join(s_category.split()).replace('|', '_').replace('::', '_')
        line = '\t* [%s](text/categories/%s.md)' % (s_category, clean_cat)
        lines.append(line)

        # collect text lines for the subcategory page
        s_category_lines = []
        for num in sorted(components[s_category].keys()):
            for comp in sorted(components[s_category][num]):
                readable_name = comp.replace('_', ' ')
                line = '\t\t* [%s](text/components/%s.md)' % (readable_name, comp)
                icon = '* ![IMAGE](../../images/icons/%s.png)' % comp
                s_category_lines.append(
                    icon + line.replace('\t\t*', '').replace('text', '..'))
                lines.append(line)

        # write md file for the category
        file_path = os.path.join(folder, 'text', 'categories', '%s.md' % clean_cat)
        with open(file_path, 'w') as tab:
            tab.write('#### Component list:\n' + '\n'.join(s_category_lines))

    # write the summary file
    file_path = os.path.join(folder, 'SUMMARY.md')
    with open(file_path, 'w') as summary:
        summary.write('\n'.join(lines))
    return file_path


def clean_component_filename(component):
    """Get a clean filename derived from a component's name."""
    file_name = component.Name
    for item in REMOVE_CHARACTERS:
        file_name = file_name.replace(item, '')
    for item in REPLACE_CHARACTERS:
        file_name = file_name.replace(item, '_')
    return file_name


def refresh_toolbar():
    """Try to refresh the Grasshopper toolbar after exporting a component."""
    Grasshopper.Kernel.GH_ComponentServer.UpdateRibbonUI()
