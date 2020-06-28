import sys
import neurongpu as ngpu
import nest
import ngpu_nest
import numpy as np

if len(sys.argv) != 2:
    print ("Usage: python %s n_neurons" % sys.argv[0])
    quit()
    
n_ngpu = int(sys.argv[1])
n_nest = 1000
indegree = 1000

ngpu_neuron = ngpu.Create("aeif_cond_beta", n_ngpu)
# receptor parameters
E_rev = [0.0]
tau_rise = [2.0]
tau_decay = [20.0]

ngpu.SetStatus(ngpu_neuron, {"E_rev":E_rev, "tau_decay":tau_decay,
                             "tau_rise":tau_rise})

nest_neuron = nest.Create("aeif_cond_beta_multisynapse", n_nest)
nest.SetStatus(nest_neuron, {"E_rev":E_rev, "tau_decay":tau_decay,
                             "tau_rise":tau_rise})

neuron_image = ngpu_nest.CreateNeuronImage(nest_neuron, 2)

poiss_gen = ngpu.Create("poisson_generator");
ngpu.SetStatus(poiss_gen, "rate", 10000.0)
conn_dict={"rule": "all_to_all"}

syn_dict={"weight": 0.05, "delay": 1.0, "receptor":0}
syn_dict1={"weight": 0.05, "delay": 1.0, "receptor":1}

ngpu.Connect(poiss_gen, ngpu_neuron, conn_dict, syn_dict)
ngpu.Connect(poiss_gen, neuron_image, conn_dict, syn_dict1)

neur_conn_dict={"rule": "fixed_indegree", "indegree": indegree}
neur_syn_dict={"weight": 0.005, "delay": 1.0, "receptor":0}
neur_syn_dict1={"weight": 0.005, "delay": 1.0, "receptor":1}

ngpu.Connect(ngpu_neuron, ngpu_neuron, neur_conn_dict, neur_syn_dict)
ngpu.Connect(ngpu_neuron, neuron_image, neur_conn_dict, neur_syn_dict1)


record = ngpu.CreateRecord("", ["V_m"], [ngpu_neuron[0]], [0])
voltmeter = nest.Create('voltmeter')
nest.Connect(voltmeter, nest_neuron[0])

nest.Simulate(1000)

data_list = ngpu.GetRecordData(record)
t=[row[0] for row in data_list]
Vm=[row[1] for row in data_list]
dmm = nest.GetStatus(voltmeter)[0]
t1 = dmm["events"]["times"]
Vm1 = dmm["events"]["V_m"]

import matplotlib.pyplot as plt

plt.figure(1)
plt.plot(t, Vm)

plt.figure(2)
plt.plot(t1, Vm1)

plt.draw()
plt.pause(1)
ngpu.waitenter("<Hit Enter To Close>")
plt.close()
