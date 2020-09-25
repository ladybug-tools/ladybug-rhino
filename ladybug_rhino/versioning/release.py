"""Functions specific to stable releases like changing component versions."""


def update_component_version(components, version, year=None):
    """Update the version number and copyright year for a list of components.

    Args:
        components: A list of Grasshopper component objects which will have
            their version updated. Typically, this should be the output of the
            place_plugin_components method from ladybug_rhino.versioning.gather.
        version: Text for the version of the components to update.
        year: Text for the copyright year to update.

    Returns:
        A list of Ladybug Tools component objects that have had their version
        and copyright year updated.
    """
    new_components = []
    for comp_obj in components:
        try:
            # get the code from inside the component
            in_code = comp_obj.Code.split("\n")
            code_length = len(in_code)
            out_code = ''

            # loop through the lines of code and replace the version + copyright
            for line_count, line in enumerate(in_code):
                # replace the mesage and copyright lines
                if line.startswith('ghenv.Component.Message'):
                    line = "ghenv.Component.Message = '{}'".format(version)
                elif line.startswith('# Copyright (c) ') and year is not None:
                    line = '# Copyright (c) {}, Ladybug Tools.'.format(year)

                # append the code to the output lines
                if line_count != code_length - 1:
                    out_code += line + "\n"
                else:
                    out_code += line

            comp_obj.Code = out_code  # replace the old code with updated code
            new_components.append(comp_obj)
        except Exception:  # not a Ladybug Tools component
            print('Failed to update version in "{}".'.format(comp_obj.Name))
    return new_components
