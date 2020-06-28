
#include "ngpu_nest_interface.h"

// C++ includes:
#include <limits>

// Includes from libnestutil:
#include "dict_util.h"

// Includes from nestkernel:
#include "exceptions.h"
#include "kernel_manager.h"
#include "universal_data_logger_impl.h"

// Includes from sli:
#include "dict.h"
#include "dictutils.h"
#include "doubledatum.h"
#include "integerdatum.h"


#include "model_manager.h"
#include "model_manager_impl.h"
#include "genericmodel.h"
#include "genericmodel_impl.h"
#include "spike_buffer.h"

#include "neurongpu_C.h"

/*
extern "C" {
  int NeuronGPU_Simulate();
  int NeuronGPU_SimulationStep();
  int NeuronGPU_SetSimTime(float sim_time);
  int NeuronGPU_PushSpikesToNodes(int n_spikes, int *node_id);
  int NeuronGPU_SetVerbosityLevel(int verbosity_level);
  int NeuronGPU_GetExtNeuronInputSpikes(int *n_spikes, int **node, int **port,
					float **spike_height,
					int include_zeros);

}
*/
  
namespace nest // template specialization must be placed in namespace
{

  ngpu_nest_interface *ngpu_nest_interface_instance;
/* ----------------------------------------------------------------
 * Recordables map
 * ---------------------------------------------------------------- */

// Override the create() method with one call to
// DynamicRecordablesMap::insert() for each quantity to be recorded.
template <>
void
DynamicRecordablesMap< ngpu_nest_interface >::create( ngpu_nest_interface& host )
{
  // use standard names wherever you can for consistency!
  //insert( names::V_m, host.get_data_access_functor( ngpu_nest_interface::State_::V_M ) );

  //insert( names::w, host.get_data_access_functor( ngpu_nest_interface::State_::W ) );

  //host.insert_conductance_recordables();
}

/* ----------------------------------------------------------------
 * Default constructors defining default parameters and state
 * ---------------------------------------------------------------- */

ngpu_nest_interface::ngpu_nest_interface()
  : Node()
{
  recordablesMap_.create( *this );
  ngpu_nest_interface_instance = this;
}

ngpu_nest_interface::ngpu_nest_interface( const ngpu_nest_interface& n )
  : Node( n )
{
  // deve dare errore!!!
  recordablesMap_.create( *this );
  ngpu_nest_interface_instance = this;
}

ngpu_nest_interface::~ngpu_nest_interface()
{
}

/* ----------------------------------------------------------------
 * Node initialization functions
 * ---------------------------------------------------------------- */

void
ngpu_nest_interface::init_state_( const Node& proto )
{
  //const ngpu_nest_interface& pr = downcast< ngpu_nest_interface >( proto );
  //S_ = pr.S_;
}


/* ----------------------------------------------------------------
 * Default and copy constructor for node, and destructor
 * ---------------------------------------------------------------- */

/* ----------------------------------------------------------------
 * Node initialization functions
 * ---------------------------------------------------------------- */

void
ngpu_nest_interface::init_buffers_()
{
  for (uint i=0; i<spike_target_buffer_.size(); i++) {
    spike_target_buffer_[i].clear();   // includes resize
    //B_.step_ = Time::get_resolution().get_ms();
  }
}

void
ngpu_nest_interface::calibrate()
{
  //spike_target_buffer_.resize( n_receptors() );
  for (uint i=0; i<spike_target_buffer_.size(); i++) {
    spike_target_buffer_[i].clear();   // includes resize
    //B_.step_ = Time::get_resolution().get_ms();
  }

}

/* ----------------------------------------------------------------
 * Update and spike handling functions
 * ---------------------------------------------------------------- */
void
ngpu_nest_interface::update( Time const& origin, const long from, const long to )
{
  assert( to >= 0 && ( delay ) from < kernel().connection_manager.get_min_delay() );
  assert( from < to );
  assert( from >=0 );
  //std::cout << "update from: " << from << "  to: " << to   << "\n";

  for ( long lag = from; lag < to; ++lag ) // proceed by stepsize B_.step_
  {
    NeuronGPU_SimulationStep();
    /*
    if (lag<spike_target_buffer_.size()) {
      for (uint i=0; i<spike_target_buffer_[lag].size(); i++) {
	int image_id = spike_target_buffer_[lag][i];
	std::cout << "update image id: " << image_id << " lag:" << lag << "\n";
      }
    }
    */
    if (lag<(int)spike_target_buffer_.size()
	&& spike_target_buffer_[lag].size()>0) {
      NeuronGPU_PushSpikesToNodes(spike_target_buffer_[lag].size(),
				  spike_target_buffer_[lag].data());
      spike_target_buffer_[lag].clear();
    }
    int n_spikes;
    int *spike_node;
    int *spike_port;
    float *spike_height;
    NeuronGPU_GetExtNeuronInputSpikes(&n_spikes, &spike_node, &spike_port,
				      &spike_height, false);
    if (n_spikes>0) {
      //std::cout << "Received " << n_spikes << "input spikes from ngpu\n";
      //std::cout << "index\tnode\tport\theight\n";
      for (int i=0; i<n_spikes; i++) {
	//std::cout << i << "\t" << spike_node[i] << "\t" << spike_port[i]
	//	  << "\t" << spike_height[i] << "\n";
	int i_node_image = spike_node[i];
	int pos = (int)(std::find(node_image_id_.begin(), node_image_id_.end(),
				  i_node_image) - node_image_id_.begin());
        if(pos >= (int)node_image_id_.size()) {
	  std::cerr << "Unrecognized node image id\n";
           exit(0);
        }
	int nest_node_id = nest_node_id_[pos];
	//std::cout << "nest node id: " << nest_node_id << "\n";
	Node *nest_node = kernel().node_manager.get_node_or_proxy
			    (nest_node_id);
	SpikeEvent e;
	e.set_sender( *this );
	e.set_receiver(*nest_node);
	e.set_stamp( kernel().simulation_manager.get_slice_origin()
		     + Time::step( lag + 1 ) );
	e.set_weight(spike_height[i]);
	e.set_delay_steps(1);
	e.set_rport(spike_port[i]);
	e();
	//nest_node->handle(e);

      }
    }
    // log state data
    //B_.logger_.record_data( origin.get_steps() + lag );
  } // for-loop

}

port
ngpu_nest_interface::handles_test_event( SpikeEvent&, rport receptor_type )
{
  if ( receptor_type < 0 || receptor_type >= static_cast< port >( n_receptors() ) )
  {
    throw IncompatibleReceptorType( receptor_type, get_name(), "SpikeEvent" );
  }
  //P_.has_connections_ = true;
  return receptor_type;
}

void
ngpu_nest_interface::handle( SpikeEvent& e )
{
  if ( e.get_weight() < 0 )
  {
    throw BadProperty(
      "Synaptic weights for conductance-based multisynapse models "
      "must be positive." );
  }
  assert( ( e.get_rport() >= 0 ) && ( ( size_t ) e.get_rport() < n_receptors() ) );

  //std::cout << "Got spike w:" << e.get_weight() << " port:" << e.get_rport() << "\n";
  //B_.spikes_[ e.get_rport() - 1 ].add_value(
  //  e.get_rel_delivery_steps( kernel().simulation_manager.get_slice_origin() ), e.get_weight() * e.get_multiplicity() );
  int port = e.get_rport();
  int image_id = node_image_id_[port];
  int lag =
    e.get_rel_delivery_steps(kernel().simulation_manager.get_slice_origin())
    - 1;
  assert(lag>=0);
  //std::cout << "image id: " << image_id << " lag:" << lag << "\n";
  while ((int)spike_target_buffer_.size()<=lag) {
    spike_target_buffer_.push_back(std::vector<int>());
  }
  spike_target_buffer_[lag].push_back(image_id);
}

void
ngpu_nest_interface::set_status( const DictionaryDatum& d )
{
}

int ngpu_nest_interface::AddNode(int nest_node_id, int node_image_id)
{
  nest_node_id_.push_back(nest_node_id);
  node_image_id_.push_back(node_image_id);
  return (int)nest_node_id_.size() - 1;
}

  

} // namespace nest

extern "C" {

int ngpu_nest_Init()
{
  NeuronGPU_SetVerbosityLevel(0);
  NeuronGPU_SetSimTime(0.1);
  const Name& name="ngpu";
  int ngpu_model_index = nest::kernel().model_manager.register_node_model<nest::ngpu_nest_interface>(name);
  return ngpu_model_index;
}

int ngpu_nest_AddNode(int nest_node_id, int node_image_id)
{
  return nest::ngpu_nest_interface_instance->AddNode(nest_node_id,
						     node_image_id);
}

}
