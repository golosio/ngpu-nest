import neurongpu as ngpu
import nest
import ngpu_nest
import numpy as np

neuron = ngpu.Create('aeif_cond_beta',1, 4)
ngpu.SetStatus(neuron, {"V_peak": 0.0, "a": 4.0, "b":80.5})
ngpu.SetStatus(neuron, {'E_rev':[0.0,0.0,0.0,-85.0],
                        'tau_decay':[50.0,20.0,20.0,20.0],
                        'tau_rise':[10.0,10.0,1.0,1.0]})

spike = nest.Create('spike_generator', params = {'spike_times':
                                                     np.array([10.0])})

spike_image = ngpu_nest.CreateNeuronImage(spike, 1)

delay=[1.0, 300.0, 500.0, 700.0]
w=[1.0, 1.0, 1.0, 1.0]
conn_spec={"rule": "all_to_all"}
for syn in range(4):
    syn_spec={'receptor': syn, 'weight': w[syn], 'delay': delay[syn]}
    ngpu.Connect(spike_image, neuron, conn_spec, syn_spec)

record = ngpu.CreateRecord("", ["V_m"], [neuron[0]], [0])

nest.Simulate(1000.0)

data_list = ngpu.GetRecordData(record)
t=[row[0] for row in data_list]
V_m=[row[1] for row in data_list]

import matplotlib.pyplot as plt

plt.figure(1)
plt.plot(t, V_m)

plt.draw()
plt.pause(1)
ngpu.waitenter("<Hit Enter To Close>")
plt.close()

