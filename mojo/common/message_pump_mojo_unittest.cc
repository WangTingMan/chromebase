// Copyright 2013 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "mojo/common/message_pump_mojo.h"

#include "base/message_loop/message_loop_test.h"
#include "base/run_loop.h"
#include "mojo/common/message_pump_mojo_handler.h"
#include "mojo/public/cpp/system/core.h"
#include "testing/gtest/include/gtest/gtest.h"

namespace mojo {
namespace common {
namespace test {

scoped_ptr<base::MessagePump> CreateMojoMessagePump() {
  return scoped_ptr<base::MessagePump>(new MessagePumpMojo());
}

RUN_MESSAGE_LOOP_TESTS(Mojo, &CreateMojoMessagePump);

class CountingMojoHandler : public MessagePumpMojoHandler {
 public:
  CountingMojoHandler() : success_count_(0), error_count_(0) {}

  virtual void OnHandleReady(const Handle& handle) override {
    ReadMessageRaw(static_cast<const MessagePipeHandle&>(handle),
                   NULL,
                   NULL,
                   NULL,
                   NULL,
                   MOJO_READ_MESSAGE_FLAG_NONE);
    ++success_count_;
  }
  virtual void OnHandleError(const Handle& handle, MojoResult result) override {
    ++error_count_;
  }

  int success_count() { return success_count_; }
  int error_count() { return error_count_; }

 private:
  int success_count_;
  int error_count_;

  DISALLOW_COPY_AND_ASSIGN(CountingMojoHandler);
};

TEST(MessagePumpMojo, RunUntilIdle) {
  base::MessageLoop message_loop(MessagePumpMojo::Create());
  CountingMojoHandler handler;
  MessagePipe handles;
  MessagePumpMojo::current()->AddHandler(&handler,
                                         handles.handle0.get(),
                                         MOJO_HANDLE_SIGNAL_READABLE,
                                         base::TimeTicks());
  WriteMessageRaw(
      handles.handle1.get(), NULL, 0, NULL, 0, MOJO_WRITE_MESSAGE_FLAG_NONE);
  WriteMessageRaw(
      handles.handle1.get(), NULL, 0, NULL, 0, MOJO_WRITE_MESSAGE_FLAG_NONE);
  base::RunLoop run_loop;
  run_loop.RunUntilIdle();
  EXPECT_EQ(2, handler.success_count());
}

TEST(MessagePumpMojo, UnregisterAfterDeadline) {
  base::MessageLoop message_loop(MessagePumpMojo::Create());
  CountingMojoHandler handler;
  MessagePipe handles;
  MessagePumpMojo::current()->AddHandler(
      &handler,
      handles.handle0.get(),
      MOJO_HANDLE_SIGNAL_READABLE,
      base::TimeTicks::Now() - base::TimeDelta::FromSeconds(1));
  for (int i = 0; i < 2; ++i) {
    base::RunLoop run_loop;
    run_loop.RunUntilIdle();
  }
  EXPECT_EQ(1, handler.error_count());
}

}  // namespace test
}  // namespace common
}  // namespace mojo
