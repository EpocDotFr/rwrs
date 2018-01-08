from glob import glob
from . import utils
import math
import os


class BaseExtractor:
    def __init__(self, game_dir, output_dir):
        self.game_dir = game_dir
        self.output_dir = output_dir

        if not os.path.isdir(self.game_dir):
            raise FileNotFoundError(self.game_dir + ' does not exists')

        if not os.path.isdir(self.output_dir):
            raise FileNotFoundError(self.output_dir + ' does not exists')

        self.packages_dir = os.path.join(self.game_dir, 'media/packages')

    def extract(self):
        raise NotImplemented('Must be implemented')


class MinimapsImageExtractor(BaseExtractor):
    minimap_image_size = (320, 320)

    def extract(self):
        """Actually run the extract process."""
        from PIL import Image

        minimaps_paths = []

        for type in ['vanilla', 'pacific']:
            minimaps_paths.extend(glob(os.path.join(self.packages_dir, type, 'maps', '*', 'map.png')))

        for minimap_path in minimaps_paths:
            server_type, map_id = utils.parse_map_path(minimap_path.replace('\\', '/').replace('/map.png', ''))

            if not map_id or map_id == 'lobby' or server_type == 'teddy_hunt':
                continue

            # Copy the original minimap first
            minimap = Image.open(minimap_path)
            minimap.save(os.path.join(self.output_dir, server_type, map_id + '.png'), optimize=True)

            # Create the thumbnail
            minimap.thumbnail(self.minimap_image_size, Image.ANTIALIAS)
            minimap.save(os.path.join(self.output_dir, server_type, map_id + '_thumb.png'), optimize=True)


class RanksImageExtractor(BaseExtractor):
    needed_sizes = [
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

        for type in ['vanilla', 'pacific']:
            ranks_paths.extend(glob(os.path.join(self.packages_dir, 'vanilla', 'textures', 'hud_rank*.png')))

        for rank_path in ranks_paths:
            server_type, rank_id = utils.parse_rank_path(rank_path.replace('\\', '/'))

            if server_type == 'vanilla':
                country = 'us'
            elif server_type == 'pacific':
                country = 'jp'

            rank_image = Image.open(rank_path)

            # Only get the actual content of the image
            rank_image = rank_image.crop(rank_image.convert('RGBa').getbbox())

            # Generate the needed images
            for needed_size in self.needed_sizes:
                needed_size_image = rank_image.copy()
                needed_size_image.thumbnail(needed_size['size'], Image.ANTIALIAS)

                paste_pos = (
                    math.floor(needed_size['size'][0] / 2) - math.floor(needed_size_image.width / 2),
                    math.floor(needed_size['size'][1] / 2) - math.floor(needed_size_image.height / 2)
                )

                new_rank_image = Image.new('RGBA', needed_size['size'])
                new_rank_image.paste(needed_size_image, paste_pos)
                new_rank_image.save(os.path.join(self.output_dir, country, needed_size['name'](rank_id) + '.png'), optimize=True)
