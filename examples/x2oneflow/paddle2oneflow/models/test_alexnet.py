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
# https://github.com/PaddlePaddle/PaddleClas/blob/develop/ppcls/modeling/architectures/alexnet.py
import paddle
from paddle import ParamAttr
import paddle.nn as nn
import paddle.nn.functional as F
from paddle.nn import Conv2D, BatchNorm, Linear, Dropout, ReLU
from paddle.nn import AdaptiveAvgPool2D, MaxPool2D, AvgPool2D
from paddle.nn.initializer import Uniform
import math

_all__ = ["AlexNet"]

from oneflow_onnx.x2oneflow.util import load_paddle_module_and_check


class ConvPoolLayer(nn.Layer):
    def __init__(
        self,
        input_channels,
        output_channels,
        filter_size,
        stride,
        padding,
        stdv,
        groups=1,
        act=None,
        name=None,
    ):
        super(ConvPoolLayer, self).__init__()

        self.relu = ReLU() if act == "relu" else None

        self._conv = Conv2D(
            in_channels=input_channels,
            out_channels=output_channels,
            kernel_size=filter_size,
            stride=stride,
            padding=padding,
            groups=groups,
            weight_attr=ParamAttr(
                name=name + "_weights", initializer=Uniform(-stdv, stdv)
            ),
            bias_attr=ParamAttr(
                name=name + "_offset", initializer=Uniform(-stdv, stdv)
            ),
        )
        self._pool = MaxPool2D(kernel_size=3, stride=2, padding=0)

    def forward(self, inputs):
        x = self._conv(inputs)
        if self.relu is not None:
            x = self.relu(x)
        x = self._pool(x)
        return x


class AlexNetDY(nn.Layer):
    def __init__(self, class_dim=1000):
        super(AlexNetDY, self).__init__()

        stdv = 1.0 / math.sqrt(3 * 11 * 11)
        self._conv1 = ConvPoolLayer(3, 64, 11, 4, 2, stdv, act="relu", name="conv1")
        stdv = 1.0 / math.sqrt(64 * 5 * 5)
        self._conv2 = ConvPoolLayer(64, 192, 5, 1, 2, stdv, act="relu", name="conv2")
        stdv = 1.0 / math.sqrt(192 * 3 * 3)
        self._conv3 = Conv2D(
            192,
            384,
            3,
            stride=1,
            padding=1,
            weight_attr=ParamAttr(
                name="conv3_weights", initializer=Uniform(-stdv, stdv)
            ),
            bias_attr=ParamAttr(name="conv3_offset", initializer=Uniform(-stdv, stdv)),
        )
        stdv = 1.0 / math.sqrt(384 * 3 * 3)
        self._conv4 = Conv2D(
            384,
            256,
            3,
            stride=1,
            padding=1,
            weight_attr=ParamAttr(
                name="conv4_weights", initializer=Uniform(-stdv, stdv)
            ),
            bias_attr=ParamAttr(name="conv4_offset", initializer=Uniform(-stdv, stdv)),
        )
        stdv = 1.0 / math.sqrt(256 * 3 * 3)
        self._conv5 = ConvPoolLayer(256, 256, 3, 1, 1, stdv, act="relu", name="conv5")
        stdv = 1.0 / math.sqrt(256 * 6 * 6)

        self._drop1 = Dropout(p=0.5, mode="downscale_in_infer")
        self._fc6 = Linear(
            in_features=256 * 6 * 6,
            out_features=4096,
            weight_attr=ParamAttr(name="fc6_weights", initializer=Uniform(-stdv, stdv)),
            bias_attr=ParamAttr(name="fc6_offset", initializer=Uniform(-stdv, stdv)),
        )

        self._drop2 = Dropout(p=0.5, mode="downscale_in_infer")
        self._fc7 = Linear(
            in_features=4096,
            out_features=4096,
            weight_attr=ParamAttr(name="fc7_weights", initializer=Uniform(-stdv, stdv)),
            bias_attr=ParamAttr(name="fc7_offset", initializer=Uniform(-stdv, stdv)),
        )
        self._fc8 = Linear(
            in_features=4096,
            out_features=class_dim,
            weight_attr=ParamAttr(name="fc8_weights", initializer=Uniform(-stdv, stdv)),
            bias_attr=ParamAttr(name="fc8_offset", initializer=Uniform(-stdv, stdv)),
        )

    def forward(self, inputs):
        x = self._conv1(inputs)
        x = self._conv2(x)
        x = self._conv3(x)
        x = F.relu(x)
        x = self._conv4(x)
        x = F.relu(x)
        x = self._conv5(x)
        x = paddle.flatten(x, start_axis=1, stop_axis=-1)
        x = self._drop1(x)
        x = self._fc6(x)
        x = F.relu(x)
        x = self._drop2(x)
        x = self._fc7(x)
        x = F.relu(x)
        x = self._fc8(x)
        return x


def AlexNet(**args):
    model = AlexNetDY(**args)
    return model


def test_alexnet():
    load_paddle_module_and_check(
        AlexNet, input_size=(1, 3, 224, 224), train_flag=False, flow_weight_dir="/tmp/oneflow"
    )
