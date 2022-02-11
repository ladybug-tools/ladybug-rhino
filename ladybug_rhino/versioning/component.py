"""Module for exporting components from Grasshopper with all metadata and source code.
"""
import json
import os


class Component(object):
    """Grasshopper component wrapper used to serialize component properties to dict.

    Args:
        name: Text for the name of the component.
        nickname: Text for the nickname of the component.
        description: Text for the description of the component.
        code: Text for all the Python code of the component.
        category: Text for all Python code in the component (including import statements)
        subcategory: Text for the subcategory of the component.
        version: Text for the version of the component formatted as a 3-number
            semantic version.
    """
    # dictionary to map plugin-specific language to generic slugs
    MAPPING = {
        'grasshopper': '{{plugin}}',
        'Grasshopper': '{{Plugin}}',
        'GH': '{{PLGN}}',
        'Food4Rhino': '{{Package_Manager}}',
        'rhino': '{{cad}}',
        'Rhino': '{{Cad}}'
    }

    def __init__(self, name, nickname, description, code,
                 category, subcategory, version):
        """Grasshopper component wrapper."""
        self.name = name.replace('\r\n', '\n')
        self.nickname = nickname.replace('\r\n', '\n')
        self.description = description.replace('\r\n', '\n')
        self.code = code.replace('\r\n', '\n')
        self.category = category.replace('\r\n', '\n')
        self.subcategory = subcategory.replace('\r\n', '\n')
        self.version = version
        self._inputs = []
        self._outputs = []

    @classmethod
    def from_gh_component(cls, component):
        """Create Component from a Grasshopper component object.

        Args:
            component: A Grasshopper component object.
        """
        comp = cls(component.Name, component.NickName, component.Description,
                   component.Code, component.Category, component.SubCategory,
                   component.Message)

        for inp in component.Params.Input:
            comp.add_input(Port.from_gh_port(inp))

        for out in component.Params.Output:
            if out.Name == 'out':
                continue
            comp.add_output(Port.from_gh_port(out))

        return comp

    @property
    def inputs(self):
        """Get a list of Port objects for the component Inputs."""
        return self._inputs

    @property
    def outputs(self):
        """Get a list of Port objects for the component Outputs."""
        return self._outputs

    def add_input(self, inp):
        """Add an input for the component.

        Args:
            inp: A Port object for the input.
        """
        assert isinstance(inp, Port)
        self._inputs.append(inp)

    def add_output(self, out):
        """Add an output for the component.

        Args:
            out: A Port object for the output.
        """
        assert isinstance(out, Port)
        self._outputs.append(out)

    def to_dict(self):
        """Get the Component instance as a dictionary."""
        component = {
            'name': self.name,
            'version': self.version,
            'nickname': self.nickname,
            'description': self.description,
            'code': self._clean_code(),
            'category': self.category,
            'subcategory': self.subcategory,
            'inputs': [i.to_dict() for i in self.inputs],
            'outputs': [[i.to_dict() for i in self.outputs]]
        }
        return component

    def to_json(self, folder, name=None, indent=2):
        """Write the Component instance to a JSON file.

        Args:
            folder: Text for the folder into which the JSON should be written.
            name: Text for the file name for the JSON.
            indent: Integer for the number of spaces in an indent.
        """
        name = name or self.name.replace(' ', '_')
        if not name.lower().endswith('.json'):
            name = '%s.json' % name
        fp = os.path.join(folder, name)
        with open(fp, 'w') as outf:
            json.dump(self.to_dict(), outf, indent=indent)

    def _clean_code(self):
        """Clean up the text of the code before export.

        This replaces plugin-specific text like "Grasshopper" with the generic slugs
        in the MAPPING property of this class.
        """
        code = self.code
        code = code.split('\n')

        for count, line in enumerate(code):
            if line.startswith('ghenv.Component.AdditionalHelpFromDocStrings'):
                break

        gist = '\n'.join(code[count + 1:])

        for o, t in self.MAPPING.items():
            gist = gist.replace(o, t)

        return gist


class Port(object):
    """Grasshopper port wrapper used to serialize inputs and outputs to dict.

    Args:
        name: Text for the name of the input or output.
        description: Text for the description of the input or output.
        default_value: Default value for the input or output.
        value_type: Text the type of input or output (eg. bool)
        access_type: Text for list vs. item access.
    """

    def __init__(self, name, description=None, default_value=None, value_type=None,
                 access_type=None):
        self.name = name.replace('\r\n', '\n')
        self.description = description.replace('\r\n', '\n')
        self.default_value = default_value
        self.value_type = value_type
        self.access_type = str(access_type)

    @classmethod
    def from_gh_port(cls, port):
        """Create Port from a Grasshopper port object.

        Args:
            port: A Grasshopper port object, typically accessed by iterating over the
                component.Params.Input or component.Params.Output properties.
        """
        if hasattr(port, 'TypeHint'):  # it's an input
            v = port.VolatileData
            if v.IsEmpty:
                value = None
            else:
                values = tuple(str(i.Value).lower() if port.TypeHint.TypeName == 'bool'
                               else i.Value for i in v.AllData(True))
                try:
                    value = tuple(v.replace('\\\\', '\\').replace('\\', '\\\\')
                                  for v in values)
                except AttributeError:
                    # non string type
                    value = values

            if value and str(port.Access) == 'item':
                value = value[0]

            return cls(port.Name, port.Description, value, port.TypeHint.TypeName,
                       str(port.Access))
        else:  # it's an output
            return cls(port.Name, port.Description, None, None, None)

    def to_dict(self):
        """Translate Port instance to a dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'default': self.default_value,
            'type': self.value_type,
            'access': self.access_type
        }
