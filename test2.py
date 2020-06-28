import neurongpu as ngpu
import nest
import ngpu_nest
import numpy as np

neuron = nest.Create('aeif_cond_beta_multisynapse')
nest.SetStatus(neuron, {"V_peak": 0.0, "a": 4.0, "b":80.5})
nest.SetStatus(neuron, {'E_rev':[0.0,0.0,0.0,-85.0],
                        'tau_decay':[50.0,20.0,20.0,20.0],
                        'tau_rise':[10.0,10.0,1.0,1.0]})

neuron_image = ngpu_nest.CreateNeuronImage(neuron, 5)


spike = ngpu.Create('spike_generator')
ngpu.SetStatus(spike, {'spike_times': [10.0]})

voltmeter = nest.Create('voltmeter')

delays=[1.0, 300.0, 500.0, 700.0]
w=[1.0, 1.0, 1.0, 1.0]
conn_spec={"rule": "one_to_one"}
for syn in range(4):
    syn_spec={'receptor': 1 + syn,
              'weight': w[syn],
              'delay': delays[syn]}
    ngpu.Connect(spike, neuron_image, conn_spec, syn_spec)

nest.Connect(voltmeter, neuron)

nest.Simulate(1000.0)
dmm = nest.GetStatus(voltmeter)[0]
Vms = dmm["events"]["V_m"]
ts = dmm["events"]["times"]
import matplotlib.pyplot as plt
plt.figure(2)
plt.plot(ts, Vms)

plt.draw()
plt.pause(1)
ngpu.waitenter("<Hit Enter To Close>")
plt.close()
