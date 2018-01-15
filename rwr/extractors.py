from collections import OrderedDict
from glob import glob
from rwrs import app
from . import utils
import helpers
import click
import math
import os


VALID_GAME_TYPES = ['vanilla', 'pacific']
INVALID_GAME_TYPES = ['teddy_hunt']
INVALID_MAPS = ['lobby']


class BaseExtractor:
    def __init__(self, steam_dir, output_location):
        self.steam_dir = steam_dir
        self.output_location = output_location

        if not os.path.isdir(self.steam_dir):
            raise FileNotFoundError(self.steam_dir + ' does not exists')

        if not os.path.exists(self.output_location):
            raise FileNotFoundError(self.output_location + ' does not exists')

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
        from PIL import Image

        minimaps_paths = []

        minimaps_paths.extend(glob(os.path.join(self.packages_dir, '*', 'maps', '*', 'map.png'))) # Maps in RWR game directory
        minimaps_paths.extend(glob(os.path.join(self.workshop_dir, '*', 'media', 'packages', '*', 'maps', '*', 'map.png'))) # Maps in RWR workshop directory

        for minimap_path in minimaps_paths:
            server_type, map_id = utils.parse_map_path(minimap_path.replace('\\', '/').replace('/map.png', ''))

            if not map_id or map_id in INVALID_MAPS or server_type in INVALID_GAME_TYPES:
                continue

            click.echo(server_type + ':' + map_id)

            output_dir = os.path.join(self.output_location, server_type)

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
        from lxml import etree

        maps_paths = []

        maps_paths.extend(glob(os.path.join(self.packages_dir, '*', 'maps', '*', 'objects.svg'))) # Maps in RWR game directory
        maps_paths.extend(glob(os.path.join(self.workshop_dir, '*', 'media', 'packages', '*', 'maps', '*', 'objects.svg'))) # Maps in RWR workshop directory

        data = OrderedDict()

        for map_path in maps_paths:
            server_type, map_id = utils.parse_map_path(map_path.replace('\\', '/').replace('/objects.svg', ''))

            if not map_id or map_id in INVALID_MAPS or server_type in INVALID_GAME_TYPES:
                continue

            map_xml = etree.parse(map_path)

            map_infos = map_xml.xpath('//svg:rect[@inkscape:label=\'#general\']/svg:desc/text()', namespaces={'svg': 'http://www.w3.org/2000/svg', 'inkscape': 'http://www.inkscape.org/namespaces/inkscape'})

            if not map_infos:
                continue

            map_infos = map_infos[0]
            map_infos = self._parse_map_data(map_infos)

            if 'name' not in map_infos:
                continue

            click.echo(server_type + ':' + map_id)

            if server_type not in data:
                data[server_type] = OrderedDict()

            data[server_type][map_id] = {
                'name': map_infos['name'].replace('Pacific: ', '').title(),
                'has_minimap': os.path.isfile(os.path.join(app.config['MINIMAPS_IMAGES_DIR'], server_type, map_id + '.png')),
                'has_preview': os.path.isfile(os.path.join(app.config['MAPS_PREVIEW_IMAGES_DIR'], server_type, map_id + '.png'))
            }

        helpers.save_json(self.output_location, data)

    def _parse_map_data(self, map_infos):
        """Parse a map's semicolon-separated data and return its dict representation as key-value pairs."""
        return {entry[0]: entry[1] for entry in [[kv.strip() for kv in param.strip().split('=', maxsplit=1)] for param in filter(None, map_infos.strip().split(';'))]}


class RanksDataExtractor(BaseExtractor):
    """Extract ranks data from RWR."""
    def extract(self):
        """Actually run the extract process."""
        from lxml import etree

        # Only take official ranks data
        ranks_files_paths = {
            'us': os.path.join(self.packages_dir, 'vanilla', 'factions', 'brown.xml'), # In Vanilla, ranks from all factions are the same, inspired by the US Army
            'jp': os.path.join(self.packages_dir, 'pacific', 'factions', 'ija.xml') # In Pacific, US factions are the same as the Vanilla ones, so only parse IJA ranks
        }

        data = OrderedDict()

        for country, ranks_file_path in ranks_files_paths.items():
            click.echo(country)

            data[country] = OrderedDict()

            faction_xml = etree.parse(ranks_file_path)

            i = 0

            for rank_node in faction_xml.xpath('/faction/rank'):
                rank_name = rank_node.get('name')

                click.echo(rank_name)

                data[country][i] = {'name': rank_name, 'xp': int(float(rank_node.get('xp')) * 10000)}

                i += 1

        helpers.save_json(self.output_location, data)


class RanksImageExtractor(BaseExtractor):
    """Extract ranks images from RWR."""
    desired_sizes = [
        {
            'name': lambda rank_id: rank_id,
            'size': (64, 64)
        },
        {
            'name': lambda rank_id: rank_id + '_icon',
            'size': (20, 20)
        }
    ]

    def extract(self):
        """Actually run the extract process."""
        from PIL import Image

        ranks_paths = []

        # Only take official ranks images
        for type in ['vanilla', 'pacific']:
            ranks_paths.extend(glob(os.path.join(self.packages_dir, 'vanilla', 'textures', 'hud_rank*.png')))

        for rank_path in ranks_paths:
            click.echo(rank_path)

            server_type, rank_id = utils.parse_rank_path(rank_path.replace('\\', '/'))

            if server_type == 'vanilla':
                country = 'us'
            elif server_type == 'pacific':
                country = 'jp'

            rank_image = Image.open(rank_path)

            # Only get the actual content of the image
            rank_image = rank_image.crop(rank_image.convert('RGBa').getbbox())

            # Generate the desired images
            for desired_size in self.desired_sizes:
                click.echo(desired_size['size'])

                desired_size_image = rank_image.copy()
                desired_size_image.thumbnail(desired_size['size'], Image.ANTIALIAS)

                paste_pos = (
                    math.floor(desired_size['size'][0] / 2) - math.floor(desired_size_image.width / 2),
                    math.floor(desired_size['size'][1] / 2) - math.floor(desired_size_image.height / 2)
                )

                new_rank_image = Image.new('RGBA', desired_size['size'])
                new_rank_image.paste(desired_size_image, paste_pos)
                new_rank_image.save(os.path.join(self.output_location, country, desired_size['name'](rank_id) + '.png'), optimize=True)
