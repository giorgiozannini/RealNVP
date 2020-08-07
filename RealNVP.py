"""
Title: Density estimation using Real NVP
Author: [Mandolini Giorgio Maria](https://www.linkedin.com/in/giorgio-maria-mandolini-a2a1b71b4/), [Sanna Daniele](https://www.linkedin.com/in/daniele-sanna-338629bb/), [Zannini Quirini Giorgio](https://www.linkedin.com/in/giorgio-zannini-quirini-16ab181a0/)
Date created: 2020/03/15
Last modified: 2020/08/07
Description: Estimating the density distribution from a toy dataset.
"""

"""
## Introduction
The aim of this work consists in mapping a simple distribution - which is easy to sample
and whose density is simple to estimate - to a more complex one learned from the data;
these kind of generative models is also knowm as "normalizing flows".

In order to obtain the aforementioned result the model is trained by means of the maximum
likelihood principle, resorting to the "change of variable formula".

An affine coupling layer function is built. It is created such that its inverse and the determinant
of the jacobian is easy to obtain (more details in the referenced paper).

References:
[Density estimation using Real NVP](https://arxiv.org/pdf/1605.08803.pdf)
"""

"""
## Setup

"""

"""invisible
pip install tensorflow-gpu==2.1.0rc0
pip install tensorflow_probability==0.8.0rc0
"""

# Libraries to import

import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.datasets import make_moons
import tensorflow_probability as tfp
from tensorflow.keras.layers import Layer, Dense, ReLU, Activation, Input
from tensorflow.keras.regularizers import l2
from tensorflow.keras import Model
from tqdm import notebook

"""
## Load the data
"""

# Generating the examples

moons = make_moons(1000, noise=0.05)[0].astype("float32")
moons_df = pd.DataFrame(moons)
plt.figure(figsize=(15, 10))
moons_plot = sns.scatterplot(x=0, y=1, data=moons_df)
moons_plot.set(title="Double moons", xlabel="x", ylabel="y")

"""
## Affine coupling layer
"""

# Creating a custom layer with keras API


class s_t(Layer):
    def __init__(
        self, input_shape, nweights=256, reg=0.01, name="net", dtype="float32"
    ):
        super(s_t, self).__init__()

        # t has no activation function
        # s has tanh activation function
        # all the other layers have a relu activation function

        self.layer1 = Dense(nweights, activation="relu", kernel_regularizer=l2(reg))
        self.layer2 = Dense(nweights, activation="relu", kernel_regularizer=l2(reg))
        self.layer3 = Dense(nweights, activation="relu", kernel_regularizer=l2(reg))
        self.layer4 = Dense(nweights, activation="relu", kernel_regularizer=l2(reg))
        self.layer5 = Dense(
            input_shape, activation="linear", kernel_regularizer=l2(reg)
        )

        self.layer6 = Dense(nweights, activation="relu", kernel_regularizer=l2(reg))
        self.layer7 = Dense(nweights, activation="relu", kernel_regularizer=l2(reg))
        self.layer8 = Dense(nweights, activation="relu", kernel_regularizer=l2(reg))
        self.layer9 = Dense(nweights, activation="relu", kernel_regularizer=l2(reg))
        self.layer10 = Dense(input_shape, activation="tanh", kernel_regularizer=l2(reg))

    # Operations performed when the layer is called

    def call(self, x):

        # Calling the previously specified layers one by one
        y = self.layer1(x)
        y = self.layer2(y)
        y = self.layer3(y)
        y = self.layer4(y)
        t = self.layer5(y)

        z = self.layer6(x)
        z = self.layer7(z)
        z = self.layer8(z)
        z = self.layer9(z)
        s = self.layer10(z)

        return s, t


"""
## Real NVP
"""

# class containing the whole set of operations


