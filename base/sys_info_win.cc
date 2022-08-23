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
#include "base/strings/stringprintf.h"
#include "base/win/windows_version.h"

#include <windows.h>

namespace {

int64_t AmountOfMemory( DWORDLONG MEMORYSTATUSEX::* memory_field )
{
    MEMORYSTATUSEX memory_info;
    memory_info.dwLength = sizeof( memory_info );
    if( !GlobalMemoryStatusEx( &memory_info ) )
    {
        NOTREACHED();
        return 0;
    }

    int64_t rv = static_cast< int64_t >( memory_info.*memory_field );
    if( rv < 0 )
        rv = std::numeric_limits<int64_t>::max();
    return rv;
}

base::LazyInstance<
    base::internal::LazySysInfoValue<int64_t, base::SysInfo::AmountOfPhysicalMemory>>::Leaky
    g_lazy_physical_memory = LAZY_INSTANCE_INITIALIZER;

}  // namespace

namespace base {

int64_t SysInfo::AmountOfPhysicalMemory()
{
    return AmountOfMemory( &MEMORYSTATUSEX::ullTotalPhys );
}

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
    return win::OSInfo::GetInstance()->processor_model_name();
}

int64_t SysInfo::AmountOfFreeDiskSpace( const FilePath& path )
{
    base::ThreadRestrictions::AssertIOAllowed();

    ULARGE_INTEGER available, total, free;
    if( !GetDiskFreeSpaceExW( path.value().c_str(), &available, &total, &free ) )
    {
        return -1;
    }
    int64_t rv = static_cast< int64_t >( available.QuadPart );
    if( rv < 0 )
        rv = std::numeric_limits<int64_t>::max();
    return rv;
}

// static
std::string SysInfo::OperatingSystemName()
{
    return "Windows NT";
}

int SysInfo::NumberOfProcessors()
{
    return win::OSInfo::GetInstance()->processors();
}

int64_t SysInfo::AmountOfVirtualMemory()
{
    return 1;
}

size_t SysInfo::VMAllocationGranularity()
{
    return win::OSInfo::GetInstance()->allocation_granularity();
}

std::string SysInfo::OperatingSystemVersion()
{
    win::OSInfo* os_info = win::OSInfo::GetInstance();
    win::OSInfo::VersionNumber version_number = os_info->version_number();
    std::string version( StringPrintf( "%d.%d", version_number.major,
        version_number.minor ) );
    win::OSInfo::ServicePack service_pack = os_info->service_pack();
    if( service_pack.major != 0 )
    {
        version += StringPrintf( " SP%d", service_pack.major );
        if( service_pack.minor != 0 )
            version += StringPrintf( ".%d", service_pack.minor );
    }
    return version;
}

// static
void SysInfo::OperatingSystemVersionNumbers( int32_t* major_version,
    int32_t* minor_version,
    int32_t* bugfix_version )
{
    win::OSInfo* os_info = win::OSInfo::GetInstance();
    *major_version = os_info->version_number().major;
    *minor_version = os_info->version_number().minor;
    *bugfix_version = 0;
}

// static
std::string SysInfo::OperatingSystemArchitecture()
{
    win::OSInfo::WindowsArchitecture arch =
        win::OSInfo::GetInstance()->GetArchitecture();
    switch( arch )
    {
    case win::OSInfo::X86_ARCHITECTURE:
        return "x86";
    case win::OSInfo::X64_ARCHITECTURE:
        return "x86_64";
    case win::OSInfo::IA64_ARCHITECTURE:
        return "ia64";
    default:
        return "";
    }
}

}  // namespace base
