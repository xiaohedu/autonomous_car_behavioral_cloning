from import_data import train_generator, valid_generator, CROP, SIZE
import tensorflow as tf
import numpy as np
from sklearn.model_selection import train_test_split
import keras as K
from keras.models import Sequential
from keras.layers import Lambda, Cropping2D
from keras.layers.pooling import AveragePooling2D
from keras.preprocessing.image import ImageDataGenerator
from keras.layers.core import Dense, Activation, Flatten, Dropout
from keras.layers.convolutional import Convolution2D
from keras.optimizers import Adam
from keras.regularizers import l2
from optparse import OptionParser
from zipfile import ZipFile
import gc
import cv2
import csv

# Model meta-parameters

batch_size = 128
learning_rate = 0.0001
valid_split = .2
nb_epoch = 30
angle_corr = .28
ch = 3
keep_prob = .5

parser = OptionParser()
parser.add_option("-l", "--local", action = "store_true", dest = "local", default = False,
    help = "Tells the code to run locally. Defaults to False (then path names correspond to a remote instance")
(options, args) = parser.parse_args()

if options.local == True:
    log_dir = '/home/lucfrachon/udacity_sim/data/'
    im_dir = '/home/lucfrachon/udacity_sim/data/IMG/'
else:
    log_dir = "/mnt/data/"
    im_dir = "/mnt/data/IMG/"


# Build generator:


samples = []
with open(log_dir + 'driving_log.csv') as f:
	reader = csv.reader(f)
	for line in reader:
		samples.append(line)

train_samples, validation_samples = train_test_split(samples, 
	test_size = valid_split)

train_gen = train_generator(train_samples, log_dir, batch_size = batch_size, 
	angle_corr = angle_corr, channels = ch)
valid_gen = valid_generator(validation_samples, log_dir, batch_size = batch_size,
	channels = ch)


# Build model:
model = Sequential()

# Normalize on the fly:
model.add(Lambda(lambda x: (x / 127.5) - 1., 
    input_shape = (SIZE[1], SIZE[0], 3)))

model.add(Convolution2D(6, 1, 1, init = 'glorot_normal', border_mode = 'same',
    subsample = (1, 1), W_regularizer = l2(0.001)))
model.add(Activation('relu'))

model.add(Convolution2D(48, 5, 5, init = 'glorot_normal', border_mode = 'valid', 
	subsample = (2, 2), W_regularizer = l2(0.001)))
model.add(Activation('relu'))
model.add(Dropout(keep_prob))

model.add(Convolution2D(72, 5, 5, init = 'glorot_normal', border_mode = 'valid', 
	subsample = (2, 2), W_regularizer = l2(0.001)))
model.add(Activation('relu'))
model.add(Dropout(keep_prob))

model.add(Convolution2D(96, 3, 3, init = 'glorot_normal', border_mode = 'valid', 
	subsample = (1, 1), W_regularizer = l2(0.001)))
model.add(Activation('relu'))
model.add(Dropout(keep_prob))

model.add(Convolution2D(128, 1, 1, init = 'glorot_normal', border_mode = 'same', 
	subsample = (1, 1), W_regularizer = l2(0.001)))
model.add(Activation('relu'))
model.add(Dropout(keep_prob))

model.add(Flatten())

model.add(Dense(128, W_regularizer = l2(0.001)))
model.add(Activation('relu'))
model.add(Dropout(keep_prob))

model.add(Dense(64, W_regularizer = l2(0.001)))
model.add(Activation('relu'))
model.add(Dropout(keep_prob))

model.add(Dense(16, W_regularizer = l2(0.001)))
model.add(Activation('relu'))
model.add(Dropout(keep_prob))

model.add(Dense(1, W_regularizer = l2(0.001)))

# Configure learning process and train model:
adam = Adam(lr = learning_rate)
model.compile(loss = 'mse', optimizer = adam, metrics = ['accuracy'])

# Display model architecture
model.summary()

# Note that the actual batch size is twice the parameter because we use both the 
# original and the flipped images at each epoch.
history = model.fit_generator(train_gen, samples_per_epoch = 2 * len(train_samples), 
	validation_data = valid_gen, nb_val_samples = len(validation_samples), 
	 nb_epoch = nb_epoch, verbose = 1)

model.save('model_final.h5')
gc.collect()