import tensorflow as tf
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

def train(target, uploaded_photos, machine_name, num_classes):
    # resize the photos first
    uploaded_photos = resize_images(uploaded_photos)

    # use 80% of images for training and 20% for validation
    train_data = utils.image_dataset_from_directory(uploaded_photos, validation_split = 0.2, subset = "training", 
                                                    image_size = (img_height, img_width), batch_size=batch_size)
    valid_Data = utils.image_dataset_from_directory(uploaded_photos, validation_split = 0.2, subset = "validation", 
                                                    image_size = (img_height, img_width), batch_size=batch_size)
    
    #set class names
    class_names = target
    
    return 0