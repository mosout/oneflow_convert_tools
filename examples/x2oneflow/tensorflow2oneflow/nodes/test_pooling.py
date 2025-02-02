"""
Copyright 2020 The OneFlow Authors. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import tensorflow as tf

from oneflow_onnx.x2oneflow.util import load_tensorflow2_module_and_check


def _test_k3s1p1(pt_pool):
    class Net(tf.keras.Model):
        def __init__(self):
            super(Net, self).__init__()
            self.pool = pt_pool(pool_size=(3,3), strides=(1,1), padding="same")

        def call(self, x):
            x = self.pool(x)
            return x

    load_tensorflow2_module_and_check(Net, input_size=(2, 4, 3, 5))


def test_maxpool_k3s1p1():
    _test_k3s1p1(tf.keras.layers.MaxPool2D)


def test_avgpool_k3s1p1():
    _test_k3s1p1(tf.keras.layers.AveragePooling2D)


def _test_k4s2p2(pt_pool):
    class Net(tf.keras.Model):
        def __init__(self):
            super(Net, self).__init__()
            self.pool = pt_pool(pool_size=(4,4), strides=(2,2), padding="same")

        def call(self, x):
            x = self.pool(x)
            return x

    load_tensorflow2_module_and_check(Net, input_size=(2, 4, 10, 9))


def test_maxpool_k4s2p2():
    _test_k4s2p2(tf.keras.layers.MaxPool2D)


def test_avgpool_k4s2p3():
    _test_k4s2p2(tf.keras.layers.AveragePooling2D)


def _test_k43s2p1(pt_pool):
    class Net(tf.keras.Model):
        def __init__(self):
            super(Net, self).__init__()
            self.pool = pt_pool(pool_size=(4, 3), strides=(2,2), padding="same")

        def call(self, x):
            x = self.pool(x)
            return x

    load_tensorflow2_module_and_check(Net, input_size=(2, 4, 10, 9))


def test_maxpool_k43s2p1():
    _test_k43s2p1(tf.keras.layers.MaxPool2D)


def test_avgpool_k43s2p1():
    _test_k43s2p1(tf.keras.layers.AveragePooling2D)


def _test_k43s2p21(pt_pool):
    class Net(tf.keras.Model):
        def __init__(self):
            super(Net, self).__init__()
            self.pool = pt_pool(pool_size=(4, 3), strides=(2,2), padding="same")

        def call(self, x):
            x = self.pool(x)
            return x

    load_tensorflow2_module_and_check(Net, input_size=(2, 4, 10, 9))


def test_maxpool_k43s2p21():
    _test_k43s2p21(tf.keras.layers.MaxPool2D)


def test_avgpool_k43s2p21():
    _test_k43s2p21(tf.keras.layers.AveragePooling2D)


def _test_global_pooling(pt_pool):
    class Net(tf.keras.Model):
        def __init__(self):
            super(Net, self).__init__()
            self.pool = pt_pool()

        def call(self, x):
            x = self.pool(x)
            return x

    load_tensorflow2_module_and_check(Net, input_size=(2, 4, 10, 9))


def test_global_avg_pooling():
    _test_global_pooling(tf.keras.layers.GlobalAveragePooling2D)


def test_global_max_pooling():
    _test_global_pooling(tf.keras.layers.GlobalMaxPool2D)

