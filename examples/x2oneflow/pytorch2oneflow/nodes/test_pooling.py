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
import torch
from torch import nn

from oneflow_onnx.x2oneflow.util import load_pytorch_module_and_check


def _test_k3s1p1(pt_pool):
    class Net(nn.Module):
        def __init__(self):
            super(Net, self).__init__()
            self.pool = pt_pool(3, stride=1, padding=1)

        def forward(self, x):
            x = self.pool(x)
            return x

    load_pytorch_module_and_check(Net, input_size=(2, 4, 3, 5))


def test_maxpool_k3s1p1():
    _test_k3s1p1(nn.MaxPool2d)


def test_avgpool_k3s1p1():
    _test_k3s1p1(nn.AvgPool2d)


def _test_k4s2p2(pt_pool):
    class Net(nn.Module):
        def __init__(self):
            super(Net, self).__init__()
            self.pool = pt_pool(4, stride=2, padding=2)

        def forward(self, x):
            x = self.pool(x)
            return x

    load_pytorch_module_and_check(Net, input_size=(2, 4, 10, 9))


def test_maxpool_k4s2p2():
    _test_k4s2p2(nn.MaxPool2d)


def test_avgpool_k4s2p3():
    _test_k4s2p2(nn.AvgPool2d)


def _test_k43s2p1(pt_pool):
    class Net(nn.Module):
        def __init__(self):
            super(Net, self).__init__()
            self.pool = pt_pool((4, 3), stride=2, padding=1)

        def forward(self, x):
            x = self.pool(x)
            return x

    load_pytorch_module_and_check(Net, input_size=(2, 4, 10, 9))


def test_maxpool_k43s2p1():
    _test_k43s2p1(nn.MaxPool2d)


def test_avgpool_k43s2p1():
    _test_k43s2p1(nn.AvgPool2d)


def _test_k43s2p21(pt_pool):
    class Net(nn.Module):
        def __init__(self):
            super(Net, self).__init__()
            self.pool = pt_pool((4, 3), stride=2, padding=(2, 1))

        def forward(self, x):
            x = self.pool(x)
            return x

    load_pytorch_module_and_check(Net, input_size=(2, 4, 10, 9))


def test_maxpool_k43s2p21():
    _test_k43s2p21(nn.MaxPool2d)


def test_avgpool_k43s2p21():
    _test_k43s2p21(nn.AvgPool2d)


def _test_global_pooling(pt_pool):
    class Net(nn.Module):
        def __init__(self):
            super(Net, self).__init__()
            self.pool = pt_pool((1, 1))

        def forward(self, x):
            x = self.pool(x)
            return x

    load_pytorch_module_and_check(Net, input_size=(2, 4, 10, 9))


def test_global_avg_pooling():
    _test_global_pooling(nn.AdaptiveAvgPool2d)


def test_global_max_pooling():
    _test_global_pooling(nn.AdaptiveMaxPool2d)
