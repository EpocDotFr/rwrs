from collections import OrderedDict
from slugify import slugify
from lxml import etree
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
    def __init__(self, steam_dir):
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
        from PIL import Image

        minimaps_paths = []

        minimaps_paths.extend(glob(os.path.join(self.packages_dir, '*', 'maps', '*', 'map.png'))) # Maps in RWR game directory
        minimaps_paths.extend(glob(os.path.join(self.workshop_dir, '*', 'media', 'packages', '*', 'maps', '*', 'map.png'))) # Maps in RWR workshop directory

        for minimap_path in minimaps_paths:
            server_type, map_id = utils.parse_map_path(minimap_path.replace('\\', '/').replace('/map.png', ''))

            if not map_id or map_id in INVALID_MAPS or server_type in INVALID_GAME_TYPES:
                click.secho('Invalid map ID ({}) or server type ({})'.format(map_id, server_type), fg='yellow')

                continue

            click.echo(server_type + ':' + map_id)

            output_dir = os.path.join(app.config['MINIMAPS_IMAGES_DIR'], server_type)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            # Copy the original minimap first
            minimap = Image.open(minimap_path)
            minimap.save(os.path.join(output_dir, map_id + '.png'), optimize=True)

            # Create the thumbnail
            minimap.thumbnail(self.minimap_image_size, Image.LANCZOS)
            minimap.save(os.path.join(output_dir, map_id + '_thumb.png'), optimize=True)


class MapsDataExtractor(BaseExtractor):
    namespaces = {'svg': 'http://www.w3.org/2000/svg', 'inkscape': 'http://www.inkscape.org/namespaces/inkscape'}

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
                click.secho('Invalid map ID ({}) or server type ({})'.format(map_id, server_type), fg='yellow')

                continue

            self.map_xml = etree.parse(map_path)

            map_info_attributes = self.map_xml.findtext('//svg:rect[@inkscape:label=\'#general\']/svg:desc', namespaces=self.namespaces)

            if not map_info_attributes:
                click.secho('No general map info found', fg='yellow')

                continue

            map_info_attributes = self._parse_attributes(map_info_attributes)

            if 'name' not in map_info_attributes:
                click.secho('Map name not found', fg='yellow')

                continue

            click.echo(server_type + ':' + map_id)

            if server_type not in data:
                data[server_type] = OrderedDict()

            map_name = map_info_attributes['name'].replace('Pacific: ', '').title()

            data[server_type][map_id] = OrderedDict([
                ('name', map_name),
                ('slug', slugify(map_name)),
                ('has_minimap', os.path.isfile(os.path.join(app.config['MINIMAPS_IMAGES_DIR'], server_type, map_id + '.png'))),
                ('has_preview', os.path.isfile(os.path.join(app.config['MAPS_PREVIEW_IMAGES_DIR'], server_type, map_id + '.png')))
            ])

            self._extract_players_spawns(data[server_type][map_id])

        helpers.save_json(app.config['MAPS_DATA_FILE'], data)

    def _parse_attributes(self, attributes):
        """Parse a map's semicolon-separated data and return its dict representation as key-value pairs."""
        return {entry[0]: entry[1] for entry in [[kv.strip() for kv in param.strip().split('=', maxsplit=1)] for param in filter(None, attributes.strip().split(';'))]}

    def _extract_players_spawns(self, map_data):
        """Extract all players spawns."""
        print(self.map_xml.findall('//svg:g[@inkscape:label=\'spawnpoints\']/rect', namespaces=self.namespaces))


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
        from PIL import Image

        rank_image = Image.open(os.path.join(self.packages_dir, game_type, 'textures', filename))

        # Only get the actual content of the image
        rank_image = rank_image.crop(rank_image.convert('RGBa').getbbox())

        # Generate the desired images
        for image_size in self.images_sizes:
            click.echo(image_size['size'])

            desired_size_image = rank_image.copy()
            desired_size_image.thumbnail(image_size['size'], Image.LANCZOS)

            paste_pos = (
                math.floor(image_size['size'][0] / 2) - math.floor(desired_size_image.width / 2),
                math.floor(image_size['size'][1] / 2) - math.floor(desired_size_image.height / 2)
            )

            new_rank_image = Image.new('RGBA', image_size['size'])
            new_rank_image.paste(desired_size_image, paste_pos)

            new_rank_image_dir = os.path.join(app.config['RANKS_IMAGES_DIR'], country)

            if not os.path.isdir(new_rank_image_dir):
                os.makedirs(new_rank_image_dir)

            new_rank_image.save(os.path.join(new_rank_image_dir, image_size['name'](rank_id) + '.png'), optimize=True)


