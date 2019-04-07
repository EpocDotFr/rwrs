from collections import OrderedDict
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
        """Actually run the extraction process."""
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
    """Extract maps data from RWR."""
    def extract(self):
        """Actually run the extraction process."""
        maps_paths = []

        maps_paths.extend(glob(os.path.join(self.packages_dir, '*', 'maps', '*', 'objects.svg'))) # Maps in RWR game directory
        maps_paths.extend(glob(os.path.join(self.workshop_dir, '*', 'media', 'packages', '*', 'maps', '*', 'objects.svg'))) # Maps in RWR workshop directory

        data = OrderedDict()

        for map_path in maps_paths:
            server_type, map_id = utils.parse_map_path(map_path.replace('\\', '/').replace('/objects.svg', ''))

            if not map_id or map_id in INVALID_MAPS or server_type in INVALID_GAME_TYPES:
                click.secho('Invalid map ID ({}) or server type ({})'.format(map_id, server_type), fg='yellow')

                continue

            map_xml = etree.parse(map_path)

            map_infos = map_xml.findtext('//svg:rect[@inkscape:label=\'#general\']/svg:desc', namespaces={'svg': 'http://www.w3.org/2000/svg', 'inkscape': 'http://www.inkscape.org/namespaces/inkscape'})

            if not map_infos:
                click.secho('No general map info found', fg='yellow')

                continue

            map_infos = self._parse_map_data(map_infos)

            if 'name' not in map_infos:
                click.secho('Map name not found', fg='yellow')

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
        """Actually run the extraction process."""
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


