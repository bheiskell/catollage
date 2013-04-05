"""
"""

from flask import Flask
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

@app.route('/collage/')
def serve_img():
    """Serve the requested image."""
    img = Image.new('RGB')
    return serve_pil_image(img)

def serve_pil_image(image):
    """Serve a Flask image stream."""
    stream = StringIO()
    image.save(stream, 'JPEG', quality=70)
    stream.seek(0)
    return send_file(stream, mimetype='image/jpeg')


__OFFSET = pow(2, 8)

def image_average_color(image):
    histogram_list = image.convert("RGB").histogram()
    histogram_dict = {
        'R': histogram_list[__OFFSET * 0:__OFFSET],
        'G': histogram_list[__OFFSET * 1:__OFFSET * 2],
        'B': histogram_list[__OFFSET * 2:__OFFSET * 3],
    }

    average_color = {}
    for color, histogram in histogram_dict.items():
        # http://stackoverflow.com/questions/7563315/how-to-loop-over-histogram-to-get-the-color-of-the-picture
        weighted_sum = sum(count * histogram[count] for count in range(len(histogram)))
        num_pixels = sum(histogram)
        average_color[color] = weighted_sum / num_pixels


    return (average_color['R'] , average_color['G'], average_color['B'])

def get_image_dict(directory, max_cell_size):
    images = {}
    for filename in listdir(directory):
        try:
            image = Image.open(join(directory,filename))
            average_color = image_average_color(image)

            __log__.debug("Average color of '%s' is %s", filename, average_color)

            images[average_color] = image.resize((max_cell_size, max_cell_size))
        except IOError:
            pass

    return images

def get_average_color(pixels, x_min, x_max, y_min, y_max):

    count = 0
    r_sum = 0
    g_sum = 0
    b_sum = 0

    for x in range(x_min, x_max):
        for y in range(y_min, y_max):
            (r, g, b) = pixels[x, y]
            r_sum += r
            g_sum += g
            b_sum += b
            count += 1

    return (
        int(round(r_sum / count)),
        int(round(g_sum / count)),
        int(round(b_sum / count))
    )

cell_size = 32

images = get_image_dict(argv[1], cell_size)
coordinates = images.keys()

kdtree = spatial.KDTree(coordinates)

image = Image.open(argv[2])
pixels = image.convert("RGB").load()
(width, height) = image.size

color_to_coord = {}
for x_cell in range(width // cell_size):
    for y_cell in range(height // cell_size):
        x_min = x_cell * cell_size
        x_max = min(x_min + cell_size, width)
        y_min = y_cell * cell_size
        y_max = min(y_min + cell_size, height)

        average_color = get_average_color(pixels, x_min, x_max, y_min, y_max)

        if average_color not in color_to_coord:
            color_to_coord[average_color] = []

        color_to_coord[average_color].append((x_min, y_min))

        #__log__.debug("Blocks %d:%d:%d:%d - %s", x_min, x_max, y_min, y_max, average_color)

colors = color_to_coord.keys()
(distances, indexes) = kdtree.query(colors)

new_image = Image.new("RGB", (width, height))

offsets = []
for i in range(len(colors)):
    index = indexes[i]
    coordinate = coordinates[indexes[i]]
    cell = images[coordinates[indexes[i]]]
    for offset in color_to_coord[colors[i]]:
        offsets.append(offset)
        __log__.debug("At %s color %s is similar to %s", offset, colors[i], coordinate)
        new_image.paste(cell, offset)

#print set(offsets).difference(set(color_to_coord.values()))
#print set(color_to_coord.values()).difference(set(offsets))

new_image.save(argv[3])

#http://docs.python.org/2/library/colorsys.html
#http://stackoverflow.com/questions/500607/what-are-the-lesser-known-but-useful-data-structures
#http://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.query.html#scipy.spatial.KDTree.query
#https://en.wikipedia.org/wiki/K-d_tree
#http://www.pythonware.com/library/pil/handbook/image.htm
#Loop through all images getting their average rgb or hvs or chom whatever
#Generate a kd tree
#
#Check image size (reject anything over a meg)
#Pick a pixel size (reject anything that will result in > 1024
#Loop through each section calculating average
#Get the average color for that section using the histogram
#Load the image for that color
#Resize the image to the block size
#Overlay it onto the image
