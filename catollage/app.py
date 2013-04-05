"""Catollage web application."""

from flask import Flask, render_template, request, send_file
from PIL import Image
from StringIO import StringIO
from scipy import spatial
from sys import argv
from os import listdir
from os.path import join
import logging

__log__ = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__) #pylint: disable=C0103

MAX_CELL_SIZE = 16
HISTOGRAM_OFFSET = pow(2, 8)

@app.route('/')
def index():
    """Index page."""
    return render_template('index.html')

@app.route('/collage/', methods=['POST'])
def upload():
    """Handle the uploaded image."""

    uploaded_image = Image.open(request.files['image'])

    __log__.debug("Uploaded image %s", uploaded_image)

    collage_image = app.config['catollage'].collage_from(uploaded_image)
    return serve_image(collage_image)

def serve_image(image):
    """Serve a image stream."""
    stream = StringIO()
    image.save(stream, 'JPEG', quality=70)
    stream.seek(0)
    return send_file(stream, mimetype='image/jpeg', cache_timeout=0)

class Sources(object):
    """Manage and interact with collage sources."""

    def __init__(self):
        self.rgb_to_images = None
        self.rgbs = None
        self.kdtree = None

    def from_dir(self, directory):
        """Load sources from a directory"""
        self.from_images(( Image.open(join(directory, filename)) for filename in listdir(directory) ))

    def from_images(self, images):
        """Load sources from a list of images."""
        self.rgb_to_images = Sources._get_rgb_to_images(images)
        self.rgbs = self.rgb_to_images.keys()
        self.kdtree = spatial.KDTree(self.rgbs)

    def collage_from(self, image):
        """Convert the image to a collage."""

        # TODO: simply this method
        #pylint: disable=R0914

        if image.mode != "RGB":
            image = image.convert("RGB")

        (width, height) = image.size

        __log__.debug("Processing an image of size %dx%d", width, height)

        rgb_to_coords = Sources._get_rgb_to_coords(image, width, height)
        rgbs = rgb_to_coords.keys()

        (distances, indexes) = self.kdtree.query(rgbs) #pylint: disable=W0612

        new_image = Image.new("RGB", (width, height))

        for i in range(len(rgbs)):
            rgb = self.rgbs[indexes[i]]
            source = self.rgb_to_images[rgb]

            for coord in rgb_to_coords[rgbs[i]]:
                #__log__.debug("Coordinate: %s - Color %s is similar to %s", coord, rgbs[i], rgb)

                (x_min, y_min) = coord
                range_tuple = Sources._get_x_y_range(x_min, y_min, width, height, MAX_CELL_SIZE)

                new_image.paste(source, range_tuple)

        return new_image

    @staticmethod
    def _get_rgb_to_images(images):
        """Get a mapping of RGB tuples to images."""
        rgb_to_images = {}
        for image in images:
            try:
                if image.mode != "RGB":
                    image = image.convert("RGB")

                rgb = Sources._get_rgb(image)

                __log__.debug("Color of %s is %s", image, rgb)

                rgb_to_images[rgb] = image.resize((MAX_CELL_SIZE, MAX_CELL_SIZE))

            except IOError, exception:
                __log__.warn("Failed to load image %s: %s", image, exception)

        return rgb_to_images

    @staticmethod
    def _get_rgb(image):
        """Get an RGB tuple that represents this image."""

        histogram_dict = Sources._get_color_to_histogram(image.histogram())

        rgb = {}
        for color, histogram in histogram_dict.items():
            weighted_sum = sum(count * histogram[count] for count in range(len(histogram)))
            num_pixels = sum(histogram)
            rgb[color] = weighted_sum / num_pixels


        return (rgb['R'] , rgb['G'], rgb['B'])

    @staticmethod
    def _get_color_to_histogram(histogram):
        """Get a dict mapping color to a histogram list."""
        return {
            'R': histogram[HISTOGRAM_OFFSET * 0:HISTOGRAM_OFFSET],
            'G': histogram[HISTOGRAM_OFFSET * 1:HISTOGRAM_OFFSET * 2],
            'B': histogram[HISTOGRAM_OFFSET * 2:HISTOGRAM_OFFSET * 3],
        }

    @staticmethod
    def _get_rgb_to_coords(image, width, height):
        """Get a dict mapping rgbs to lists of top-left coordinates."""

        rgb_to_coords = {}
        for x_cell in range(width // MAX_CELL_SIZE):
            for y_cell in range(height // MAX_CELL_SIZE):

                (x_min, y_min, x_max, y_max) = Sources._get_x_y_range(
                    x_cell * MAX_CELL_SIZE,
                    y_cell * MAX_CELL_SIZE,
                    width,
                    height,
                    MAX_CELL_SIZE
                )

                rgb = Sources._get_rgb_of_region(image, x_min, x_max, y_min, y_max)

                if rgb not in rgb_to_coords:
                    rgb_to_coords[rgb] = []

                rgb_to_coords[rgb].append((x_min, y_min))

        return rgb_to_coords

    @staticmethod
    def _get_x_y_range(x, y, width, height, cell_size):
        """Helper for getting region coordinates."""

        #pylint: disable=C0103
        return (
            x,
            y,
            min(x + cell_size, width),
            min(y + cell_size, height),
        )

    @staticmethod
    def _get_rgb_of_region(image, x_min, x_max, y_min, y_max):
        """Get an RGB tuple that represents an images region."""

        count = 0
        r_sum = 0
        g_sum = 0
        b_sum = 0

        #pylint: disable=C0103
        for x in range(x_min, x_max):
            for y in range(y_min, y_max):
                (r, g, b) = image.getpixel((x, y))
                r_sum += r
                g_sum += g
                b_sum += b
                count += 1

        return (
            int(round(r_sum / count)),
            int(round(g_sum / count)),
            int(round(b_sum / count))
        )

def main():
    """Run the web application."""
    sources = Sources()
    sources.from_dir(argv[1])

    app.config['catollage'] = sources
    app.run(host='0.0.0.0', debug=True)

if __name__ == '__main__':
    main()
