from PIL import Image, ImageDraw, ImageFont
from flask import make_response
from io import BytesIO
import rwr.utils
import helpers
import arrow


font_path = 'static/fonts/komikax.ttf'

big_font = ImageFont.truetype(font_path, 15)
normal_font = ImageFont.truetype(font_path, 12)
small_font = ImageFont.truetype(font_path, 10)

dark_grey = (51, 51, 51)
white = (255, 255, 255)
green = (164, 207, 23)


class DynamicImage:
    """A dynamic image."""
    def init(self, background_path):
        self.image = Image.open(background_path).convert('RGBA')
        self.image_draw = ImageDraw.Draw(self.image)

    @classmethod
    def create(cls, *args):
        """Create a new dynamic image for "entity" and send it to the client."""
        ret = cls(*args)

        ret.do_create()
        ret.render()

        return ret.send()

    def render(self):
        """Render the final dynamic image."""
        self.final_image = BytesIO()

        self.image.save(self.final_image, format='png', optimize=True)

        self.final_image.seek(0)

    def send(self):
        """Send the final rendered dynamic image to the client."""
        response = make_response(self.final_image.getvalue())

        response.headers.set('Content-Type', 'image/png')
        response.last_modified = arrow.now().datetime

        return response

    def do_create(self):
        """Actually create the dynamic image."""
        raise NotImplemented('Must be implemented')

    def do_create_error(self, message):
        """Create an image with an error message."""
        raise NotImplemented('Must be implemented')

    @property
    def background_path(self):
        return 'static/images/dynamic_images/{}_image_background.png'.format(self.name)

    @property
    def error_background_path(self):
        return 'static/images/dynamic_images/{}_image_error_background.png'.format(self.name)

    def _paste(self, image, pos):
        """Paste an image onto the final one."""
        self.image.paste(image, pos, image)

    def _draw_text(self, pos, text, font=normal_font, color=white, shadow=dark_grey):
        """Draw a text on the final image."""
        if shadow:
            pos_shadow = (pos[0] + 2, pos[1] + 2)

            self.image_draw.text(pos_shadow, text, font=font, fill=shadow)

        self.image_draw.text(pos, text, font=font, fill=color)


class DynamicServerImage(DynamicImage):
    """A server dynamic image."""
    name = 'server'

    def __init__(self, ip, port, server):
        self.ip = ip
        self.port = port
        self.server = server

    def do_create(self):
        if not self.server:
            self.do_create_error('No Running With Rifles server found at {}:{}.'.format(self.ip, self.port))
        elif not self.server.is_dedicated:
            self.do_create_error('Server banner is only available for dedicated servers.')
        else:
            self.init(self.background_path)

            self._do_create_header()
            self._do_create_body()

    def do_create_error(self, message):
        self.init(self.error_background_path)
        self._draw_text((10, 50), message)

    def _do_create_header(self):
        """Create the top of the dynamic server image."""
        x = 7

        # Country flag
        if self.server.location.country_code:
            flag_image = Image.open('static/images/flags/{}.png'.format(self.server.location.country_code.upper())).convert('RGBA')

            self._paste(flag_image, (x, 4))

            x += 29

        # Ranked server indicator
        if self.server.is_ranked:
            yellow_star_image = Image.open('static/images/dynamic_images/yellow_star.png').convert('RGBA')

            self._paste(yellow_star_image, (x, 8))

            x += 23

        # Server name
        self._draw_text((x, 2), self.server.name, font=big_font)

    def _do_create_body(self):
        """Create the body (main area) of the dynamic server image."""
        # IP
        self._draw_text((7, 44), self.server.ip)

        # Port
        self._draw_text((7, 73), str(self.server.port))

        # Players
        self._draw_text((121, 44), '{}/{}'.format(self.server.players.current, self.server.players.max))

        # Server mode
        self._draw_text((121, 73), self.server.mode_name_long)

        # Map
        self._draw_text((234, 44), self.server.map.name_display)

        # Server type
        self._draw_text((234, 73), self.server.type_name)


class DynamicPlayerImage(DynamicImage):
    """A player dynamic image."""
    name = 'player'

    def __init__(self, database, username, player):
        self.database = database
        self.username = username
        self.player = player

    def do_create(self):
        if not self.player:
            self.do_create_error('Player "{}" wasn\'t found in the {} players list.'.format(self.username, rwr.utils.get_database_name(self.database)))
        else:
            self.init(self.background_path)

            self._do_create_header()
            self._do_create_body()

    def do_create_error(self, message):
        self.init(self.error_background_path)
        self._draw_text((10, 50), message)

    def _do_create_header(self):
        """Create the top of the dynamic player image."""
        # Username
        self._draw_text((9, 2), self.player.username, font=big_font)

        # Rank name
        rank_name_w, rank_name_h = self.image_draw.textsize(self.player.rank.name, font=small_font)

        self._draw_text((self.image.width - rank_name_w - 7, 7), self.player.rank.name, font=small_font)

    def _do_create_body(self):
        """Create the body (main area) of the dynamic player image."""
        # Rank image
        rank_image = Image.open('static/images/ranks/us/8.png').convert('RGBA')

        self._paste(rank_image, (3, 32))

        # XP
        self._draw_text((82, 45), helpers.simplified_integer(self.player.xp))

        # Score
        self._draw_text((82, 76), helpers.simplified_integer(self.player.score))

        # Kills
        self._draw_text((148, 45), helpers.simplified_integer(self.player.kills))

        # Deaths
        self._draw_text((148, 76), helpers.simplified_integer(self.player.deaths))

        # K/D ratio
        self._draw_text((219, 44), str(self.player.kd_ratio))

        # Time played
        self._draw_text((219, 76), helpers.humanize_seconds_to_hours(self.player.time_played))
