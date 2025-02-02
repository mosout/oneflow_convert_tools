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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import paddle
from paddle import ParamAttr
import paddle.nn as nn
import paddle.nn.functional as F
from paddle.nn import Conv2D, BatchNorm, Linear, Dropout
from paddle.nn import AdaptiveAvgPool2D, MaxPool2D, AvgPool2D
from paddle.nn.initializer import Uniform

import math

__all__ = ["ResNet18", "ResNet34", "ResNet50", "ResNet101", "ResNet152"]

from oneflow_onnx.x2oneflow.util import load_paddle_module_and_check


class ConvBNLayer(nn.Layer):
    def __init__(
        self,
        num_channels,
        num_filters,
        filter_size,
        stride=1,
        groups=1,
        act=None,
        name=None,
        data_format="NCHW",
    ):
        super(ConvBNLayer, self).__init__()

        self._conv = Conv2D(
            in_channels=num_channels,
            out_channels=num_filters,
            kernel_size=filter_size,
            stride=stride,
            padding=(filter_size - 1) // 2,
            groups=groups,
            weight_attr=ParamAttr(name=name + "_weights"),
            bias_attr=False,
            data_format=data_format,
        )
        if name == "conv1":
            bn_name = "bn_" + name
        else:
            bn_name = "bn" + name[3:]
        self._batch_norm = BatchNorm(
            num_filters,
            act=act,
            param_attr=ParamAttr(name=bn_name + "_scale"),
            bias_attr=ParamAttr(bn_name + "_offset"),
            moving_mean_name=bn_name + "_mean",
            moving_variance_name=bn_name + "_variance",
            data_layout=data_format,
        )

    def forward(self, inputs):
        y = self._conv(inputs)
        y = self._batch_norm(y)
        return y


class BottleneckBlock(nn.Layer):
    def __init__(
        self,
        num_channels,
        num_filters,
        stride,
        shortcut=True,
        name=None,
        data_format="NCHW",
    ):
        super(BottleneckBlock, self).__init__()

        self.conv0 = ConvBNLayer(
            num_channels=num_channels,
            num_filters=num_filters,
            filter_size=1,
            act="relu",
            name=name + "_branch2a",
            data_format=data_format,
        )
        self.conv1 = ConvBNLayer(
            num_channels=num_filters,
            num_filters=num_filters,
            filter_size=3,
            stride=stride,
            act="relu",
            name=name + "_branch2b",
            data_format=data_format,
        )
        self.conv2 = ConvBNLayer(
            num_channels=num_filters,
            num_filters=num_filters * 4,
            filter_size=1,
            act=None,
            name=name + "_branch2c",
            data_format=data_format,
        )

        if not shortcut:
            self.short = ConvBNLayer(
                num_channels=num_channels,
                num_filters=num_filters * 4,
                filter_size=1,
                stride=stride,
                name=name + "_branch1",
                data_format=data_format,
            )

        self.shortcut = shortcut

        self._num_channels_out = num_filters * 4

    def forward(self, inputs):
        y = self.conv0(inputs)
        conv1 = self.conv1(y)
        conv2 = self.conv2(conv1)

        if self.shortcut:
            short = inputs
        else:
            short = self.short(inputs)

        y = paddle.add(x=short, y=conv2)
        y = F.relu(y)
        return y


class BasicBlock(nn.Layer):
    def __init__(
        self,
        num_channels,
        num_filters,
        stride,
        shortcut=True,
        name=None,
        data_format="NCHW",
    ):
        super(BasicBlock, self).__init__()
        self.stride = stride
        self.conv0 = ConvBNLayer(
            num_channels=num_channels,
            num_filters=num_filters,
            filter_size=3,
            stride=stride,
            act="relu",
            name=name + "_branch2a",
            data_format=data_format,
        )
        self.conv1 = ConvBNLayer(
            num_channels=num_filters,
            num_filters=num_filters,
            filter_size=3,
            act=None,
            name=name + "_branch2b",
            data_format=data_format,
        )

        if not shortcut:
            self.short = ConvBNLayer(
                num_channels=num_channels,
                num_filters=num_filters,
                filter_size=1,
                stride=stride,
                name=name + "_branch1",
                data_format=data_format,
            )

        self.shortcut = shortcut

    def forward(self, inputs):
        y = self.conv0(inputs)
        conv1 = self.conv1(y)

        if self.shortcut:
            short = inputs
        else:
            short = self.short(inputs)
        y = paddle.add(x=short, y=conv1)
        y = F.relu(y)
        return y


