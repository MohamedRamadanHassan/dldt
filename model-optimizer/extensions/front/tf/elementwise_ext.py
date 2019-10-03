"""
 Copyright (c) 2018-2019 Intel Corporation

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
import logging as log

from extensions.ops.elementwise import Add, Mul, Sub, Div, Maximum, Minimum, Pow, LogicalAnd, LogicalOr, Equal, \
    GreaterEqual, Greater, Less, LessEqual, NotEqual, FloorMod, BiasAdd
from mo.front.extractor import FrontExtractorOp
from mo.front.tf.extractors.utils import tf_dtype_extractor
from mo.ops.eltwise_n import EltwiseNAdd
from mo.ops.power import Power


class AddExtractor(FrontExtractorOp):
    op = 'Add'
    enabled = True

    @classmethod
    def extract(cls, node):
        Add.update_node_stat(node, {'data_type': tf_dtype_extractor(node.pb.attr["T"].type)})
        return cls.enabled


class AddV2Extractor(FrontExtractorOp):
    op = 'AddV2'
    enabled = True

    @staticmethod
    def extract(node):
        Add.update_node_stat(node, {'data_type': tf_dtype_extractor(node.pb.attr["T"].type)})
        return __class__.enabled


class AddNExtractor(FrontExtractorOp):
    op = 'AddN'
    enabled = True

    @classmethod
    def extract(cls, node):
        EltwiseNAdd.update_node_stat(node)
        return cls.enabled


class BiasAddExtractor(FrontExtractorOp):
    op = 'BiasAdd'
    enabled = True

    @classmethod
    def extract(cls, node):
        BiasAdd.update_node_stat(node, {'data_type': tf_dtype_extractor(node.pb.attr["T"].type),
                                        'data_format': node.pb.attr["data_format"].s.decode()})
        return cls.enabled


class MulExtractor(FrontExtractorOp):
    op = 'Mul'
    enabled = True

    @classmethod
    def extract(cls, node):
        Mul.update_node_stat(node, {'data_type': tf_dtype_extractor(node.pb.attr["T"].type)})
        return cls.enabled


class SubExtractor(FrontExtractorOp):
    op = 'Sub'
    enabled = True

    @classmethod
    def extract(cls, node):
        Sub.update_node_stat(node, {'data_type': tf_dtype_extractor(node.pb.attr["T"].type)})
        return cls.enabled


class DivExtractor(FrontExtractorOp):
    op = 'RealDiv'
    enabled = True

    @classmethod
    def extract(cls, node):
        Div.update_node_stat(node, {'data_type': tf_dtype_extractor(node.pb.attr["T"].type)})
        return cls.enabled


class SqrtExtractor(FrontExtractorOp):
    op = 'Sqrt'
    enabled = True

    @classmethod
    def extract(cls, node):
        Power.update_node_stat(node, {'power': 0.5})
        return cls.enabled


class RsqrtExtractor(FrontExtractorOp):
    op = 'Rsqrt'
    enabled = True

    @classmethod
    def extract(cls, node):
        Power.update_node_stat(node, {'power': -0.5})
        return cls.enabled


class SquareExtractor(FrontExtractorOp):
    op = 'Square'
    enabled = True

    @classmethod
    def extract(cls, node):
        # update the attributes of the node
        Power.update_node_stat(node, {'power': 2})
        return cls.enabled


class NegExtractor(FrontExtractorOp):
    op = 'Neg'
    enabled = True

    @classmethod
    def extract(cls, node):
        Power.update_node_stat(node, {'scale': -1})
        return cls.enabled


class ZerosLike(FrontExtractorOp):
    op = 'ZerosLike'
    enabled = True

    @classmethod
    def extract(cls, node):
        Power.update_node_stat(node, {'scale': 0})
        return cls.enabled


class MaximumExtractor(FrontExtractorOp):
    op = 'Maximum'
    enabled = True

    @classmethod
    def extract(cls, node):
        Maximum.update_node_stat(node, {'data_type': tf_dtype_extractor(node.pb.attr["T"].type)})
        return cls.enabled


class MinimumExtractor(FrontExtractorOp):
    op = 'Minimum'
    enabled = True

    @classmethod
    def extract(cls, node):
        Minimum.update_node_stat(node, {'data_type': tf_dtype_extractor(node.pb.attr["T"].type)})
        return cls.enabled


class PowExtractor(FrontExtractorOp):
    op = 'Pow'
    enabled = True

    @classmethod
    def extract(cls, node):
        Pow.update_node_stat(node, {'data_type': tf_dtype_extractor(node.pb.attr["T"].type)})
        return cls.enabled


class LogicalAndFrontExtractor(FrontExtractorOp):
    op = 'LogicalAnd'
    enabled = True

    @classmethod
    def extract(cls, node):
        LogicalAnd.update_node_stat(node)
        return cls.enabled


class LogicalOrFrontExtractor(FrontExtractorOp):
    op = 'LogicalOr'
    enabled = True

    @classmethod
    def extract(cls, node):
        LogicalOr.update_node_stat(node)
        return cls.enabled


class EqualExtractor(FrontExtractorOp):
    op = 'Equal'
    enabled = True

    @classmethod
    def extract(cls, node):
        Equal.update_node_stat(node)
        return cls.enabled


class LessEqualExtractor(FrontExtractorOp):
    op = 'LessEqual'
    enabled = True

    @classmethod
    def extract(cls, node):
        LessEqual.update_node_stat(node)
        return cls.enabled


class LessExtractor(FrontExtractorOp):
    op = 'Less'
    enabled = True

    @classmethod
    def extract(cls, node):
        Less.update_node_stat(node)
        return cls.enabled


class GreaterExtractor(FrontExtractorOp):
    op = 'Greater'
    enabled = True

    @classmethod
    def extract(cls, node):
        Greater.update_node_stat(node)
        return cls.enabled


class GreaterEqualExtractor(FrontExtractorOp):
    op = 'GreaterEqual'
    enabled = True

    @classmethod
    def extract(cls, node):
        GreaterEqual.update_node_stat(node)
        return cls.enabled


class NotEqualExtractor(FrontExtractorOp):
    op = 'NotEqual'
    enabled = True

    @classmethod
    def extract(cls, node):
        NotEqual.update_node_stat(node)
        return cls.enabled


class FloorModFrontExtractor(FrontExtractorOp):
    op = 'FloorMod'
    enabled = True

    @classmethod
    def extract(cls, node):
        FloorMod.update_node_stat(node)
        return cls.enabled