class UnlockablesExtractor(BaseExtractor):
    """Extract unlockables data and images from RWR."""
    radio_call_size = (64, 64)
    throwable_size = (48, 48)

    def extract(self):
        """Actually run the extract process."""
        data = OrderedDict()

        for game_type in VALID_GAME_TYPES:
            click.echo(game_type)

            data[game_type] = OrderedDict()

            self._extract_radio_calls(data[game_type], game_type)
            self._extract_throwables(data[game_type], game_type)
            self._extract_weapons(data[game_type], game_type)
            self._extract_equipment(data[game_type], game_type)

            data[game_type] = OrderedDict(sorted(data[game_type].items(), key=lambda k: k[0]))

        helpers.save_json(app.config['UNLOCKABLES_DATA_FILE'], data)

    def _extract_radio_calls(self, data, game_type):
        """Extract radio calls data and images from RWR."""
        from PIL import Image

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
                    click.secho('No applicable file found', fg='yellow')

                    continue

            click.echo(call_file)

            call_xml = etree.parse(call_file)
            call_xml_root = call_xml.getroot()

            if call_xml_root.tag == 'call':
                call_node = call_xml_root
            elif call_xml_root.tag == 'calls':
                call_node = call_xml_root.find('call[@radio_view_text]')

            capacity_node = call_node.find('capacity[@value="100"][@source="rank"]')
            hud_icon_node = call_node.find('hud_icon')

            if capacity_node is None or hud_icon_node is None or (not call_node.get('name') and not call_node.get('radio_view_text')):
                click.secho('Not usable', fg='yellow')

                continue

            call_xp = int(float(capacity_node.get('source_value')) * 10000)

            call = OrderedDict([
                ('name', call_node.get('name').title() if call_node.get('name') else call_node.get('radio_view_text').title()),
                ('image', call_node.get('key').replace('.call', ''))
            ])

            if call_xp not in data:
                data[call_xp] = OrderedDict()

            if 'radio_calls' not in data[call_xp]:
                data[call_xp]['radio_calls'] = []

            data[call_xp]['radio_calls'].append(call)

            call_image_file = os.path.join(self.packages_dir, game_type, 'textures', hud_icon_node.get('filename'))

            if not os.path.isfile(call_image_file) and game_type != 'vanilla': # Try to use call image inherited from Vanilla
                call_image_file = os.path.join(self.packages_dir, 'vanilla', 'textures', hud_icon_node.get('filename'))

                if not os.path.isfile(call_image_file):
                    click.secho('No applicable file found', fg='yellow')

                    continue

            call_image = Image.open(call_image_file)

            # Only get the actual content of the image
            call_image = call_image.crop(call_image.convert('RGBa').getbbox())

            call_image.thumbnail(self.radio_call_size, Image.LANCZOS)

            paste_pos = (
                math.floor(self.radio_call_size[0] / 2) - math.floor(call_image.width / 2),
                math.floor(self.radio_call_size[1] / 2) - math.floor(call_image.height / 2)
            )

            new_call_image = Image.new('RGBA', self.radio_call_size)
            new_call_image.paste(call_image, paste_pos)

            output_dir = os.path.join(app.config['UNLOCKABLES_IMAGES_DIR'], game_type, 'radio_calls')

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            new_call_image.save(os.path.join(output_dir, call['image'] + '.png'), optimize=True)

    def _extract_weapons(self, data, game_type):
        """Extract weapons data and images from RWR ."""
        click.echo('Extracting weapons')

        main_weapons_file = os.path.join(self.packages_dir, game_type, 'weapons', 'all_weapons.xml')
        weapons_directory = os.path.dirname(main_weapons_file)

        main_weapons_xml = etree.parse(main_weapons_file)
        main_weapons_xml_root = main_weapons_xml.getroot()

        for main_weapon_node in main_weapons_xml_root.iterchildren('weapon'):
            weapon_file = os.path.join(weapons_directory, main_weapon_node.get('file'))

            if not os.path.isfile(weapon_file) and game_type != 'vanilla': # Try to use weapon inherited from Vanilla
                weapon_file = os.path.join(self.packages_dir, 'vanilla', 'weapons', main_weapon_node.get('file'))

                if not os.path.isfile(weapon_file): # Abort as there's nothing we can do
                    click.secho('No applicable file found', fg='yellow')

                    continue

            click.echo(weapon_file)

            weapon_xml = etree.parse(weapon_file)
            weapon_xml_root = weapon_xml.getroot()

            specification_node = weapon_xml_root.find('specification')
            hud_icon_node = weapon_xml_root.find('hud_icon')

            if specification_node is None or hud_icon_node is None or not specification_node.get('name'):
                click.secho('Not usable', fg='yellow')

                continue

            weapon_name = specification_node.get('name').title()
            capacity_nodes = weapon_xml_root.xpath('capacity[@value!="0"][@source="rank"]')

            if capacity_nodes:
                for capacity_node in capacity_nodes:
                    weapon_xp = int(float(capacity_node.get('source_value')) * 10000)

                    weapon = OrderedDict([
                        ('name', weapon_name),
                        ('image', 'TODO')
                    ])

                    if int(capacity_node.get('value')) > 1:
                        weapon['amount'] = int(capacity_node.get('value'))

                    if weapon_xp not in data:
                        data[weapon_xp] = OrderedDict()

                    if 'weapons' not in data[weapon_xp]:
                        data[weapon_xp]['weapons'] = []

                    data[weapon_xp]['weapons'].append(weapon)

            # TODO

    def _extract_equipment(self, data, game_type):
        """Extract equipment data and images from RWR."""
        click.echo('Extracting equipment')

        # TODO Use weapons/all_weapons.xml

    def _extract_throwables(self, data, game_type):
        """Extract throwables data and images from RWR."""
        from PIL import Image

        click.echo('Extracting throwables')

        main_throwables_file = os.path.join(self.packages_dir, game_type, 'weapons', 'all_throwables.xml')
        throwables_directory = os.path.dirname(main_throwables_file)

        main_throwables_xml = etree.parse(main_throwables_file)
        main_throwables_xml_root = main_throwables_xml.getroot()

        for main_throwable_node in main_throwables_xml_root.iterchildren('projectile'):
            throwable_file = os.path.join(throwables_directory, main_throwable_node.get('file'))

            if not os.path.isfile(throwable_file) and game_type != 'vanilla': # Try to use throwable inherited from Vanilla
                throwable_file = os.path.join(self.packages_dir, 'vanilla', 'weapons', main_throwable_node.get('file'))

                if not os.path.isfile(throwable_file): # Abort as there's nothing we can do
                    click.secho('No applicable file found', fg='yellow')

                    continue

            click.echo(throwable_file)

            throwable_xml = etree.parse(throwable_file)
            throwable_xml_root = throwable_xml.getroot()

            capacity_nodes = throwable_xml_root.xpath('capacity[@value!="0"][@source="rank"]')
            hud_icon_node = throwable_xml_root.find('hud_icon')

            if not capacity_nodes or hud_icon_node is None or not throwable_xml_root.get('name'):
                click.secho('Not usable', fg='yellow')

                continue

            throwable_name = throwable_xml_root.get('name').title()
            throwable_image_name = throwable_xml_root.get('key').replace('.projectile', '')

            for capacity_node in capacity_nodes:
                throwable_xp = int(float(capacity_node.get('source_value')) * 10000)

                throwable = OrderedDict([
                    ('name', throwable_name),
                    ('image', throwable_image_name)
                ])

                if int(capacity_node.get('value')) > 1:
                    throwable['amount'] = int(capacity_node.get('value'))

                if throwable_xp not in data:
                    data[throwable_xp] = OrderedDict()

                if 'throwables' not in data[throwable_xp]:
                    data[throwable_xp]['throwables'] = []

                data[throwable_xp]['throwables'].append(throwable)

            throwable_image_file = os.path.join(self.packages_dir, game_type, 'textures', hud_icon_node.get('filename'))

            if not os.path.isfile(throwable_image_file) and game_type != 'vanilla': # Try to use call image inherited from Vanilla
                throwable_image_file = os.path.join(self.packages_dir, 'vanilla', 'textures', hud_icon_node.get('filename'))

                if not os.path.isfile(throwable_image_file):
                    click.secho('No applicable file found', fg='yellow')

                    continue

            throwable_image = Image.open(throwable_image_file)

            # Only get the actual content of the image
            throwable_image = throwable_image.crop(throwable_image.convert('RGBa').getbbox())

            throwable_image.thumbnail(self.throwable_size, Image.LANCZOS)

            paste_pos = (
                math.floor(self.throwable_size[0] / 2) - math.floor(throwable_image.width / 2),
                math.floor(self.throwable_size[1] / 2) - math.floor(throwable_image.height / 2)
            )

            new_throwable_image = Image.new('RGBA', self.throwable_size)
            new_throwable_image.paste(throwable_image, paste_pos)

            output_dir = os.path.join(app.config['UNLOCKABLES_IMAGES_DIR'], game_type, 'throwables')

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            new_throwable_image.save(os.path.join(output_dir, throwable_image_name + '.png'), optimize=True)
