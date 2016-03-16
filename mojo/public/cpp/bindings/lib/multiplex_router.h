// Copyright 2015 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef MOJO_PUBLIC_CPP_BINDINGS_LIB_MULTIPLEX_ROUTER_H_
#define MOJO_PUBLIC_CPP_BINDINGS_LIB_MULTIPLEX_ROUTER_H_

#include <stdint.h>

#include <deque>
#include <map>

#include "base/logging.h"
#include "base/macros.h"
#include "base/memory/ref_counted.h"
#include "base/memory/ref_counted_delete_on_message_loop.h"
#include "base/memory/scoped_ptr.h"
#include "base/memory/weak_ptr.h"
#include "base/synchronization/lock.h"
#include "base/threading/thread_checker.h"
#include "mojo/public/cpp/bindings/callback.h"
#include "mojo/public/cpp/bindings/lib/connector.h"
#include "mojo/public/cpp/bindings/lib/interface_id.h"
#include "mojo/public/cpp/bindings/lib/message_header_validator.h"
#include "mojo/public/cpp/bindings/lib/pipe_control_message_handler.h"
#include "mojo/public/cpp/bindings/lib/pipe_control_message_handler_delegate.h"
#include "mojo/public/cpp/bindings/lib/pipe_control_message_proxy.h"
#include "mojo/public/cpp/bindings/lib/scoped_interface_endpoint_handle.h"

