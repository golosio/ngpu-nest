import neurongpu as ngpu
import nest
import ngpu_nest
import numpy as np

ngpu_neuron = ngpu.Create("aeif_cond_beta")
# receptor parameters
E_rev = [0.0]
tau_rise = [2.0]
tau_decay = [20.0]


ngpu.SetStatus(ngpu_neuron, {"E_rev":E_rev, "tau_decay":tau_decay,
                             "tau_rise":tau_rise})

nest_neuron = nest.Create("aeif_cond_beta_multisynapse")
nest.SetStatus(nest_neuron, {"E_rev":E_rev, "tau_decay":tau_decay,
                             "tau_rise":tau_rise})

neuron_image = ngpu_nest.CreateNeuronImage(nest_neuron, 2)

poiss_gen = ngpu.Create("poisson_generator");
ngpu.SetStatus(poiss_gen, "rate", 12000.0)

parrot = ngpu.Create("parrot_neuron");
ngpu.SetStatus(parrot, {'hold_spike_height': 1})

conn_dict={"rule": "one_to_one"}
syn_dict_pg={"weight": 1.0, "delay": 1.0}
ngpu.Connect(poiss_gen, parrot, conn_dict, syn_dict_pg)

syn_dict={"weight": 0.05, "delay": 2.0, "receptor":0}
syn_dict1={"weight": 0.05, "delay": 2.0, "receptor":1}

ngpu.Connect(parrot, ngpu_neuron, conn_dict, syn_dict)
ngpu.Connect(parrot, neuron_image, conn_dict, syn_dict1)
record = ngpu.CreateRecord("", ["V_m"], [ngpu_neuron[0]], [0])
voltmeter = nest.Create('voltmeter')
nest.Connect(voltmeter, nest_neuron)

nest.Simulate(1000)

data_list = ngpu.GetRecordData(record)
t=[row[0] for row in data_list]
Vm=[row[1] for row in data_list]
dmm = nest.GetStatus(voltmeter)[0]
t1 = dmm["events"]["times"]
Vm1 = dmm["events"]["V_m"]

import matplotlib.pyplot as plt

plt.figure(1)
plt.plot(t, Vm, label='NGPU')

#plt.figure(2)
plt.plot(t1, Vm1, label='NEST')

plt.xlabel('time (ms)')
plt.ylabel('Vm')

plt.legend(loc='lower center')

plt.draw()
plt.pause(1)
ngpu.waitenter("<Hit Enter To Close>")
plt.close()
