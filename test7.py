import sys
import ctypes
import neurongpu as ngpu
import nest
import ngpu_nest
from random import randrange

if len(sys.argv) != 2:
    print ("Usage: python %s n_neurons" % sys.argv[0])
    quit()
    
order = int(sys.argv[1])//5

n_test = 100

print("Building ...")

ngpu.SetRandomSeed(1234) # seed for GPU random numbers

n_receptors = 2

NE = 4 * order       # number of excitatory neurons
NI = 1 * order       # number of inhibitory neurons
n_neurons = NE + NI  # number of neurons in total

CE = 800   # number of excitatory synapses per neuron
CI = CE//4  # number of inhibitory synapses per neuron

Wex = 0.05
Win = 0.35

# poisson generator parameters
poiss_rate = 20000.0 # poisson signal rate in Hz
poiss_weight = 0.37
poiss_delay = 0.2 # poisson signal delay in ms

# create poisson generator
pg = ngpu.Create("poisson_generator")
ngpu.SetStatus(pg, "rate", poiss_rate)

# Create n_neurons neurons with n_receptor receptor ports
neuron = ngpu.Create("aeif_cond_beta", n_neurons, n_receptors)
exc_neuron = neuron[0:NE]      # excitatory neurons
inh_neuron = neuron[NE:n_neurons]   # inhibitory neurons
  
# receptor parameters
E_rev = [0.0, -85.0]
tau_decay = [1.0, 1.0]
tau_rise = [1.0, 1.0]

ngpu.SetStatus(neuron, {"E_rev":E_rev, "tau_decay":tau_decay,
                        "tau_rise":tau_rise, "t_ref":0.5})

nest_neuron = nest.Create("aeif_cond_beta_multisynapse", n_test)
nest.SetStatus(nest_neuron, {"E_rev":E_rev, "tau_decay":tau_decay,
                             "tau_rise":tau_rise, "t_ref":0.5})

neuron_image = ngpu_nest.CreateNeuronImage(nest_neuron, 3)

mean_delay = 0.5
std_delay = 0.25
min_delay = 0.1
# Excitatory connections
# connect excitatory neurons to port 0 of all neurons
# normally distributed delays, weight Wex and CE connections per neuron
exc_conn_dict={"rule": "fixed_indegree", "indegree": CE}
exc_syn_dict={"weight": Wex, "delay": {"distribution":"normal_clipped",
                                       "mu":mean_delay, "low":min_delay,
                                       "high":mean_delay+3*std_delay,
                                       "sigma":std_delay}, "receptor":0}
ngpu.Connect(exc_neuron, neuron, exc_conn_dict, exc_syn_dict)

exc_syn_dict1={"weight": Wex, "delay": {"distribution":"normal_clipped",
                                        "mu":mean_delay, "low":min_delay,
                                        "high":mean_delay+3*std_delay,
                                        "sigma":std_delay}, "receptor":1}

ngpu.Connect(exc_neuron, neuron_image, exc_conn_dict, exc_syn_dict1)

# Inhibitory connections
# connect inhibitory neurons to port 1 of all neurons
# normally distributed delays, weight Win and CI connections per neuron
inh_conn_dict={"rule": "fixed_indegree", "indegree": CI}
inh_syn_dict={"weight": Win, "delay":{"distribution":"normal_clipped",
                                      "mu":mean_delay, "low":min_delay,
                                      "high":mean_delay+3*std_delay,
                                      "sigma":std_delay}, "receptor":1}
ngpu.Connect(inh_neuron, neuron, inh_conn_dict, inh_syn_dict)

inh_syn_dict1={"weight": Win, "delay":{"distribution":"normal_clipped",
                                       "mu":mean_delay, "low":min_delay,
                                       "high":mean_delay+3*std_delay,
                                       "sigma":std_delay}, "receptor":2}
ngpu.Connect(inh_neuron, neuron_image, inh_conn_dict, inh_syn_dict1)


#connect poisson generator to port 0 of all neurons
pg_conn_dict={"rule": "all_to_all"}
pg_syn_dict={"weight": poiss_weight, "delay": poiss_delay, "receptor":0}

ngpu.Connect(pg, neuron, pg_conn_dict, pg_syn_dict)

pg_syn_dict1={"weight": poiss_weight, "delay": poiss_delay, "receptor":1}

ngpu.Connect(pg, neuron_image, pg_conn_dict, pg_syn_dict1)

sd = ngpu.Create("spike_detector", n_test)
sd_conn_dict={"rule": "one_to_one"}
sd_syn_dict={"weight": 1.0, "delay": 1.0}
i_neuron_list = []
i_receptor_list = []
var_name_list = []
for i in range(n_test):
    ngpu.Connect([neuron[randrange(n_neurons)]], [sd[i]], sd_conn_dict,
                 sd_syn_dict)
    i_neuron_list.append(sd[i])
    i_receptor_list.append(0)
    var_name_list.append("spike_height")

# create multimeter record of spikes
record = ngpu.CreateRecord("", var_name_list, i_neuron_list, i_receptor_list)

nest_sd = nest.Create('spike_detector', n_test)
nest.Connect(nest_neuron, nest_sd, sd_conn_dict, sd_syn_dict)

nest.Simulate(1000)

data_list = ngpu.GetRecordData(record)
t=[row[0] for row in data_list]
spike_height=[row[1] for row in data_list]

import matplotlib.pyplot as plt

plt.figure(1)
plt.plot(t, spike_height)

row_sum = data_list[0]
for row in data_list[1:len(data_list)]:
    for i in range(len(row_sum)):
        row_sum[i] = row_sum[i] + row[i]

spike = row_sum[1:len(row_sum)]

import numpy as np
spike_arr = np.array(spike)

mean_spike_num = np.mean(spike_arr)
#diff = abs(mean_spike_num - 30.78)
#max_diff = 3.0*np.sqrt(30.78)/np.sqrt(n_test)
std_spike_num = np.std(spike_arr)
print("NGPU mean spike num. ", mean_spike_num)
print("NGPU spike num. STD", std_spike_num)

n_events = []
for i in range(n_test):
    n_events.append(nest.GetStatus(nest_sd, "n_events")[i])

n_events_arr = np.array(n_events)
print("NEST mean spike num. ", np.mean(n_events_arr))
print("NEST spike num. STD", np.std(n_events_arr))

plt.draw()
plt.pause(0.5)
ngpu.waitenter("<Hit Enter To Close>")
plt.close()
