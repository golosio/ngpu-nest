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

record_n = ngpu.CreateRecord("", ["spike"], [node_image[0]], [0])

record_sd = ngpu.CreateRecord("", ["spike_height"], [spike_det[0]], [0])

multimeter = nest.Create("multimeter")
multimeter.set(record_from=["V_m"])
nest.Connect(multimeter, nest_neuron)


nest_neuron2 = nest.Create("aeif_cond_alpha",1)
node_image2 = ngpu_nest.CreateNeuronImage(nest_neuron2, 1)

spike = ngpu.Create("spike_generator")
spike_times = [50.0, 100.0, 400.0, 600.0]
n_spikes = 4

# set spike times and heights
ngpu.SetStatus(spike, {"spike_times": spike_times})
delay = [1.0, 50.0, 100.0]
weight = [0.1, 0.2, 0.5]

conn_spec={"rule": "all_to_all"}
for syn in range(1):
    syn_spec={'receptor': syn, 'weight': weight[syn], 'delay': delay[syn]}
    ngpu.Connect(spike, node_image2, conn_spec, syn_spec)

i_neuron_arr = [node_image2[0]]
i_receptor_arr = [0]
var_name_arr = ["port_value"]
record = ngpu.CreateRecord("", var_name_arr, i_neuron_arr,
                           i_receptor_arr)


#print (nest_neuron2[0].global_id)
nest.Simulate(800)

data_sd = ngpu.GetRecordData(record_sd)
t_sd=[row[0] for row in data_sd]
spike_sd=[70.0*row[1]-70.0 for row in data_sd]


dmm = multimeter.get()
Vms = dmm["events"]["V_m"]
ts = dmm["events"]["times"]

import matplotlib.pyplot as plt

plt.figure(1)
plt.plot(t_sd, spike_sd, 'r')

#plt.figure(2)
plt.plot(ts, Vms)


data_list = ngpu.GetRecordData(record)
t=[row[0] for row in data_list]
val1=[row[1] for row in data_list]
#val2=[row[2] for row in data_list]
#val3=[row[3] for row in data_list]

fig3 = plt.figure(3)
plt.plot(t, val1)

plt.draw()
plt.pause(1)
ngpu.waitenter("<Hit Enter To Close>")
plt.close()

