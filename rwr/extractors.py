from collections import OrderedDict
from lxml import etree
from PIL import Image
from glob import glob
from rwrs import app
from . import utils
import helpers
import click
import math
import os


VALID_GAME_TYPES = ['vanilla', 'pacific']
INVALID_GAME_TYPES = ['teddy_hunt', 'minimodes', 'man_vs_world']
INVALID_MAPS = ['lobby']


class BaseExtractor:
    def __init__(self, steam_dir,):
        self.steam_dir = steam_dir

        if not os.path.isdir(self.steam_dir):
            raise FileNotFoundError(self.steam_dir + ' does not exists')

        self.game_dir = os.path.join(self.steam_dir, 'steamapps', 'common', 'RunningWithRifles')
        self.workshop_dir = os.path.join(self.steam_dir, 'steamapps', 'workshop', 'content', str(app.config['RWR_STEAM_APP_ID']))
        self.packages_dir = os.path.join(self.game_dir, 'media', 'packages')

    def extract(self):
        raise NotImplemented('Must be implemented')


class MinimapsImageExtractor(BaseExtractor):
    """Extract minimaps from RWR."""
    minimap_image_size = (320, 320)

    def extract(self):
        """Actually run the extract process."""
        minimaps_paths = []

        minimaps_paths.extend(glob(os.path.join(self.packages_dir, '*', 'maps', '*', 'map.png'))) # Maps in RWR game directory
        minimaps_paths.extend(glob(os.path.join(self.workshop_dir, '*', 'media', 'packages', '*', 'maps', '*', 'map.png'))) # Maps in RWR workshop directory

        for minimap_path in minimaps_paths:
            server_type, map_id = utils.parse_map_path(minimap_path.replace('\\', '/').replace('/map.png', ''))

            if not map_id or map_id in INVALID_MAPS or server_type in INVALID_GAME_TYPES:
                continue

            click.echo(server_type + ':' + map_id)

            output_dir = os.path.join(app.config['MINIMAPS_IMAGES_DIR'], server_type)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            # Copy the original minimap first
            minimap = Image.open(minimap_path)
            minimap.save(os.path.join(output_dir, map_id + '.png'), optimize=True)

            # Create the thumbnail
            minimap.thumbnail(self.minimap_image_size, Image.ANTIALIAS)
            minimap.save(os.path.join(output_dir, map_id + '_thumb.png'), optimize=True)


class MapsDataExtractor(BaseExtractor):
    """Extract maps data from RWR."""
    def extract(self):
        """Actually run the extract process."""
        maps_paths = []

        maps_paths.extend(glob(os.path.join(self.packages_dir, '*', 'maps', '*', 'objects.svg'))) # Maps in RWR game directory
        maps_paths.extend(glob(os.path.join(self.workshop_dir, '*', 'media', 'packages', '*', 'maps', '*', 'objects.svg'))) # Maps in RWR workshop directory

        data = OrderedDict()

        for map_path in maps_paths:
            server_type, map_id = utils.parse_map_path(map_path.replace('\\', '/').replace('/objects.svg', ''))

            if not map_id or map_id in INVALID_MAPS or server_type in INVALID_GAME_TYPES:
                continue

            map_xml = etree.parse(map_path)

            map_infos = map_xml.findtext('//svg:rect[@inkscape:label=\'#general\']/svg:desc', namespaces={'svg': 'http://www.w3.org/2000/svg', 'inkscape': 'http://www.inkscape.org/namespaces/inkscape'})

            if not map_infos:
                continue

            map_infos = self._parse_map_data(map_infos)

            if 'name' not in map_infos:
                continue

            click.echo(server_type + ':' + map_id)

            if server_type not in data:
                data[server_type] = OrderedDict()

            data[server_type][map_id] = OrderedDict([
                ('name', map_infos['name'].replace('Pacific: ', '').title()),
                ('has_minimap', os.path.isfile(os.path.join(app.config['MINIMAPS_IMAGES_DIR'], server_type, map_id + '.png'))),
                ('has_preview', os.path.isfile(os.path.join(app.config['MAPS_PREVIEW_IMAGES_DIR'], server_type, map_id + '.png')))
            ])

        helpers.save_json(app.config['MAPS_DATA_FILE'], data)

    def _parse_map_data(self, map_infos):
        """Parse a map's semicolon-separated data and return its dict representation as key-value pairs."""
        return {entry[0]: entry[1] for entry in [[kv.strip() for kv in param.strip().split('=', maxsplit=1)] for param in filter(None, map_infos.strip().split(';'))]}


