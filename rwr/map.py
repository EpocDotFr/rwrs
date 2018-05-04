from lxml import etree
import os


class Parser:
    data = {
        'name': None,
        'description': None,
        'capture_zones': {},
        'spawn_points': {
            'vehicles': {},
            'soldiers': {}
        }
    }

    namespaces = {
        'svg': 'http://www.w3.org/2000/svg',
        'inkscape': 'http://www.inkscape.org/namespaces/inkscape'
    }

    def __init__(self, filename):
        self.filename = filename

        if not os.path.isfile(self.filename):
            raise FileNotFoundError(self.filename + ' does not exists')

    def parse(self):
        """Actually run the parsing process."""
        self.tree = etree.parse(self.filename)
        self.tree_root = self.tree.getroot()

        for group in self.tree_root.iterchildren(Parser.nse('svg', 'g')):
            group_name = group.get(Parser.nse('inkscape', 'label'))

            if not group_name: # We don't know what's this group: ignore it
                continue

            if group_name == 'materials':
                self._parse_materials_group(group, group_name)
            elif group_name.startswith('bases') and '.' in group_name: # TODO Temporary
                self._parse_bases_group(group, group_name)
            elif group_name.startswith('layer') and '.' in group_name: # TODO Temporary
                self._parse_layer_group(group, group_name)

        return self.data

    def _parse_materials_group(self, group, group_name):
        """Parse the materials group."""
        for element in group.iterchildren():
            group_element_name = element.get(Parser.nse('inkscape', 'label'))

            if not group_element_name: # We don't know what's this element: ignore it
                continue

            if group_element_name == '#general': # General information about the map
                self._parse_general_map_info_element(element)

    def _parse_general_map_info_element(self, element):
        """Parse the general map information element."""
        map_info_attributes = element.findtext('svg:desc', namespaces=self.namespaces)

        if not map_info_attributes:
            return

        map_info_attributes = Parser.parse_attrs(map_info_attributes)

        self.data['name'] = map_info_attributes['name'] if 'name' in map_info_attributes else None
        self.data['description'] = map_info_attributes['description'] if 'description' in map_info_attributes else None

    def _parse_bases_group(self, group, group_name):
        """Parse a bases group."""
        group_id, game_type = group_name.split('.', maxsplit=1)

        if game_type not in self.data['capture_zones']:
            self.data['capture_zones'][game_type] = {}

        if group_id not in self.data['capture_zones'][game_type]:
            self.data['capture_zones'][game_type][group_id] = []

        for element in group.iterchildren(Parser.nse('svg', 'rect')):
            base_attributes = element.findtext('svg:desc', namespaces=self.namespaces)

            if not base_attributes:
                continue

            base_attributes = Parser.parse_attrs(base_attributes)

            lat1 = float(element.get('x'))
            lng1 = float(element.get('y'))
            lat2 = lat1 + float(element.get('width'))
            lng2 = lng1 + float(element.get('height'))

            self.data['capture_zones'][game_type][group_id].append({
                'name': base_attributes['name'] if 'name' in base_attributes else None,
                'faction_index': int(base_attributes['faction_index']) if 'faction_index' in base_attributes else None,
                'capturable': base_attributes['capturable'] == '1' if 'capturable' in base_attributes else True,
                'bounds': [
                    [lat1, lng1],
                    [lat2, lng2]
                ]
            })

    def _parse_layer_group(self, group, group_name):
        """Parse a layer group."""
        group_id, game_type = group_name.split('.', maxsplit=1)

        for layer in group.iterchildren(Parser.nse('svg', 'g')):
            layer_name = layer.get(Parser.nse('inkscape', 'label'))

            if not layer_name: # We don't know what's this layer group: ignore it
                continue

            if layer_name == 'spawnpoints':
                self._parse_layer_group_spawnpoints(layer, group_id, game_type)
            elif layer_name == 'vehicles':
                self._parse_layer_group_vehicles(layer, group_id, game_type)

    def _parse_layer_group_spawnpoints(self, layer, group_id, game_type):
        """Parse the spawnpoints of a layer group."""
        if game_type not in self.data['spawn_points']['soldiers']:
            self.data['spawn_points']['soldiers'][game_type] = {}

        if group_id not in self.data['spawn_points']['soldiers'][game_type]:
            self.data['spawn_points']['soldiers'][game_type][group_id] = []

        for element in layer.iterchildren(Parser.nse('svg', 'rect')):
            lat = float(element.get('x'))
            lng = float(element.get('y'))

            self.data['spawn_points']['soldiers'][game_type][group_id].append([lat, lng])

    def _parse_layer_group_vehicles(self, layer, group_id, game_type):
        """Parse the spawnpoints of a layer group."""
        if game_type not in self.data['spawn_points']['vehicles']:
            self.data['spawn_points']['vehicles'][game_type] = {}

        if group_id not in self.data['spawn_points']['vehicles'][game_type]:
            self.data['spawn_points']['vehicles'][game_type][group_id] = []

        for element in layer.iterchildren(Parser.nse('svg', 'rect')):
            element_attributes = element.findtext('svg:desc', namespaces=self.namespaces)

            if not element_attributes:
                continue

            element_attributes = Parser.parse_attrs(element_attributes)

            if 'key' in element_attributes:
                vehicle_type = os.path.splitext(element_attributes['key'])[0]
            elif 'tag' in element_attributes:
                vehicle_type = element_attributes['tag']

            lat = float(element.get('x'))
            lng = float(element.get('y'))

            self.data['spawn_points']['vehicles'][game_type][group_id].append({
                'pos': [lat, lng],
                'type': vehicle_type
            })

    @staticmethod
    def nse(namespace, tag_name):
        """Return a namespaced XML element expression."""
        return '{{{}}}{}'.format(Parser.namespaces[namespace], tag_name)

    @staticmethod
    def parse_attrs(attributes):
        """Parse a map's semicolon-separated data and return its dict representation as key-value pairs."""
        return {entry[0]: entry[1] for entry in [[kv.strip() for kv in param.strip().split('=', maxsplit=1)] for param in filter(None, attributes.strip().split(';'))]}


# ----------------------------------------------------------------------

from pprint import pprint
from glob import glob

maps_paths = []

maps_paths.extend(glob('C:/Program Files (x86)/Steam/steamapps/common/RunningWithRifles/media/packages/*/maps/*/objects.svg'))
maps_paths.extend(glob('C:/Program Files (x86)/Steam/steamapps/workshop/content/270150/*/media/packages/*/maps/*/objects.svg'))

for maps_path in maps_paths:
    print(maps_path)

    map_parser = Parser(maps_path)

    data = map_parser.parse()

# map_parser = Parser('C:/Program Files (x86)/Steam/steamapps/common/RunningWithRifles/media/packages/vanilla/maps/map10/objects.svg')
# data = map_parser.parse()

# pprint(data)
