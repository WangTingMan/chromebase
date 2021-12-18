// Copyright 2015 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "base/bind.h"
#include "build/build_config.h"
#include "base/profiler/native_stack_sampler.h"

namespace base {

// static
std::unique_ptr<NativeStackSampler> NativeStackSampler::Create(
    PlatformThreadId thread_id,
    NativeStackSamplerTestDelegate* test_delegate )
{
#if defined(ARCH_CPU_X86_64) || defined(ARCH_CPU_ARM64)
    return std::unique_ptr<NativeStackSampler>();
#else
    return nullptr;
#endif
}

// static
size_t NativeStackSampler::GetStackBufferSize() {
  // The default Win32 reserved stack size is 1 MB and Chrome Windows threads
  // currently always use the default, but this allows for expansion if it
  // occurs. The size beyond the actual stack size consists of unallocated
  // virtual memory pages so carries little cost (just a bit of wasted address
  // space).
  return 2 << 20;  // 2 MiB
}

}  // namespace base