class RanksExtractor(BaseExtractor):
    """Extract ranks data and images from RWR."""
    images_sizes = [
        {
            'name': lambda rank_id: str(rank_id),
            'size': (64, 64)
        },
        {
            'name': lambda rank_id: str(rank_id) + '_icon',
            'size': (20, 20)
        }
    ]

    def extract(self):
        """Actually run the extract process."""
        # Only handle official ranks
        ranks_files_paths = [
            { # In Vanilla, ranks from all factions are the same, inspired from the US Army
                'country': 'us',
                'path': os.path.join(self.packages_dir, 'vanilla', 'factions', 'brown.xml'),
                'game_type': 'vanilla'
            },
            { # In Pacific, US factions are the same as the Vanilla ones, so only parse IJA ranks
                'country': 'jp',
                'path': os.path.join(self.packages_dir, 'pacific', 'factions', 'ija.xml'),
                'game_type': 'pacific'
            }
        ]

        data = OrderedDict()

        for ranks_file_path in ranks_files_paths:
            click.echo(ranks_file_path['country'])

            data[ranks_file_path['country']] = OrderedDict()

            faction_xml = etree.parse(ranks_file_path['path'])
            faction_xml_root = faction_xml.getroot()

            i = 0

            for rank_node in faction_xml_root.iterchildren('rank'):
                rank_name = rank_node.get('name')

                click.echo(rank_name)

                data[ranks_file_path['country']][i] = OrderedDict([
                    ('name', rank_name),
                    ('xp', int(float(rank_node.get('xp')) * 10000))
                ])

                self._extract_images(i, ranks_file_path['game_type'], ranks_file_path['country'], rank_node.find('hud_icon').get('filename'))

                i += 1

        helpers.save_json(app.config['RANKS_DATA_FILE'], data)

    def _extract_images(self, rank_id, game_type, country, filename):
        rank_image = Image.open(os.path.join(self.packages_dir, game_type, 'textures', filename))

        # Only get the actual content of the image
        rank_image = rank_image.crop(rank_image.convert('RGBa').getbbox())

        # Generate the desired images
        for image_size in self.images_sizes:
            click.echo(image_size['size'])

            desired_size_image = rank_image.copy()
            desired_size_image.thumbnail(image_size['size'], Image.ANTIALIAS)

            paste_pos = (
                math.floor(image_size['size'][0] / 2) - math.floor(desired_size_image.width / 2),
                math.floor(image_size['size'][1] / 2) - math.floor(desired_size_image.height / 2)
            )

            new_rank_image = Image.new('RGBA', image_size['size'])
            new_rank_image.paste(desired_size_image, paste_pos)
            new_rank_image.save(os.path.join(app.config['RANKS_IMAGES_DIR'], country, image_size['name'](rank_id) + '.png'), optimize=True)


class UnlockablesExtractor(BaseExtractor):
    """Extract unlockables data and images from RWR."""
    radio_call_size = (64, 64)

    def extract(self):
        """Actually run the extract process."""
        data = OrderedDict()

        for game_type in VALID_GAME_TYPES:
            click.echo(game_type)

            data[game_type] = OrderedDict()

            self._extract_radio_calls(data[game_type], game_type)

            # TODO Implement the others

            data[game_type] = OrderedDict(sorted(data[game_type].items(), key=lambda k: k[0]))

        helpers.save_json(app.config['UNLOCKABLES_DATA_FILE'], data)

    def _extract_radio_calls(self, data, game_type):
        """Extract radio calls data and images from RWR."""
        click.echo('Extracting radio calls')

        main_calls_file = os.path.join(self.packages_dir, game_type, 'calls', 'all_calls.xml')
        calls_directory = os.path.dirname(main_calls_file)

        main_calls_xml = etree.parse(main_calls_file)
        main_calls_xml_root = main_calls_xml.getroot()

        for main_call_node in main_calls_xml_root.iterchildren('call'):
            call_file = os.path.join(calls_directory, main_call_node.get('file'))

            if not os.path.isfile(call_file) and game_type != 'vanilla': # Try to use call inherited from Vanilla
                call_file = os.path.join(self.packages_dir, 'vanilla', 'calls', main_call_node.get('file'))

                if not os.path.isfile(call_file): # Abort as there's nothing we can do
                    continue

            click.echo(call_file)
            click.echo('Data')

            call_xml = etree.parse(call_file)
            call_xml_root = call_xml.getroot()

            if call_xml_root.tag == 'call':
                call_node = call_xml_root
            elif call_xml_root.tag == 'calls':
                call_node = call_xml_root.find('call[@radio_view_text]')

            call_xp = int(float(call_node.find('capacity[@value="100"][@source="rank"]').get('source_value')) * 10000)

            call = OrderedDict([
                ('name', call_node.get('name').title() if call_node.get('name') else call_node.get('radio_view_text').title()),
                ('image', call_node.get('key').replace('.call', ''))
            ])

            if call_xp not in data:
                data[call_xp] = {}

            if 'radio_calls' not in data[call_xp]:
                data[call_xp]['radio_calls'] = []

            data[call_xp]['radio_calls'].append(call)

            click.echo('Image')

            call_image_file = os.path.join(self.packages_dir, game_type, 'textures', call_node.find('hud_icon').get('filename'))

            if not os.path.isfile(call_image_file) and game_type != 'vanilla': # Try to use call image inherited from Vanilla
                call_image_file = os.path.join(self.packages_dir, 'vanilla', 'textures', call_node.find('hud_icon').get('filename'))

                if not os.path.isfile(call_image_file):
                    continue

            call_image = Image.open(call_image_file)

            # Only get the actual content of the image
            call_image = call_image.crop(call_image.convert('RGBa').getbbox())

            call_image.thumbnail(self.radio_call_size, Image.ANTIALIAS)

            paste_pos = (
                math.floor(self.radio_call_size[0] / 2) - math.floor(call_image.width / 2),
                math.floor(self.radio_call_size[1] / 2) - math.floor(call_image.height / 2)
            )

            new_rank_image = Image.new('RGBA', self.radio_call_size)
            new_rank_image.paste(call_image, paste_pos)

            output_dir = os.path.join(app.config['UNLOCKABLES_IMAGES_DIR'], game_type, 'radio_calls')

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            new_rank_image.save(os.path.join(output_dir, call['image'] + '.png'), optimize=True)

    def _extract_weapons(self):
        """Extract weapons data and images from RWR ."""
        click.echo('Extracting weapons')

        # TODO Use weapons/all_weapons.xml

    def _extract_equipment(self):
        """Extract equipment data and images from RWR."""
        click.echo('Extracting equipment')

        # TODO Use weapons/all_weapons.xml

    def _extract_throwables(self):
        """Extract throwables data and images from RWR."""
        click.echo('Extracting throwables')

        # TODO Use weapons/all_throwables.xml
