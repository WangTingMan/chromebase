// Copyright 2014 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef MOJO_SHELL_STANDALONE_ANDROID_ANDROID_HANDLER_H_
#define MOJO_SHELL_STANDALONE_ANDROID_ANDROID_HANDLER_H_

#include <jni.h>

#include "mojo/shell/public/cpp/interface_factory_impl.h"
#include "mojo/shell/public/cpp/shell_client.h"
#include "mojo/shell/public/cpp/shell_client_factory.h"
#include "mojo/shell/public/interfaces/shell_client_factory.mojom.h"

namespace base {
class FilePath;
}

namespace mojo {
namespace shell {

class AndroidHandler : public ShellClient,
                       public ShellClientFactory::Delegate {
 public:
  AndroidHandler();
  ~AndroidHandler();

 private:
  // mojo::ShellClient:
  void Initialize(Shell* shell, const std::string& url, uint32_t id) override;
  bool AcceptConnection(Connection* connection) override;

  // ShellClientFactory::Delegate:
  void CreateShellClient(mojom::ShellClientRequest request,
                         const GURL& url) override;

  ShellClientFactory shell_client_factory_;
  MOJO_DISALLOW_COPY_AND_ASSIGN(AndroidHandler);
};

bool RegisterAndroidHandlerJni(JNIEnv* env);

}  // namespace shell
}  // namespace mojo

#endif  // MOJO_SHELL_STANDALONE_ANDROID_ANDROID_HANDLER_H_
