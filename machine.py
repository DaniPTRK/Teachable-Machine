import random as rd
import numpy as np
from tensorflow.keras import layers, models, utils
from PIL import Image

def build_model(input, num_classes):
    # build model
    model = models.Sequential()
    
    # add layers to the model
    model.add(layers.Conv2D(32, (3, 3), activation="relu", input_shape = input, name = "layer1"))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    
    # flatten the output
    model.add(layers.Flatten())
    
    # add dense layers to the model
    model.add(layers.Dense(64, activation='relu'))

    # output layer
    model.add(layers.Dense(num_classes, activation='softmax'))
    
    return model

#define image & batch info
batch_size = 32
img_height = 180
img_width = 180

def resize_images(uploaded_photos):
    # resize each photo inside uploaded_photos
    for sublist in uploaded_photos:
        for image in sublist:
            image = image.resize((180, 180), Image.BILINEAR)
    return uploaded_photos    

def preprocess(X_data, Y_data, num_classes):
    # convert images to numpy arrays and normalize pixel values
    all_data = []
    all_labels = []

    for labels in Y_data:
        all_labels.append(Y_data)

    for photo in X_data:
        pixel_array = np.array(photo) / 255.0
        all_data.append(pixel_array)

    x_data = np.array(all_data)
    y_data = utils.to_categorical(all_labels, num_classes=num_classes)
    return x_data, y_data

def train(target, uploaded_photos, machine_name, num_classes):
    # resize the photos first
    uploaded_photos = resize_images(uploaded_photos)
    x_data = []
    y_data = []

    # failed attempt
    # train_data = utils.image_dataset_from_directory(uploaded_photos, validation_split = 0.2, subset = "training", seed = 123,
    #                                                 image_size = (img_height, img_width), batch_size=batch_size)
    # valid_Data = utils.image_dataset_from_directory(uploaded_photos, validation_split = 0.2, subset = "validation", seed = 123,
    #                                                 image_size = (img_height, img_width), batch_size=batch_size)

    # set labels
    for i in range(num_classes):
        print("HELLO!")
        for value in uploaded_photos[i]:
            x_data.append(value)
            y_data.append(i)
    
    
    # zip so shuffle is consistent
    temp = list(zip(x_data, y_data))
    rd.shuffle(temp)
    X_data, Y_data = zip(*temp)

    # # shuffle data & use 80% of images for training and 20% for validation
    # X_data = list(X_data)
    # Y_data = list(Y_data)
    # index = int(len(X_data) * 0.8)
    # trainX_data = X_data[:index]
    # validX_data = X_data[index:]
    # trainY_data = Y_data[:index]
    # validY_data = Y_data[index:]

    x_train, y_train = preprocess(X_data, Y_data, num_classes)
    
    # build and compile the model
    model = build_model((img_height, img_width), num_classes)
    model.compile(optimizer = 'adam', loss = 'categorical_crossentropy', metrics=['accuracy'])
    
    # train the model
    model.fit(x_train, y_train, epochs = 10, batch_size = batch_size)

    # save model
    model_export_path = f"{machine_name}_trained_model"
    model.save(model_export_path)

    return model