class realnvp(Layer):
    def __init__(self, layers, masks, distr):
        super(realnvp, self).__init__()

        # number of coupling layers
        self.num_cl = len(masks)
        # distribution of the latent space
        self.distr = distr
        # masks to divide into 1:d and d+1:D
        self.masks = masks
        # s and t custom layers of before
        self.layers = layers

    # Custom function defining the forward operation

    def forward(self, y):
        # log determinant of the forward pass
        log_det_for = tf.zeros(y.shape[0])
        x = y
        for i in range(self.num_cl):
            x_masked = x * self.masks[i]
            reversed_mask = 1 - self.masks[i]
            s, t = self.layers[i](x_masked)
            x = x_masked + reversed_mask * (
                x * tf.exp(s) * reversed_mask + t * reversed_mask
            )
            log_det_for += tf.reduce_sum(s, [1])

        return x, log_det_for

    # Custom function defining the forward operation

    def inverse(self, x):
        # log determinant of the forward pass
        log_det_inv = tf.zeros(x.shape[0])
        y = x
        for i in reversed(range(self.num_cl)):
            y_masked = y * self.masks[i]
            reversed_mask = 1 - self.masks[i]
            s, t = self.layers[i](y_masked)
            y = (
                reversed_mask * (y - t * reversed_mask) * tf.exp(-(s * reversed_mask))
                + y_masked
            )
            log_det_inv -= tf.reduce_sum(s, [1])

        return y, log_det_inv

    # log likelihood of the normal distribution + the log determinant of the jacobian

    def log_likelihood(self, x):
        y, logdet = self.inverse(x)
        return self.distr.log_prob(y) + logdet


"""
## Initialization
"""

# initializing the masks, the layers and the prior distribution for the real nvp
num_cl = 6
masks = np.array([[0, 1], [1, 0]] * (num_cl // 2), dtype="float32")
layers = [s_t(2) for i in range(num_cl)]

tfd = tfp.distributions
distr = tfd.MultivariateNormalDiag(loc=[0.0, 0.0], scale_diag=[1.0, 1.0])

real_nvp = realnvp(layers, masks, distr)

"""
## Model training
"""

loss_history = []
# Adam optimizer
optimizer = tf.keras.optimizers.Adam(learning_rate=0.00005)

# 2000 epochs
for i in notebook.tqdm(range(2000)):
    with tf.GradientTape() as tape:

        # the loss is - the mean of the log likelihood
        loss = -tf.reduce_mean(real_nvp.log_likelihood(moons))
        loss_history.append(loss)
        if i % 100 == 0:
            print(loss)

    # updating the variables
    g = tape.gradient(loss, real_nvp.trainable_variables)
    l = optimizer.apply_gradients(zip(g, real_nvp.trainable_variables))

"""
## Performance evaluation
"""

# loss history
sns.set_style("whitegrid")
plt.figure(figsize=(15, 10))
ax = sns.lineplot(range(len(loss_history)), np.array(loss_history))
ax.set(title="Loss history", xlabel="Epochs", ylabel="Loss")

# From moons to latent space
z, _ = real_nvp.inverse(moons)

# From latent space to moons
samples = distr.sample(100)
x, _ = real_nvp.forward(samples)

# Storing variables into dataframe to plot with seaborn
moons_df, z_df, samples_df, x_df = (
    pd.DataFrame(moons),
    pd.DataFrame(np.array(z)),
    pd.DataFrame(np.array(samples)),
    pd.DataFrame(np.array(x)),
)

f, axes = plt.subplots(2, 2)
f.set_size_inches(20, 15)

ax_0 = sns.scatterplot(x=0, y=1, data=moons_df, ax=axes[0, 0])
ax_0.set(title="Inference data space X", xlabel="x", ylabel="y")
ax_1 = sns.scatterplot(x=0, y=1, data=z_df, ax=axes[0, 1])
ax_1.set(title="Inference latent space Z", xlabel="x", ylabel="y")
ax_2 = sns.scatterplot(x=0, y=1, data=samples_df, ax=axes[1, 0], color="g")
ax_2.set(title="Generated latent space Z", xlabel="x", ylabel="y")
ax_3 = sns.scatterplot(x=0, y=1, data=x_df, ax=axes[1, 1], color="g")
ax_3.set(title="Generated data space X", label="x", ylabel="y")
