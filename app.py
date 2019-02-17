from os import listdir, makedirs, path
from io import BytesIO
from tensorflow import logging
from keras.applications.vgg16 import VGG16
from keras.applications.nasnet import NASNetLarge
from keras.applications.vgg16 import preprocess_input, decode_predictions
from keras.preprocessing import image as kimage
from PIL import Image as pimage
from matplotlib import pyplot as plt

import requests
import numpy as np
import argparse


# attempts to validate if a collection of bytes represents an image by parsing them with PIL.Image
# throws an exception if the data cannot be parsed
def validate_image(bytes_data):
    buf = BytesIO(bytes_data)
    img = pimage.open(buf)


def download_imgs(links, save_dir, download_limit=100):
    # throw error if links isnt a list
    assert type(links) is list
    
    # iterate over each link, carrying both the link and it's list index
    i=0
    for link, i in zip(links, range(len(links))):
        if i > download_limit: break
        
        # log downloads
        print("GET : {} ...".format(link), end="")
        try:
            # make a GET request and dont follow redirects - timeout after 3 secs
            r = requests.get(link, allow_redirects=False, timeout=3)

            # make sure the response is an image, not HTML
            validate_image(r.content)

            filename = "{}img-{}".format(save_dir, i)
            if not path.exists(save_dir):
                makedirs(save_dir)
            with open(filename, 'wb') as f:
                f.write(r.content)
            print('complete.\n=>\tSaved as: {}'.format(filename))

        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout, OSError):
            print("failed.\n=>\tStatus-code:{}".format(r.status_code))
            pass
    
    return


def read_links(src):
    links = []
    with open(src, 'r') as srcfile:
        for line in srcfile:
            links.append(line)
    links = [line.rstrip('\n') for line in links]
    return links


#airplane_links = read_links('./dataset/url/airplane/url.txt')
#download_imgs(airplane_links, './dataset/img/airplane/')
#exit()

# silence tensorflow's useless info logging
logging.set_verbosity(logging.ERROR)

# parse arguments (image file's path)
argparser = argparse.ArgumentParser()
argparser.add_argument('file')
argparser.add_argument('--model')
args = argparser.parse_args()

# get testing image from test_src and VGG16 model from keras
test_src =  args.file

target_size = (224, 224)
base_model = None

if args.model == 'nasnet':
    target_size=(331, 331)
    print()
    base_model = NASNetLarge(include_top=True, weights="imagenet")
else:
    base_model = VGG16(include_top=True, weights="imagenet")
test_image = kimage.load_img(test_src, target_size=target_size )

# convert image to numerical array and reshape dimensions to match vgg input (224, 224, 3)
x_input = kimage.img_to_array(test_image)
x_input = np.expand_dims(x_input, axis=0)
x_input = preprocess_input(x_input)
pred    = decode_predictions(base_model.predict(x_input), top=3)[0]

# aggregate data from predictions - parallel arrays for simplicity
classes = []
datapoints = []
for cls in pred:
    classes.append( cls[1] )
    datapoints.append( cls[2] )

item_index = np.arange(len(classes))

# show image tested and corresponding machine predictions
image_figure = plt.figure(1)
plt.imshow(test_image)
image_figure.show()

prediction_figure = plt.figure(2)
plt.xticks( item_index , classes)
plt.ylabel('certainty')
plt.bar(item_index, datapoints, align='center')
prediction_figure.show()

#pause execution until input is received
input()

