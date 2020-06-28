/*
 *  ngpu_nest_interface.h
 *
 */

#ifndef NGPU_NEST_INTERFACE_H
#define NGPU_NEST_INTERFACE_H

// Generated includes:
//#include "config.h"
#include <sstream>

// Includes from nestkernel:
//#include "archiving_node.h"
#include "node.h"
#include "connection.h"
#include "event.h"
#include "nest_types.h"
#include "ring_buffer.h"
#include "universal_data_logger.h"

namespace nest
{

class ngpu_nest_interface : public Node // Archiving_Node
{

public:
  ngpu_nest_interface();
  ngpu_nest_interface( const ngpu_nest_interface& );
  virtual ~ngpu_nest_interface();


  /**
   * Import sets of overloaded virtual functions.
   * @see Technical Issues / Virtual Functions: Overriding, Overloading, and
   * Hiding
   */
  using Node::handle;
  using Node::handles_test_event;

  port send_test_event( Node&, rport, synindex, bool );

  void handle( SpikeEvent& );

  port handles_test_event( SpikeEvent&, rport );

  void get_status( DictionaryDatum& ) const;
  void set_status( const DictionaryDatum& );

  int AddNode(int nest_node_id, int node_image_id);

private:
  std::vector< int > nest_node_id_;     // global ids of NEST nodes
  std::vector< int > node_image_id_;     // ids of node images in NeuronGPU

  void init_state_( const Node& proto );
  void init_buffers_();
  void calibrate();
  void update( Time const&, const long, const long );

  // The next three classes need to be friends to access the State_ class/member
  friend class DynamicRecordablesMap< ngpu_nest_interface >;
  friend class DynamicUniversalDataLogger< ngpu_nest_interface >;
  friend class DataAccessFunctor< ngpu_nest_interface >;
  // ----------------------------------------------------------------

  
  inline size_t
    n_receptors() const
  {
    return nest_node_id_.size();
  };

  // ----------------------------------------------------------------

  /**
   * Buffers of the model.
   */

  std::vector<std::vector<int> > spike_target_buffer_;
  // ----------------------------------------------------------------


  //! Mapping of recordables names to access functions
  DynamicRecordablesMap< ngpu_nest_interface > recordablesMap_;

  // Data Access Functor getter
  DataAccessFunctor< ngpu_nest_interface > get_data_access_functor( size_t elem );
  // Utility function that inserts the synaptic conductances to the
  // recordables map

  Name get_g_receptor_name( size_t receptor );
  void insert_conductance_recordables( size_t first = 0 );
};

inline port
ngpu_nest_interface::send_test_event( Node& target, rport receptor_type,
				      synindex, bool )
{
  SpikeEvent e;
  e.set_sender( *this );

  return target.handles_test_event( e, receptor_type );
}

inline void
ngpu_nest_interface::get_status( DictionaryDatum& d ) const
{
}

} // namespace

#endif // NGPU_NEST_INTERFACE_H //