namespace mojo {

class AssociatedGroup;

namespace internal {

class InterfaceEndpointClient;

// MultiplexRouter supports routing messages for multiple interfaces over a
// single message pipe.
//
// It is created on the thread where the master interface of the message pipe
// lives. Although it is ref-counted, it is guarateed to be destructed on the
// same thread.
// Some public methods are only allowed to be called on the creating thread;
// while the others are safe to call from any threads. Please see the method
// comments for more details.
class MultiplexRouter
    : public MessageReceiver,
      public base::RefCountedDeleteOnMessageLoop<MultiplexRouter>,
      public PipeControlMessageHandlerDelegate {
 public:
  // If |set_interface_id_namespace_bit| is true, the interface IDs generated by
  // this router will have the highest bit set.
  MultiplexRouter(bool set_interface_id_namespace_bit,
                  ScopedMessagePipeHandle message_pipe);

  // ---------------------------------------------------------------------------
  // The following public methods are safe to call from any threads.

  // Creates a pair of interface endpoint handles. The method generates a new
  // interface ID and assigns it to the two handles. |local_endpoint| is used
  // locally; while |remote_endpoint| is sent over the message pipe.
  void CreateEndpointHandlePair(ScopedInterfaceEndpointHandle* local_endpoint,
                                ScopedInterfaceEndpointHandle* remote_endpoint);

  // Creates an interface endpoint handle from a given interface ID. The handle
  // is used locally.
  // Typically, this method is used to (1) create an endpoint handle for the
  // master interface; or (2) create an endpoint handle on receiving an
  // interface ID from the message pipe.
  ScopedInterfaceEndpointHandle CreateLocalEndpointHandle(InterfaceId id);

  // Closes an interface endpoint handle.
  void CloseEndpointHandle(InterfaceId id, bool is_local);

  // Attaches an client to the specified endpoint to send and receive messages.
  void AttachEndpointClient(const ScopedInterfaceEndpointHandle& handle,
                            InterfaceEndpointClient* endpoint_client);
  // Detaches the client attached to the specified endpoint. It should be called
  // on the same thread as the corresponding AttachEndpointClient() call.
  void DetachEndpointClient(const ScopedInterfaceEndpointHandle& handle);

  bool SendMessage(const ScopedInterfaceEndpointHandle& handle,
                   Message* message);

  // Raises an error on the underlying message pipe. It disconnects the pipe
  // and notifies all interfaces running on this pipe.
  void RaiseError();

  scoped_ptr<AssociatedGroup> CreateAssociatedGroup();

  static MultiplexRouter* GetRouter(AssociatedGroup* associated_group);

  // ---------------------------------------------------------------------------
  // The following public methods are called on the creating thread.

  // Please note that this method shouldn't be called unless it results from an
  // explicit request of the user of bindings (e.g., the user sets an
  // InterfacePtr to null or closes a Binding).
  void CloseMessagePipe() {
    DCHECK(thread_checker_.CalledOnValidThread());
    connector_.CloseMessagePipe();
  }

  // Extracts the underlying message pipe.
  ScopedMessagePipeHandle PassMessagePipe() {
    DCHECK(thread_checker_.CalledOnValidThread());
    DCHECK(!HasAssociatedEndpoints());
    return connector_.PassMessagePipe();
  }

  // Blocks the current thread until the first incoming message, or |deadline|.
  bool WaitForIncomingMessage(MojoDeadline deadline) {
    DCHECK(thread_checker_.CalledOnValidThread());
    return connector_.WaitForIncomingMessage(deadline);
  }

  // See Binding for details of pause/resume.
  void PauseIncomingMethodCallProcessing() {
    DCHECK(thread_checker_.CalledOnValidThread());
    connector_.PauseIncomingMethodCallProcessing();
  }
  void ResumeIncomingMethodCallProcessing() {
    DCHECK(thread_checker_.CalledOnValidThread());
    connector_.ResumeIncomingMethodCallProcessing();
  }

  // Whether there are any associated interfaces running currently.
  bool HasAssociatedEndpoints() const;

  // Sets this object to testing mode.
  // In testing mode, the object doesn't disconnect the underlying message pipe
  // when it receives unexpected or invalid messages.
  void EnableTestingMode();

  // Is the router bound to a message pipe handle?
  bool is_valid() const {
    DCHECK(thread_checker_.CalledOnValidThread());
    return connector_.is_valid();
  }

  // TODO(yzshen): consider removing this getter.
  MessagePipeHandle handle() const {
    DCHECK(thread_checker_.CalledOnValidThread());
    return connector_.handle();
  }

 private:
  friend class base::RefCountedDeleteOnMessageLoop<MultiplexRouter>;
  friend class base::DeleteHelper<MultiplexRouter>;

  class InterfaceEndpoint;
  struct Task;

  ~MultiplexRouter() override;

  // MessageReceiver implementation:
  bool Accept(Message* message) override;

  // PipeControlMessageHandlerDelegate implementation:
  bool OnPeerAssociatedEndpointClosed(InterfaceId id) override;
  bool OnAssociatedEndpointClosedBeforeSent(InterfaceId id) override;

  void OnPipeConnectionError();

  // Processes enqueued tasks (incoming messages and error notifications).
  // If |force_async| is true, it guarantees not to call any
  // InterfaceEndpointClient methods directly.
  //
  // Note: Because calling into InterfaceEndpointClient may lead to destruction
  // of this object, if |force_async| is set to false, the caller needs to hold
  // on to a ref outside of |lock_| before calling this method.
  void ProcessTasks(bool force_async);

  // Returns true to indicate that |task| has been processed. Otherwise the task
  // will be added back to the front of the queue.
  bool ProcessNotifyErrorTask(Task* task, bool force_async);
  bool ProcessIncomingMessageTask(Task* task, bool force_async);

  void LockAndCallProcessTasks();

  // Updates the state of |endpoint|. If both the endpoint and its peer have
  // been closed, removes it from |endpoints_|.
  // NOTE: The method may invalidate |endpoint|.
  enum EndpointStateUpdateType { ENDPOINT_CLOSED, PEER_ENDPOINT_CLOSED };
  void UpdateEndpointStateMayRemove(InterfaceEndpoint* endpoint,
                                    EndpointStateUpdateType type);

  void RaiseErrorInNonTestingMode();

  // Whether to set the namespace bit when generating interface IDs. Please see
  // comments of kInterfaceIdNamespaceMask.
  const bool set_interface_id_namespace_bit_;

  MessageHeaderValidator header_validator_;
  Connector connector_;
  bool encountered_error_;

  base::ThreadChecker thread_checker_;

  // Protects the following members.
  mutable base::Lock lock_;
  PipeControlMessageHandler control_message_handler_;
  PipeControlMessageProxy control_message_proxy_;

  std::map<InterfaceId, scoped_refptr<InterfaceEndpoint>> endpoints_;
  uint32_t next_interface_id_value_;

  std::deque<scoped_ptr<Task>> tasks_;

  bool testing_mode_;

  DISALLOW_COPY_AND_ASSIGN(MultiplexRouter);
};

}  // namespace internal
}  // namespace mojo

#endif  // MOJO_PUBLIC_CPP_BINDINGS_LIB_MULTIPLEX_ROUTER_H_