class ItemsExtractor(BaseExtractor):
    """Extract items data and images from RWR."""
    images_size = (270, 80)
    do_not_rotate_images_for = [
        # Vanilla
        'tti',
        # Pacific
        'binoculars',
        'medikit',
        'morphine'
    ]

    def extract(self):
        """Actually run the extraction process."""
        data = OrderedDict()

        for game_type in VALID_GAME_TYPES:
            click.echo(game_type)

            data[game_type] = OrderedDict()

            self._extract_weapons(game_type, data[game_type])
            self._extract_throwables(game_type, data[game_type])
            self._extract_carry_items(game_type, data[game_type])

        helpers.save_json(app.config['ITEMS_DATA_FILE'], data)

    def _extract_weapons(self, game_type, data):
        """Extract weapons data and images from RWR ."""
        from PIL import Image

        click.echo('  Extracting weapons')

        weapons_directory = os.path.join(self.packages_dir, game_type, 'weapons')
        all_weapons_file = os.path.join(weapons_directory, 'all_weapons.xml')

        all_weapons_xml = etree.parse(all_weapons_file)
        all_weapons_xml_root = all_weapons_xml.getroot()

        for weapon_node in all_weapons_xml_root.iterchildren('weapon'):
            weapon_file_name = weapon_node.get('file')
            weapon_file = os.path.join(weapons_directory, weapon_file_name)

            if not os.path.isfile(weapon_file) and game_type != 'vanilla': # Try to use weapon inherited from Vanilla
                weapon_file = os.path.join(self.packages_dir, 'vanilla', 'weapons', weapon_file_name)

                if not os.path.isfile(weapon_file): # Abort as there's nothing we can do
                    click.secho('    No applicable file found for {}'.format(weapon_file), fg='yellow')

                    continue

            click.echo('    ' + weapon_file)

            weapon_id = os.path.splitext(os.path.basename(weapon_file_name))[0]

            weapon_xml = etree.parse(weapon_file)
            weapon_xml_root = weapon_xml.getroot()

            specification_node = weapon_xml_root.find('specification')

            if specification_node is None:
                click.secho('      specification node not found', fg='yellow')

                continue

            weapon_slot = specification_node.get('slot')

            if weapon_slot:
                weapon_slot = int(weapon_slot)

                if weapon_slot == 0:
                    weapon_slot = 'primary'
                elif weapon_slot == 1:
                    weapon_slot = 'secondary'
                elif weapon_slot == 2:
                    click.secho('      Static / mounted weapon', fg='yellow')

                    continue
            else:
                weapon_slot = 'primary'

            commonness_node = weapon_xml_root.find('commonness')

            if commonness_node is not None and (not commonness_node.get('can_respawn_with') or (commonness_node.get('can_respawn_with') and int(commonness_node.get('can_respawn_with')) == 1)):
                click.secho('      Not a rare weapon', fg='yellow')

                continue

            hud_icon_node = weapon_xml_root.find('hud_icon')

            if hud_icon_node is None:
                click.secho('      hud_icon node not found', fg='yellow')

                continue

            if not specification_node.get('name'):
                click.secho('      No name set', fg='yellow')

                continue

            if not hud_icon_node.get('filename'):
                click.secho('      No HUD icon set', fg='yellow')

                continue

            weapon_name = specification_node.get('name')

            inventory_node = weapon_xml_root.find('inventory')
            weapon_price = int(float(inventory_node.get('price'))) if inventory_node is not None else 0

            if weapon_slot not in data:
                data[weapon_slot] = OrderedDict()

            data[weapon_slot][weapon_id] = OrderedDict([
                ('name', weapon_name),
                ('price', weapon_price)
            ])

            weapon_image_file_name = hud_icon_node.get('filename')
            weapon_image_file = os.path.join(self.packages_dir, game_type, 'textures', weapon_image_file_name)

            if not os.path.isfile(weapon_image_file) and game_type != 'vanilla': # Try to use weapon image inherited from Vanilla
                weapon_image_file = os.path.join(self.packages_dir, 'vanilla', 'textures', weapon_image_file_name)

                if not os.path.isfile(weapon_image_file):
                    click.secho('      No applicable image found for {}'.format(weapon_file), fg='yellow')

                    continue

            weapon_image = Image.open(weapon_image_file)

            # Only get the actual content of the image
            weapon_image = weapon_image.crop(weapon_image.convert('RGBa').getbbox())

            if not weapon_id.endswith('_resource') and weapon_id not in self.do_not_rotate_images_for:
                weapon_image = weapon_image.transpose(Image.ROTATE_270)

            weapon_image.thumbnail(self.images_size, Image.LANCZOS)

            output_dir = os.path.join(app.config['ITEMS_IMAGES_DIR'], game_type, weapon_slot)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            weapon_image.save(os.path.join(output_dir, weapon_id + '.png'), optimize=True)

    def _extract_throwables(self, game_type, data):
        """Extract throwable data and images from RWR ."""
        from PIL import Image

        click.echo('  Extracting throwables')

        weapons_directory = os.path.join(self.packages_dir, game_type, 'weapons')
        all_throwables_file = os.path.join(weapons_directory, 'all_throwables.xml')

        all_throwables_xml = etree.parse(all_throwables_file)
        all_throwables_xml_root = all_throwables_xml.getroot()

        for throwable_node in all_throwables_xml_root.iterchildren('projectile'):
            throwable_file_name = throwable_node.get('file')
            throwable_file = os.path.join(weapons_directory, throwable_file_name)

            if not os.path.isfile(throwable_file) and game_type != 'vanilla': # Try to use throwable inherited from Vanilla
                throwable_file = os.path.join(self.packages_dir, 'vanilla', 'weapons', throwable_file_name)

                if not os.path.isfile(throwable_file): # Abort as there's nothing we can do
                    click.secho('    No applicable file found for {}'.format(throwable_file), fg='yellow')

                    continue

            click.echo('    ' + throwable_file)

            throwable_id = os.path.splitext(os.path.basename(throwable_file_name))[0]

            throwable_xml = etree.parse(throwable_file)
            throwable_xml_root = throwable_xml.getroot()

            throwable_slot = throwable_xml_root.get('slot')

            if throwable_slot:
                throwable_slot = int(throwable_slot)

                if throwable_slot != 0:
                    click.secho('      System projectile', fg='yellow')

                    continue

            commonness_node = throwable_xml_root.find('commonness')

            if commonness_node is not None and (not commonness_node.get('can_respawn_with') or (commonness_node.get('can_respawn_with') and int(commonness_node.get('can_respawn_with')) == 1)):
                click.secho('      Not a rare throwable', fg='yellow')

                continue

            hud_icon_node = throwable_xml_root.find('hud_icon')

            if hud_icon_node is None:
                click.secho('      hud_icon node not found', fg='yellow')

                continue

            if not throwable_xml_root.get('name'):
                click.secho('      No name set', fg='yellow')

                continue

            if not hud_icon_node.get('filename'):
                click.secho('      No HUD icon set', fg='yellow')

                continue

            throwable_name = throwable_xml_root.get('name')

            inventory_node = throwable_xml_root.find('inventory')
            throwable_price = int(float(inventory_node.get('price'))) if inventory_node is not None else 0

            if 'throwables' not in data:
                data['throwables'] = OrderedDict()

            data['throwables'][throwable_id] = OrderedDict([
                ('name', throwable_name),
                ('price', throwable_price)
            ])

            throwable_image_file_name = hud_icon_node.get('filename')
            throwable_image_file = os.path.join(self.packages_dir, game_type, 'textures', throwable_image_file_name)

            if not os.path.isfile(throwable_image_file) and game_type != 'vanilla': # Try to use throwable image inherited from Vanilla
                throwable_image_file = os.path.join(self.packages_dir, 'vanilla', 'textures', throwable_image_file_name)

                if not os.path.isfile(throwable_image_file):
                    click.secho('      No applicable image found for {}'.format(throwable_file), fg='yellow')

                    continue

            throwable_image = Image.open(throwable_image_file)

            # Only get the actual content of the image
            throwable_image = throwable_image.crop(throwable_image.convert('RGBa').getbbox())
            throwable_image.thumbnail(self.images_size, Image.LANCZOS)

            output_dir = os.path.join(app.config['ITEMS_IMAGES_DIR'], game_type, 'throwables')

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            throwable_image.save(os.path.join(output_dir, throwable_id + '.png'), optimize=True)

    def _extract_carry_items(self, game_type, data):
        """Extract carry items data and images from RWR ."""
        from PIL import Image

        click.echo('  Extracting carry items')

        carry_items_directory = os.path.join(self.packages_dir, game_type, 'items')
        all_carry_items_file = os.path.join(carry_items_directory, 'all_carry_items.xml')

        all_carry_items_xml = etree.parse(all_carry_items_file)
        all_carry_items_xml_root = all_carry_items_xml.getroot()

        for carry_item_node in all_carry_items_xml_root.iterchildren('carry_item'):
            carry_item_file_name = carry_item_node.get('file')
            carry_item_file = os.path.join(carry_items_directory, carry_item_file_name)

            if not os.path.isfile(carry_item_file) and game_type != 'vanilla': # Try to use carry item inherited from Vanilla
                carry_item_file = os.path.join(self.packages_dir, 'vanilla', 'items', carry_item_file_name)

                if not os.path.isfile(carry_item_file): # Abort as there's nothing we can do
                    click.secho('    No applicable file found for {}'.format(carry_item_file), fg='yellow')

                    continue

            click.echo('    ' + carry_item_file)

            carry_item_id = os.path.splitext(os.path.basename(carry_item_file_name))[0]

            carry_item_xml = etree.parse(carry_item_file)
            carry_item_xml_root = carry_item_xml.getroot()

            carry_item_slot = carry_item_xml_root.get('slot')

            if carry_item_slot:
                carry_item_slot = int(carry_item_slot)

                if carry_item_slot == 0:
                    carry_item_slot = 'valuable'
                elif carry_item_slot == 1:
                    carry_item_slot = 'wearable'
            else:
                carry_item_slot = 'valuable'

            commonness_node = carry_item_xml_root.find('commonness')

            # FIXME can_respawn_with is defined in base_valuable.carry_item
            if commonness_node is not None and (not commonness_node.get('can_respawn_with') or (commonness_node.get('can_respawn_with') and int(commonness_node.get('can_respawn_with')) == 1)):
                click.secho('      Not a rare carry item', fg='yellow')

                continue

            hud_icon_node = carry_item_xml_root.find('hud_icon')

            if hud_icon_node is None:
                click.secho('      hud_icon node not found', fg='yellow')

                continue

            if not carry_item_xml_root.get('name'):
                click.secho('      No name set', fg='yellow')

                continue

            if not hud_icon_node.get('filename'):
                click.secho('      No HUD icon set', fg='yellow')

                continue

            carry_item_name = carry_item_xml_root.get('name')

            inventory_node = carry_item_xml_root.find('inventory')
            carry_item_price = int(float(inventory_node.get('price'))) if inventory_node is not None else 0

            if carry_item_slot not in data:
                data[carry_item_slot] = OrderedDict()

            data[carry_item_slot][carry_item_id] = OrderedDict([
                ('name', carry_item_name),
                ('price', carry_item_price)
            ])

            carry_item_image_file_name = hud_icon_node.get('filename')
            carry_item_image_file = os.path.join(self.packages_dir, game_type, 'textures', carry_item_image_file_name)

            if not os.path.isfile(carry_item_image_file) and game_type != 'vanilla': # Try to use carry item image inherited from Vanilla
                carry_item_image_file = os.path.join(self.packages_dir, 'vanilla', 'textures', carry_item_image_file_name)

                if not os.path.isfile(carry_item_image_file):
                    click.secho('      No applicable image found for {}'.format(carry_item_file), fg='yellow')

                    continue

            carry_item_image = Image.open(carry_item_image_file)

            # Only get the actual content of the image
            carry_item_image = carry_item_image.crop(carry_item_image.convert('RGBa').getbbox())
            carry_item_image.thumbnail(self.images_size, Image.LANCZOS)

            output_dir = os.path.join(app.config['ITEMS_IMAGES_DIR'], game_type, carry_item_slot)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            carry_item_image.save(os.path.join(output_dir, carry_item_id + '.png'), optimize=True)
