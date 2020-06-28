""" Python interface between NeuronGPU and NEST"""
import sys, platform
import ctypes, ctypes.util
import os
import unicodedata
import nest
import neurongpu

print('-----------------------------------------------------------------')
print('Python interface between NeuronGPU and NEST')
print('-----------------------------------------------------------------')

lib_path="libngpu_nest.so"
_ngpu_nest=ctypes.CDLL(lib_path)

ngpu_nest_Init = _ngpu_nest.ngpu_nest_Init
ngpu_nest_Init.restype = ctypes.c_int
ngpu_nest_Init()
ngpu_nest_interface = nest.Create("ngpu")

ngpu_nest_AddNode = _ngpu_nest.ngpu_nest_AddNode
ngpu_nest_AddNode.argtypes = (ctypes.c_int, ctypes.c_int)
ngpu_nest_AddNode.restype = ctypes.c_int
def AddNode(nest_node_id, node_image_id):
    "Add node to NeuronGPU NEST interface"
    return ngpu_nest_AddNode(ctypes.c_int(nest_node_id), \
                             ctypes.c_int(node_image_id))

def CreateNeuronImage(nodes, n_port):
    dt = nest.GetKernelStatus("resolution")
    n_nodes = len(nodes)
    node_image = neurongpu.Create("ext_neuron", n_nodes, n_port)
    for i in range(n_nodes):
        nest_node_id = nodes[i].global_id
        i_port = AddNode(nest_node_id, node_image[i])
        syn_dict={"weight":1.0, "delay":dt, "receptor_type": i_port}
        nest.Connect(nodes[i], ngpu_nest_interface, "one_to_one", syn_dict)
    return node_image


