import logging as log

import networkx as nx
import numpy as np

from mo.front.extractor import add_attrs_props
from mo.graph.graph import Node, unique_id, dump_graph_for_graphviz
from mo.middle.pattern_match import apply_pattern
from mo.front.extractor import update_ie_fields
from mo.middle.passes.fusing.helpers import backward_bfs, get_next_operation
from mo.utils.graph import pseudo_topological_sort
from mo.middle.passes.infer import partial_infer
from mo.front.common.partial_infer.pooling import pool_explicit_padding_infer
from mo.ops.pooling import Pooling


def _clean_fw_tensor_attrs(node: Node):
    attrs = ['fw_tensor_debug_info']
    for attr in attrs:
        if node.has_valid(attr):
            node[attr] = None


def _insert_pooling(graph: nx.MultiDiGraph, first_node: Node, second_node: Node, spatial_dims):
    """
    This function inserts point wise pooling layer between two nodes
    """
    log.debug("STRIDE PROP: Insert pooling between {} and {}".format(first_node.name, second_node.name))
    stride_prop = second_node.stride_prop
    assert len(graph.get_edge_data(first_node.id, second_node.id)) == 1
    eattrs = graph.get_edge_data(first_node.id, second_node.id)[0]
    graph.remove_edge(first_node.id, second_node.id)

    pooling = Pooling(graph, dict(name='Pooling_', spatial_dims=spatial_dims, window=np.array([1, 1, 1, 1]),
                                  output_spatial_shape=None,
                                  stride=np.array(stride_prop), pad_spatial_shape=np.array([[0, 0], [0, 0]]),
                                  pad=np.array([[0, 0], [0, 0], [0, 0], [0, 0]]), pool_method='avg',
                                  is_partial_inferred=False))
    pooling_data = pooling.create_node_with_data([first_node])

    _clean_fw_tensor_attrs(pooling_data)

    graph.add_edges_from([(pooling_data.id, second_node.id, eattrs)])


def _check_next_ops(next_ops: list):
    """
    This function checks list of operation to determine that all ops has same (not 1,1,1,1) stride_prop attr
    """
    stride_props = []
    for op in next_ops:
        if op.has_valid('stride_prop'):
            stride_props.append(np.array(op.stride_prop))
        else:
            continue

    status = not (len(next_ops) != len(stride_props) or (len(stride_props) > 0 and not all(
        np.array_equal(x, stride_props[0]) and not np.array_equal(x, [1, 1, 1, 1]) for x in stride_props)))
    return stride_props, status


def _simple_stride_prop(graph: nx.MultiDiGraph, node: Node, spatial_dims, supported=True):
    """
    This function handles stride propagation for op nodes. If node is in supported ops dict so this is supported operation and we
    can propagate stride directly via this op (stride_prop will be set by using bottom stride_prop), otherwise we can't and
    stride_prop attr will be set as 1,1,1,1
    """
    next_ops = get_next_operation(node)
    stride_props, all_ops_are_valid = _check_next_ops(next_ops)

    if not supported or not all_ops_are_valid:
        # We have to insert pooling layers
        for op in next_ops:
            if op.has_valid('stride_prop') and not np.array_equal(op.stride_prop[spatial_dims], np.array([1, 1])) and \
                    (op.has_valid('has_stride') == False or op.soft_get('has_stride') == False):
                _insert_pooling(graph, node.out_node(), op, spatial_dims)
        # If Convolution is valid then set `stride_prop` to Convolution stride
        node['stride_prop'] = np.array([1, 1, 1, 1])
        return

    for op in next_ops:
        if op.soft_get('has_stride') == True:
            op.stride = np.array([1, 1, 1, 1])
            log.debug("STRIDE PROP: {} {} strides was moved upper via {}".format(op.type, op.name, node.name))

    node['stride_prop'] = np.array(stride_props[0]) if len(stride_props) > 0 else np.array([1, 1, 1, 1])
    node['is_partial_inferred'] = False
    _clean_fw_tensor_attrs(node.out_node())


def _conv_stride_prop(graph: nx.MultiDiGraph, node: Node, spatial_dims, supported=True):
    """
    This function handles convolution stride propagation. There is two cases: conv->(op) and conv->conv. In first case
    we propagate stride from op, and in second case we also change stride for second conv
    """
    next_ops = get_next_operation(node)
    stride_props, all_ops_are_valid = _check_next_ops(next_ops)

    def _check_convolution(node: Node):
        return node.has_valid('kernel_spatial') and np.array_equal(node.kernel_spatial, np.array([1, 1]))

    # Check that all ops are valid and have same values
    if not all_ops_are_valid:
        # We have to insert pooling layers
        for op in next_ops:
            if op.has_valid('stride_prop') and not np.array_equal(op.stride_prop[spatial_dims], np.array([1, 1])):
                # Insert pooling
                _insert_pooling(graph, node.out_node(), op, spatial_dims)
    elif len(stride_props) > 0:
        node.stride *= stride_props[0]
        log.debug('STRIDE PROP: {} got new strides {}'.format(node.name, node.stride))
        for op in next_ops:
            if op.soft_get('has_stride') == True:
                op.stride = np.array([1, 1, 1, 1])
        node['is_partial_inferred'] = False
        _clean_fw_tensor_attrs(node.out_node())

    # If Convolution is valid then set `stride_prop` to Convolution stride
    node['stride_prop'] = np.array(node.stride) if _check_convolution(node) else np.array([1, 1, 1, 1])


supported_ops = {
    'ReLU': {'stride_prop': _simple_stride_prop, 'attrs': {}},
    'Eltwise': {'stride_prop': _simple_stride_prop, 'attrs': {}},
    'Convolution': {'stride_prop': _conv_stride_prop, 'attrs': {'has_stride': True}},
}


def _stride_propagation(graph: nx.MultiDiGraph, spatial_dims):
    """
    This function do stride propagation for all op nodes
    """
    nodes = [Node(graph, x) for x in pseudo_topological_sort(graph, reverse=True) if Node(graph, x).kind == 'op']

    for node in nodes:
        if node.soft_get('type') in supported_ops:
            op = supported_ops[node.type]
            # Add node attrs
            for key in op['attrs'].keys():
                node[key] = op['attrs'][key]
            op['stride_prop'](graph, node, spatial_dims, True)
        else:
            _simple_stride_prop(graph, node, spatial_dims, False)


def stride_optimization(graph: nx.MultiDiGraph):
    """
    This is main function for stride optimization pass
    """
    layout = graph.graph['layout']
    if layout == 'NCHW':
        spatial_dims = np.array([2, 3])
    elif layout == 'NHWC':
        spatial_dims = np.array([1, 2])
    else:
        log.warning('STRIDE PROP: layout {} is not supported'.format(layout))
        return
    _stride_propagation(graph, spatial_dims)

    nodes = [Node(graph, x) for x in pseudo_topological_sort(graph) if
             Node(graph, x).soft_get('is_partial_inferred') == False]
    for node in nodes:
        node.infer(node)