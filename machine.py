import tensorflow as tf
from tensorflow.keras import layers, models

# build model
def build_model(input, num_classes):
    model = models.Sequential()
    # add layers to the model
    model.add(layers.Conv2D(32, (3, 3), activation="relu", input_shape = input, name = "layer1"))

# load model
def train(target, uploaded_photos, machine_name, num_classes):
    print(uploaded_photos[0].shape)
    print(uploaded_photos[1].shape)
    return 0