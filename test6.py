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

n_nest = 1000

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

nest_neuron = nest.Create("aeif_cond_beta_multisynapse", n_nest)
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


i_neuron_arr = [neuron[37], neuron[randrange(n_neurons)], neuron[n_neurons-1]]
i_receptor_arr = [0, 0, 0]
# any set of neuron indexes
# create multimeter record of V_m
var_name_arr = ["V_m", "V_m", "V_m"]
record = ngpu.CreateRecord("", var_name_arr, i_neuron_arr,
                           i_receptor_arr)

voltmeter = nest.Create('voltmeter', 3)
nest.Connect(voltmeter[0], nest_neuron[50])
nest.Connect(voltmeter[1], nest_neuron[130])
nest.Connect(voltmeter[2], nest_neuron[78])

nest.Simulate(1000)

nrows=ngpu.GetRecordDataRows(record)
ncol=ngpu.GetRecordDataColumns(record)
#print nrows, ncol

data_list = ngpu.GetRecordData(record)
t=[row[0] for row in data_list]
V1=[row[1] for row in data_list]
V2=[row[2] for row in data_list]
V3=[row[3] for row in data_list]

dmm1 = nest.GetStatus(voltmeter)[0]
tN1 = dmm1["events"]["times"]
VN1 = dmm1["events"]["V_m"]

dmm2 = nest.GetStatus(voltmeter)[1]
tN2 = dmm2["events"]["times"]
VN2 = dmm2["events"]["V_m"]

dmm3 = nest.GetStatus(voltmeter)[2]
tN3 = dmm3["events"]["times"]
VN3 = dmm3["events"]["V_m"]

import matplotlib.pyplot as plt

fig, axs = plt.subplots(2, 2)
axs[0, 0].plot(t, V1)
axs[0, 0].set_title('NGPU neuron')
axs[0, 1].plot(t, V2)
axs[0, 1].set_title('NGPU neuron')
axs[1, 0].plot(tN1, VN1)
axs[1, 0].set_title('NEST neuron')
axs[1, 1].plot(tN2, VN2)
axs[1, 1].set_title('NEST neuron')

for ax in axs.flat:
    ax.set(xlabel='time (ms)', ylabel='Vm')

fig.tight_layout(pad=1.0)
plt.draw()
plt.pause(0.5)
ngpu.waitenter("<Hit Enter To Close>")
plt.close()
