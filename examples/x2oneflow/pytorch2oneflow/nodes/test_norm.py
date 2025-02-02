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
import torch.nn.functional as F

from oneflow_onnx.x2oneflow.util import load_pytorch_module_and_check


def test_bn():
    class Net(nn.Module):
        def __init__(self):
            super(Net, self).__init__()
            self.bn = nn.BatchNorm2d(4)

        def forward(self, x):
            x = self.bn(x)
            return x

    load_pytorch_module_and_check(Net)

# def test_gn_v1():
#     class Net(nn.Module):
#         def forward(self, x):
#             # Separate 6 channels into 3 groups
#             m = nn.GroupNorm(6, 6)
#             output = m(x)
#             return output
    
#     load_pytorch_module_and_check(Net, input_size=(20, 6, 10, 10))
