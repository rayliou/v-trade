from os import environ
environ["KERAS_BACKEND"] = "plaidml.keras.backend"
import keras
import numpy as np
from os import environ
environ["KERAS_BACKEND"] = "plaidml.keras.backend"
import keras
from keras.layers import Dense
from matplotlib import pyplot as plt

# Params
num_samples = 100000; vect_len = 20; max_int = 10; min_int = 1;

# Generate dataset
X = np.random.randint(min_int, max_int, (num_samples, vect_len))
Y = np.sum(X, axis=1)

# Get 80% of data for training
split_idx = int(0.8 * len(Y))
train_X = X[:split_idx, :]; test_X = X[split_idx:, :]
train_Y = Y[:split_idx]; test_Y = Y[split_idx:]

# Make model
model = keras.models.Sequential()
model.add(keras.layers.Dense(32, activation='relu', input_shape=(vect_len,)))
model.add(keras.layers.Dense(1))
model.compile('adam', 'mse')

history = model.fit(train_X, train_Y, validation_data=(test_X, test_Y), \
                    epochs=10, batch_size=100)

# summarize history
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()