class ResNet(nn.Layer):
    def __init__(
        self, layers=50, class_dim=1000, input_image_channel=3, data_format="NCHW"
    ):
        super(ResNet, self).__init__()

        self.layers = layers
        self.data_format = data_format
        self.input_image_channel = input_image_channel

        supported_layers = [18, 34, 50, 101, 152]
        assert (
            layers in supported_layers
        ), "supported layers are {} but input layer is {}".format(
            supported_layers, layers
        )

        if layers == 18:
            depth = [2, 2, 2, 2]
        elif layers == 34 or layers == 50:
            depth = [3, 4, 6, 3]
        elif layers == 101:
            depth = [3, 4, 23, 3]
        elif layers == 152:
            depth = [3, 8, 36, 3]
        num_channels = [64, 256, 512, 1024] if layers >= 50 else [64, 64, 128, 256]
        num_filters = [64, 128, 256, 512]

        self.conv = ConvBNLayer(
            num_channels=self.input_image_channel,
            num_filters=64,
            filter_size=7,
            stride=2,
            act="relu",
            name="conv1",
            data_format=self.data_format,
        )
        self.pool2d_max = MaxPool2D(
            kernel_size=3, stride=2, padding=1, data_format=self.data_format
        )

        self.block_list = []
        if layers >= 50:
            for block in range(len(depth)):
                shortcut = False
                for i in range(depth[block]):
                    if layers in [101, 152] and block == 2:
                        if i == 0:
                            conv_name = "res" + str(block + 2) + "a"
                        else:
                            conv_name = "res" + str(block + 2) + "b" + str(i)
                    else:
                        conv_name = "res" + str(block + 2) + chr(97 + i)
                    bottleneck_block = self.add_sublayer(
                        conv_name,
                        BottleneckBlock(
                            num_channels=num_channels[block]
                            if i == 0
                            else num_filters[block] * 4,
                            num_filters=num_filters[block],
                            stride=2 if i == 0 and block != 0 else 1,
                            shortcut=shortcut,
                            name=conv_name,
                            data_format=self.data_format,
                        ),
                    )
                    self.block_list.append(bottleneck_block)
                    shortcut = True
        else:
            for block in range(len(depth)):
                shortcut = False
                for i in range(depth[block]):
                    conv_name = "res" + str(block + 2) + chr(97 + i)
                    basic_block = self.add_sublayer(
                        conv_name,
                        BasicBlock(
                            num_channels=num_channels[block]
                            if i == 0
                            else num_filters[block],
                            num_filters=num_filters[block],
                            stride=2 if i == 0 and block != 0 else 1,
                            shortcut=shortcut,
                            name=conv_name,
                            data_format=self.data_format,
                        ),
                    )
                    self.block_list.append(basic_block)
                    shortcut = True

        self.pool2d_avg = AdaptiveAvgPool2D(1, data_format=self.data_format)

        self.pool2d_avg_channels = num_channels[-1] * 2

        stdv = 1.0 / math.sqrt(self.pool2d_avg_channels * 1.0)

        self.out = Linear(
            self.pool2d_avg_channels,
            class_dim,
            weight_attr=ParamAttr(initializer=Uniform(-stdv, stdv), name="fc_0.w_0"),
            bias_attr=ParamAttr(name="fc_0.b_0"),
        )

    def forward(self, inputs):
        with paddle.static.amp.fp16_guard():
            if self.data_format == "NHWC":
                inputs = paddle.tensor.transpose(inputs, [0, 2, 3, 1])
                inputs.stop_gradient = True
            y = self.conv(inputs)
            y = self.pool2d_max(y)
            for block in self.block_list:
                y = block(y)
            y = self.pool2d_avg(y)
            y = paddle.reshape(y, shape=[-1, self.pool2d_avg_channels])
            y = self.out(y)
            return y


def ResNet18(**args):
    model = ResNet(layers=18, **args)
    return model


def ResNet34(**args):
    model = ResNet(layers=34, **args)
    return model


def ResNet50(**args):
    model = ResNet(layers=50, **args)
    return model


def ResNet101(**args):
    model = ResNet(layers=101, **args)
    return model


def ResNet152(**args):
    model = ResNet(layers=152, **args)
    return model


def test_ResNet18():
    load_paddle_module_and_check(
        ResNet18, input_size=(1, 3, 224, 224), train_flag=False, flow_weight_dir="/tmp/oneflow", oneflow_code_gen_flag=True
    )
