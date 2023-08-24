from PIL import Image, ImageDraw, ImageFont
from flask import make_response, g
from io import BytesIO
import rwr.scraper
import rwr.utils
import helpers
import arrow


font_path = 'static/fonts/komikax.ttf'

big_font = ImageFont.truetype(font_path, 15)
normal_font = ImageFont.truetype(font_path, 12)
small_font = ImageFont.truetype(font_path, 10)

white = (255, 255, 255)


class DynamicImage:
    status = 200

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
        response = make_response((self.final_image.getvalue(), self.status))

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

    def _draw_text(self, pos, text, font=normal_font, color=white):
        """Draw a text on the final image."""
        self.image_draw.text(pos, text, font=font, fill=color)


class DynamicServerImage(DynamicImage):
    """A server dynamic image."""
    name = 'server'

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def do_create(self):
        if g.UNDER_MAINTENANCE:
            self.status = 503
            self.do_create_error('Maintenance in progress.')

            return

        try:
            self.server = rwr.scraper.get_server_by_ip_and_port(self.ip, self.port)

            if not self.server:
                self.status = 404
                self.do_create_error('No Running With Rifles server found at {}:{}.'.format(self.ip, self.port))
            elif not self.server.is_dedicated:
                self.status = 403
                self.do_create_error('Server banner is only available for dedicated servers.')
            else:
                self.init(self.background_path)

                self._do_create_header()
                self._do_create_body()
        except:
            self.status = 500
            self.do_create_error('Internal server error: please try again later.')

    def do_create_error(self, message):
        self.init(self.error_background_path)
        self._draw_text((10, 50), message)

    def _do_create_header(self):
        """Creates the top of the dynamic server image."""
        x = 7

        # Country flag
        if self.server.location.country_code:
            flag_image = Image.open('static/images/flags/{}.png'.format(self.server.location.country_code.upper())).convert('RGBA')

            self._paste(flag_image, (x, 4))

            x += 29

        # Official server indicator
        if self.server.is_official:
            official_server_image = Image.open('static/images/dynamic_images/official_server.png').convert('RGBA')

            self._paste(official_server_image, (x, 8))

            x += 23

        # Server name
        self._draw_text((x, 2), self.server.name, font=big_font)

    def _do_create_body(self):
        """Creates the body (main area) of the dynamic server image."""
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

    def __init__(self, database, username):
        self.database = database
        self.username = username

    def do_create(self):
        if g.UNDER_MAINTENANCE:
            self.status = 503
            self.do_create_error('Maintenance in progress.')

            return

        try:
            self.player = rwr.scraper.search_player_by_username(self.database, self.username)

            if not self.player:
                self.status = 404
                self.do_create_error('Player "{}" wasn\'t found in\nthe {} players list.'.format(self.username, rwr.utils.get_database_name(self.database)))
            else:
                self.init(self.background_path)

                self._do_create_header()
                self._do_create_body()
        except:
            self.status = 500
            self.do_create_error('Internal server error: please try again later.')

    def do_create_error(self, message):
        self.init(self.error_background_path)
        self._draw_text((10, 45), message)

    def _do_create_header(self):
        """Creates the top of the dynamic player image."""
        # Username
        self._draw_text((7, 0), self.player.username, font=big_font)

        # Player icon
        if self.player.is_myself or self.player.is_contributor or self.player.is_rwr_dev or self.player.is_official_servers_mod:
            x, _ = self.image_draw.textsize(self.player.username, font=big_font)

            if self.player.is_myself:
                epoc_image = Image.open('static/images/epoc.png').convert('RGBA')

                x += 10

                self._paste(epoc_image, (x, 2))

                x += epoc_image.width
            elif self.player.is_contributor:
                contributor_image = Image.open('static/images/dynamic_images/contributor.png').convert('RGBA')

                x += 10

                self._paste(contributor_image, (x, 5))

                x += contributor_image.width
            elif self.player.is_rwr_dev:
                rwr_icon_image = Image.open('static/images/rwr_icon.png').convert('RGBA')

                x += 10

                self._paste(rwr_icon_image, (x, 2))

                x += rwr_icon_image.width

            if self.player.is_official_servers_mod:
                mod_image = Image.open('static/images/dynamic_images/mod.png').convert('RGBA')

                x += 5 if self.player.is_rwr_dev or self.player.is_contributor else 12

                self._paste(mod_image, (x, 6))

        # Rank name
        self._draw_text((7, 22), self.player.rank.name, font=small_font)

        # Database name
        database_name = '{} profile'.format(self.player.database_name)

        database_name_w, _ = self.image_draw.textsize(database_name, font=normal_font)

        self._draw_text((self.image.width - database_name_w - 4, 1), database_name, font=normal_font)

        # Owned icon
        if self.player.user:
            owned_image = Image.open('static/images/dynamic_images/owned.png').convert('RGBA')

            self._paste(owned_image, (self.image.width - owned_image.width - 4, 22))

    def _do_create_body(self):
        """Creates the body (main area) of the dynamic player image."""
        # Rank image
        rank_image = Image.open('static' + self.player.rank.image).convert('RGBA')

        self._paste(rank_image, (3, 42))

        # XP
        self._draw_text((82, 55), helpers.simplified_integer(self.player.xp))

        # Score
        self._draw_text((82, 86), helpers.simplified_integer(self.player.score))

        # Kills
        self._draw_text((148, 55), helpers.simplified_integer(self.player.kills))

        # Deaths
        self._draw_text((148, 86), helpers.simplified_integer(self.player.deaths))

        # K/D ratio
        self._draw_text((219, 55), str(self.player.kd_ratio))

        # Time played
        self._draw_text((219, 86), helpers.humanize_seconds_to_hours(self.player.time_played))
