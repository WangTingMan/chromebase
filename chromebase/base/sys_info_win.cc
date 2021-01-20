// Copyright (c) 2011 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "base/sys_info.h"

#include <stddef.h>
#include <stdint.h>

#include <limits>

#include "base/files/file_util.h"
#include "base/lazy_instance.h"
#include "base/logging.h"
#include "base/numerics/safe_conversions.h"
#include "base/process/process_metrics.h"
#include "base/strings/string_number_conversions.h"
#include "base/sys_info_internal.h"
#include "build/build_config.h"

namespace {

int64_t AmountOfMemory(int pages_name) {
    return 0;
}

int64_t AmountOfPhysicalMemory() {
  return 0;
}

base::LazyInstance<
    base::internal::LazySysInfoValue<int64_t, AmountOfPhysicalMemory>>::Leaky
    g_lazy_physical_memory = LAZY_INSTANCE_INITIALIZER;

}  // namespace

namespace base {

// static
int64_t SysInfo::AmountOfPhysicalMemoryImpl() {
  return g_lazy_physical_memory.Get().value();
}

// static
int64_t SysInfo::AmountOfAvailablePhysicalMemoryImpl() {
  SystemMemoryInfoKB info;
  if (!GetSystemMemoryInfo(&info))
    return 0;
  return AmountOfAvailablePhysicalMemory();
}

// static
std::string SysInfo::CPUModelName() {
  return std::string();
}

int SysInfo::NumberOfProcessors()
{
    return 1;
}

int64_t SysInfo::AmountOfVirtualMemory()
{
    return 1;
}

size_t SysInfo::VMAllocationGranularity()
{
    return 1;
}


}  // namespace base
