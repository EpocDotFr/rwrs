from PIL import Image, ImageDraw, ImageFont
from flask import send_file
from io import BytesIO
import arrow


font_path = 'static/fonts/komikax.ttf'

big_font = ImageFont.truetype(font_path, 16)
normal_font = ImageFont.truetype(font_path, 12)

grey = (90, 90, 90)
white = (255, 255, 255)
green = (164, 207, 23)
light_red = (244, 110, 110)


class DynamicImage:
    """A dynamic image."""
    def __init__(self, background_path):
        # self.image = Image.open(background_path).convert('RGBA') # TODO Use the dynamic image background instead of initializing a blank image
        self.image = Image.new('RGBA', (500, 100), (63, 63, 63))
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
        return send_file(self.final_image, mimetype='image/png', add_etags=False, cache_timeout=0, last_modified=arrow.now().datetime)

    def do_create(self):
        """Actually create the dynamic image."""
        raise NotImplemented('Must be implemented')

    def do_create_error(self, message):
        """Create an image with an error message."""
        raise NotImplemented('Must be implemented')

    def _paste(self, image, pos):
        """Paste an image onto the final one."""
        self.image.paste(image, pos, image)

    def _draw_text(self, pos, text, font=normal_font, color=white):
        """Draw a text on the final image."""
        self.image_draw.text(pos, text, font=font, fill=color)


class DynamicServerImage(DynamicImage):
    """A server dynamic image."""
    def __init__(self, ip, port, server):
        super(DynamicServerImage, self).__init__('static/images/server_image_background.png')

        self.ip = ip
        self.port = port
        self.server = server

    def do_create(self):
        if not self.server:
            self.do_create_error('There isn\'t any Running With Rifles server at {}:{}.'.format(self.ip, self.port))
        elif not self.server.is_dedicated:
            self.do_create_error('Server banner is only available for dedicated servers.')
        else:
            self._do_create_header()
            self._do_create_body()

    def do_create_error(self, message):
        # Error title
        self._draw_text((6, 3), 'Error', font=big_font, color=light_red)

        # Error message
        self._draw_text((6, 35), message)

    def _do_create_header(self):
        """Create the top of the dynamic server image."""
        x = 6

        # Country flag
        if self.server.location.country_code:
            flag_image = Image.open('static/images/flags/{}.png'.format(self.server.location.country_code)).convert('RGBA')

            self._paste(flag_image, (x, 6))

            x += 29

        # Ranked server indicator
        if self.server.is_ranked:
            yellow_star_image = Image.open('static/images/yellow_star.png').convert('RGBA')

            self._paste(yellow_star_image, (x, 10))

            x += 23

        # Server name
        self._draw_text((x, 3), self.server.name, font=big_font)

    def _do_create_body(self):
        """Create the body (main area) of the dynamic server image."""
        # IP address
        self._draw_text((6, 80), self.server.ip_and_port, color=grey)

        # Players
        self._draw_text((6, 50), '{}/{}'.format(self.server.players.current, self.server.players.max))

        # Map
        self._draw_text((70, 50), self.server.map.name_display)

        # Server type
        self._draw_text((240, 50), self.server.type_name)

        # Server mode
        self._draw_text((350, 50), self.server.mode_name_long)
