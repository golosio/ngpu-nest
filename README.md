# ngpu-nest
Interface between NeuronGPU and NEST, that offers the possibility of creating networks of NEST and NeuronGPU neurons, connected among each other, and to manage a quick exchange of spikes between NEST and NeuronGPU in both directions. With this interface, the NEST capabilities can be further extended to include the possibility of simulation on GPU supports.
Using the interface is very simple. It is sufficient to import the Python module of the interface, and to use the command CreateNeuronImage to create the images of the NEST neurons in the GPU. The second argument is the number of receptor ports.
See the following sample code and the Python test scripts.
```
import neurongpu as ngpu
import nest
import ngpu_nest

nest_neuron=nest.Create("aeif_cond_alpha",5)
node_image = ngpu_nest.CreateNeuronImage(nest_neuron, 1)

nest.SetStatus(nest_neuron, {"I_e":800.0})

spike_det = ngpu.Create("spike_detector",5)
conn_dict={"rule": "one_to_one"}
syn_dict={"weight": 1.0, "delay": 1.0}
ngpu.Connect(node_image, spike_det, conn_dict, syn_dict)
```
