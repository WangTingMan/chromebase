// Copyright 2015 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef MOJO_SHELL_APPLICATION_INSTANCE_H_
#define MOJO_SHELL_APPLICATION_INSTANCE_H_

#include <stdint.h>

#include <set>

#include "base/callback.h"
#include "base/macros.h"
#include "base/memory/scoped_ptr.h"
#include "base/process/process_handle.h"
#include "mojo/public/cpp/bindings/binding.h"
#include "mojo/shell/capability_filter.h"
#include "mojo/shell/connect_to_application_params.h"
#include "mojo/shell/identity.h"
#include "mojo/shell/public/interfaces/application_manager.mojom.h"
#include "mojo/shell/public/interfaces/shell.mojom.h"
#include "mojo/shell/public/interfaces/shell_client.mojom.h"
#include "url/gurl.h"

namespace mojo {
namespace shell {

class ApplicationManager;
class NativeRunner;

// Encapsulates a connection to an instance of an application, tracked by the
// shell's ApplicationManager.
class ApplicationInstance : public mojom::Shell,
                            public mojom::PIDReceiver {
 public:
  // |requesting_shell_client_factory_id| is the id of the factory that
  // loaded this app. If the app was not loaded by a factory the id
  // is kInvalidApplicationID.
  ApplicationInstance(
      mojom::ShellClientPtr shell_client,
      ApplicationManager* manager,
      const Identity& identity,
      uint32_t requesting_shell_client_factory_id,
      const mojom::Shell::ConnectToApplicationCallback& connect_callback,
      const base::Closure& on_application_end,
      const String& application_name);

  ~ApplicationInstance() override;

  void InitializeApplication();

  void ConnectToClient(scoped_ptr<ConnectToApplicationParams> params);

  // Required before GetProcessId can be called.
  void SetNativeRunner(NativeRunner* native_runner);

  void BindPIDReceiver(InterfaceRequest<mojom::PIDReceiver> pid_receiver);

  void RunConnectCallback();

  mojom::ShellClient* shell_client() { return shell_client_.get(); }
  const Identity& identity() const { return identity_; }
  uint32_t id() const { return id_; }
  base::ProcessId pid() const { return pid_; }
  void set_pid(base::ProcessId pid) { pid_ = pid; }
  base::Closure on_application_end() const { return on_application_end_; }
  void set_requesting_shell_client_factory_id(uint32_t id) {
    requesting_shell_client_factory_id_ = id;
  }
  uint32_t requesting_shell_client_factory_id() const {
    return requesting_shell_client_factory_id_;
  }
  const String& application_name() const { return application_name_; }

 private:
  // Shell implementation:
  void ConnectToApplication(
      URLRequestPtr app_request,
      shell::mojom::InterfaceProviderRequest remote_interfaces,
      shell::mojom::InterfaceProviderPtr local_interfaces,
      mojom::CapabilityFilterPtr filter,
      const ConnectToApplicationCallback& callback) override;
  void QuitApplication() override;

  // PIDReceiver implementation:
  void SetPID(uint32_t pid) override;

  uint32_t GenerateUniqueID() const;

  void CallAcceptConnection(scoped_ptr<ConnectToApplicationParams> params);

  void OnConnectionError();

  void OnQuitRequestedResult(bool can_quit);

  void DestroyRunner();

  ApplicationManager* const manager_;
  // An id that identifies this instance. Distinct from pid, as a single process
  // may vend multiple application instances, and this object may exist before a
  // process is launched.
  const uint32_t id_;
  const Identity identity_;
  const bool allow_any_application_;
  uint32_t requesting_shell_client_factory_id_;
  mojom::Shell::ConnectToApplicationCallback connect_callback_;
  base::Closure on_application_end_;
  mojom::ShellClientPtr shell_client_;
  Binding<mojom::Shell> binding_;
  Binding<mojom::PIDReceiver> pid_receiver_binding_;
  bool queue_requests_;
  std::vector<ConnectToApplicationParams*> queued_client_requests_;
  NativeRunner* native_runner_;
  const String application_name_;
  base::ProcessId pid_;

  DISALLOW_COPY_AND_ASSIGN(ApplicationInstance);
};

}  // namespace shell
}  // namespace mojo

#endif  // MOJO_SHELL_APPLICATION_INSTANCE_H_
