import os
from sklearn.model_selection import train_test_split
import tensorflow as tf
import numpy as np
from io import BytesIO
from tensorflow.keras import layers, models, utils
from keras.models import save_model
from PIL import Image

def build_model(input, num_classes):
    # build model
    model = models.Sequential()
    
    # add layers to the model
    model.add(layers.Conv2D(32, (3, 3), activation="relu", input_shape = input, name = "layer1"))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation="relu"))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation="relu"))
    
    # flatten the output
    model.add(layers.Flatten())
    
    # add dense layers to the model
    model.add(layers.Dense(256, activation="relu"))
    model.add(layers.Dropout(0.5))

    # output layer
    model.add(layers.Dense(num_classes, activation="softmax"))

    return model

# define image & batch info
batch_size = 32
img_height = 240
img_width = 240

# === meant to be something ===
# def resize_images(uploaded_photos):
#     # resize each photo inside uploaded_photos
#     input_size = (img_height, img_width)
#     for sublist in uploaded_photos:
#         for photo in sublist:
#             photo = photo.resize(input_size, Image.BILINEAR)
#     return uploaded_photos    
# === meant to be something ===

def preprocess(X_data, Y_data, num_classes):
    # convert images to numpy arrays and normalize pixel values
    all_data = []
    all_labels = []
    i = 0

    for photo in X_data:
        # transform bytes in rgb values
        pixel_array = np.array(photo)

        # === 
        # numpy_array = np.frombuffer(photo, dtype = np.uint8)
        # normalize_image = numpy_array / 255.0
        # ===

        normalize_image = pixel_array / 255.0
        all_data.append(normalize_image)
        all_labels.append(Y_data[i])
        i = i+1

    x_data = np.array (all_data)
    y_data = np.array (all_labels)
    return x_data, y_data

# this is used for training a machine that's about to be uploaded
def train(uploaded_photos, machine_name, num_classes):
    # convert FileStorage to image and then resize it to the preferred sizes
    actual_photos = [[] for _ in range(num_classes)]
    input_size = (img_height, img_width)
    for i in range(num_classes):
        for photo_bytes in uploaded_photos[i]:
            image = Image.open(BytesIO(photo_bytes.read())).convert("RGB")
            actual_photos[i].append(image.resize(input_size, Image.BILINEAR))
            # actual_photos[i].append(Image.open(BytesIO(photo_bytes.read())).resize(input_size, Image.BILINEAR))
    
    # uploaded_photos = resize_images(uploaded_photos)
    x_data = []
    y_data = []
    x_valid = []
    y_valid = []

    # === failed attempt
    # train_data = utils.image_dataset_from_directory(uploaded_photos, validation_split = 0.2, subset = "training", seed = 123,
    #                                                 image_size = (img_height, img_width), batch_size=batch_size)
    # valid_Data = utils.image_dataset_from_directory(uploaded_photos, validation_split = 0.2, subset = "validation", seed = 123,
    #                                                 image_size = (img_height, img_width), batch_size=batch_size)
    # ===

    # set labels
    for i in range(num_classes):
        for value in actual_photos[i]:
            x_data.append(value)
            y_data.append(i)
    
    
    # === failed attempt
    # zip so shuffle is consistent
    # temp = list(zip(x_data, y_data))
    # rd.shuffle(temp)
    # X_data, Y_data = zip(*temp)
    # for i in range(len(x_data)):
    #     indices.append(i)
    # rd.shuffle(indices)
            
    # append data afterwards
    # for i in range(len(x_data)):
    #     X_data.append(x_data[indices[i]])
    #     Y_data.append(y_data[indices[i]])

    # # shuffle data & use 80% of images for training and 20% for validation
    # X_data = list(X_data)
    # Y_data = list(Y_data)
    # index = int(len(X_data) * 0.8)
    # trainX_data = X_data[:index]
    # validX_data = X_data[index:]
    # trainY_data = Y_data[:index]
    # validY_data = Y_data[index:]  
    # ===

    x_train, y_train = preprocess(x_data, y_data, num_classes)

    # shuffle & split
    # x_train, x_valid, y_train, y_valid = train_test_split(x_train, y_train, test_size = 0.2)

    # index = int(len(x_train) * 0.8)
    # x_traind = x_train[:index]
    # x_valid = x_train[index:]
    # y_traind = y_train[:index]
    # y_valid = y_train[index:]
    
    # build and compile the model
    model = build_model((img_height, img_width, 3), num_classes)
    model.compile(optimizer = 'adam', loss = 'sparse_categorical_crossentropy', metrics=['accuracy'])
    
    # train the model
    model.fit(x_train, y_train, epochs = 10, batch_size = batch_size)

    # save model
    model_file_name = f"{machine_name}_trained_model"
    model_file_format = model_file_name + ".h5"
    model_filepath = os.path.join("machines", model_file_format)
    save_model(model, model_filepath)

    return model_file_name

# this is used for making predictions with an uploaded machine
def predict(labels, model_filepath, img):
    # extract model from given path
    model_filepath += ".h5"
    model_filepath = "./machines/" + model_filepath
    model = tf.keras.models.load_model(model_filepath)

    # extract image
    input_size = (img_height, img_width)
    image = Image.open(BytesIO(img.read())).convert("RGB")

    # resize image and prepare it for predictions by normalizing
    resized_image = image.resize(input_size, Image.BILINEAR)
    pixel_array = np.array(resized_image)
    pixel_array = pixel_array / 255.0
    pixel_array = np.expand_dims(pixel_array, axis = 0)
    predictions = model.predict(pixel_array)

    # get confidence from prediction
    confidence_predictions = tf.nn.softmax(predictions)
    confidence = np.max(confidence_predictions)

    # extract predicted class
    predicted_class = np.argmax(predictions)
    return labels[predicted_class], confidence*100