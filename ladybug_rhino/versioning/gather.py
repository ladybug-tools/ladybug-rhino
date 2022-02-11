"""Functions for gathering connected components or all components on a canvas."""
try:
    import System.Drawing
except ImportError:
    raise ImportError("Failed to import System.")

try:
    import Grasshopper.Kernel as gh
    import Grasshopper.Instances as ghi
except ImportError:
    raise ImportError("Failed to import Grasshopper.")


# Master array of all identifiers of Ladybug Tools components
LADYBUG_TOOLS = ('LB', 'HB', 'DF', 'BF', 'Ladybug', 'Honeybee',
                 'Butterfly', 'HoneybeePlus')


def is_ladybug_tools(component):
    """Check if a component is a part of Ladybug Tools."""
    return component.Name.split(' ')[0] in LADYBUG_TOOLS or \
        component.Name.split('_')[0] in LADYBUG_TOOLS


def gather_canvas_components(component):
    """Get all of the Ladybug Tools components on the same canvas as the input component.

    This will also gather any Ladybug Tools components inside of clusters.

    Args:
        component: A Grasshopper component object. Typically, this should be the
            exporter component object, which can be accessed through the
            ghenv.Component call.

    Returns:
        A list of Ladybug Tools component objects on the same canvas as the
        input component. The input component is excluded from this list.
    """
    components = []
    document = component.OnPingDocument()
    for comp_obj in document.Objects:
        if type(comp_obj) == type(component):  # GHPython component
            if is_ladybug_tools(comp_obj):  # Ladybug Tools component
                components.append(comp_obj)
        elif type(comp_obj) == gh.Special.GH_Cluster:
            cluster_doc = comp_obj.Document("")
            if not cluster_doc:
                continue
            for cluster_obj in cluster_doc.Objects:
                if type(cluster_obj) == type(component) and \
                        is_ladybug_tools(cluster_obj):
                    if cluster_obj.Locked:
                        continue
                    components.append(cluster_obj)

    # remove the exporter component from the array
    components = tuple(comp for comp in components if
                       comp.InstanceGuid != component.InstanceGuid)

    return components


def gather_connected_components(component):
    """Get all of the GHPython components connected to the component's first input.

    Args:
        component: A Grasshopper component object. Typically, this should be the
            exporter component object, which can be accessed through the
            ghenv.Component call.

    Returns:
        A list of Ladybug Tools component objects that are connected to the component's
        first input.
    """
    param = component.Params.Input[0]  # components input
    sources = param.Sources

    if sources.Count == 0:
        # no component is connected
        yield []

    for src in sources:
        attr = src.Attributes
        if attr is None or attr.GetTopLevel is None:  # not exportable
            continue
        # collect components
        comp_obj = attr.GetTopLevel.DocObject
        if comp_obj is None:
            continue
        if type(comp_obj) != type(component):  # not a GHPython component
            continue

        yield comp_obj


def plugin_components(plugin_name, sub_category=None):
    """Get all of the components of a Ladybug Tools Plugin from the component server.

    Args:
        plugin_name: Text for the name of a particular plugin (aka. insect) to
            place components from (eg. "Ladybug", "Honeybee", "HB-Energy").
        sub_category: Text for a specific plugin sub-category (aka. tab) to
            be exported (eg. "1 :: Analyze Data"). If None, all components in
            the plugin will be places on the canvas. (Default: None).

    Returns:
        A dictionary of the plugin components with the name of the component as
        the key and the component object as the value.
    """
    # loop through the component server and find all the components in the plugin
    components = {}
    for proxy in ghi.ComponentServer.ObjectProxies:
        if proxy.Obsolete:
            continue
        category = proxy.Desc.Category
        subcategory = proxy.Desc.SubCategory
        # check to see if the component is in the plugin
        if category.strip() == plugin_name:  # if so, see if it is in the sub category
            if sub_category is None or subcategory.strip() == sub_category:
                if str(proxy.Kind) == 'CompiledObject':  # it's a .gha
                    components[proxy.Desc.Name] = proxy.CreateInstance()
                elif str(proxy.Kind) == 'UserObject':  # it's a .ghuser
                    components[proxy.Desc.Name] = \
                        gh.GH_UserObject(proxy.Location).InstantiateObject()
    return components


def place_component(component_reference, component_name, x_position=200, y_position=200,
                    hold_solution=False):
    """Place a single component on the canvas.

    Args:
        component_reference: A Grasshopper component reference object to be placed
            on the canvas.
        component_name: Text for the name of the component being placed.
        x_position: An integer for where in the X dimension of the canvas the
            components will be dropped. (Default: 200).
        y_position: An integer for where in the Y dimension of the canvas the
            components will be dropped. (Default: 200).
        hold_solution: Boolean to note whether to hold off on the solution after
            the component is dropped on the canvas. (Default: False).

    Returns:
        The Component Object for the components that have been dropped
        onto the canvas.
    """
    document = ghi.ActiveCanvas.Document  # get the Grasshopper document
    component_reference.Attributes.Pivot = System.Drawing.PointF(x_position, y_position)
    document.AddObject(component_reference, False, 0)

    # find the component object on the Grasshopper canvas using its name
    component = None
    for comp in document.Objects:
        if comp.Name == component_name:
            component = comp
            break

    # expire component solution so that all of the components don't run at once
    if hold_solution:
        try:
            component.ExpireSolution(False)
        except Exception:
            print('Failed to stop "{}" from running'.format(component_name))
    return component


def place_plugin_components(plugin_name, sub_category=None, x_position=200,
                            y_position=200):
    """Place all of the components of a specific Ladybug Tools Plugin on the canvas.

    Args:
        plugin_name: Text for the name of a particular plugin (aka. insect) to
            place components from (eg. "Ladybug", "Honeybee", "HB-Energy").
        sub_category: Text for a specific plugin sub-category (aka. tab) to
            be exported (eg. "1 :: Analyze Data"). If None, all components in
            the plugin will be places on the canvas. (Default: None).
        x_position: An integer for where in the X dimension of the canvas the
            components will be dropped. (Default: 200).
        y_position: An integer for where in the Y dimension of the canvas the
            components will be dropped. (Default: 200).

    Returns:
        A list of Component Objects for the components that have been dropped
        onto the canvas. These component objects can be used to update the
        version of the dropped component, change their category, etc.
    """
    # find all Components/UserObjects in the Grasshopper Component Server
    component_references = plugin_components(plugin_name, sub_category)

    # loop through the components and add them to the canvass
    components = []  # array to hold all of the dropped components
    for comp_name, comp_obj in component_references.items():
        # add object to document
        if comp_obj.Attributes:
            comp = place_component(comp_obj, comp_name, x_position, y_position, True)
            components.append(comp)
    return components


def remove_component(component):
    """Remove a Grasshopper component from the canvas.

    Args:
        component: The Grasshopper component object to be removed.
    """
    document = ghi.ActiveCanvas.Document  # get the Grasshopper document
    document.RemoveObject(component, False)
