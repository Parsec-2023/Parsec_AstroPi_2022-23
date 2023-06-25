from keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D
from keras.models import Model

inputs = Input((1024, 1024, 3))

# encoder
x = Conv2D(64, 3, activation = 'relu', padding = 'same')(inputs)
x = Conv2D(64, 3, activation = 'relu', padding = 'same')(x)
x = MaxPooling2D((2, 2), strides = (2, 2))(x)

x = Conv2D(128, 3, activation = 'relu', padding = 'same')(x)
x = Conv2D(128, 3, activation = 'relu', padding = 'same')(x)
x = MaxPooling2D((2, 2), strides = (2, 2))(x)

x = Conv2D(256, 3, activation = 'relu', padding = 'same')(x)
x = Conv2D(256, 3, activation = 'relu', padding = 'same')(x)
x = MaxPooling2D((2, 2), strides = (2, 2))(x)

x = Conv2D(512, 3, activation = 'relu', padding = 'same')(x)
x = Conv2D(512, 3, activation = 'relu', padding = 'same')(x)
x = MaxPooling2D((2, 2), strides = (2, 2))(x)

x = Conv2D(1024, 3, activation = 'relu', padding = 'same')(x)
x = Conv2D(1024, 3, activation = 'relu', padding = 'same')(x)

# decoder
x = UpSampling2D((2, 2))(x)
x = Conv2D(512, 3, activation = 'relu', padding = 'same')(x)
x = Conv2D(512, 3, activation = 'relu', padding = 'same')(x)

x = UpSampling2D((2, 2))(x)
x = Conv2D(256, 3, activation = 'relu', padding = 'same')(x)
x = Conv2D(256, 3, activation = 'relu', padding = 'same')(x)

x = UpSampling2D((2, 2))(x)
x = Conv2D(128, 3, activation = 'relu', padding = 'same')(x)
x = Conv2D(128, 3, activation = 'relu', padding = 'same')(x)

x = UpSampling2D((2, 2))(x)
x = Conv2D(64, 3, activation = 'relu', padding = 'same')(x)
x = Conv2D(64, 3, activation = 'relu', padding = 'same')(x)

import numpy as np
from sklearn.model_selection import train_test_split
import os
from PIL import Image
from pathlib import Path

# get parent folder
baseFolder = Path(__file__).parent.resolve()
directory = str(baseFolder) + "/" + "dataset"

# get the list of image files in the directory
image_files = [f for f in os.listdir(directory + "/Images") if f.endswith(".jpg") or f.endswith(".png")]

# initialise an empty list to store the images
images = []

# iterate over the image files
for file in image_files:
    # open the image file using PIL and add it to the list
    images.append(Image.open(os.path.join(directory + "/Images", file)))

# get the list of image files in the directory
labels_files = [f for f in os.listdir(directory + "/Annotations") if f.endswith(".jpg") or f.endswith(".png")]

# initialise an empty list to store the images
labels = []

# iterate over the image files
for file in labels_files:
    # open the image file using PIL and add it to the list
    labels.append(Image.open(os.path.join(directory + "/Annotations", file)))

# convert the list of images to a NumPy array
X = np.array(images)

# convert the list of labels to a NumPy array
y = np.array(labels)

# split the labels into training and validation sets
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size = 0.2)

X_train = X_train.astype('float32') / 255.0
X_val = X_val.astype('float32') / 255.0

y_train = y_train.astype('float32') / 255.0
y_val = y_val.astype('float32') / 255.0

from keras.losses import binary_crossentropy

def dice_coeff(y_true, y_pred):
    smooth = 1.
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

def loss(y_true, y_pred):
    return binary_crossentropy(y_true, y_pred) - K.log(dice_coeff(y_true, y_pred))

optimiser = Adam(lr = 1e-4)

model.compile(optimizer = optimiser, loss = loss, metrics = [dice_coeff])

history = model.fit(X_train, y_train, epochs = num_epochs, batch_size = batch_size, validation_data = (X_val, y_val))

import matplotlib.pyplot as plt

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.show()