// Copyright (C) 2018 The Android Open Source Project
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// third_party/ashmem is Android shared memory. Instead of clone it here,
// use cutils/ashmem.h directly.
#include <cutils/ashmem.h>

#ifdef __cplusplus
extern "C" {
#endif

inline int ashmem_get_prot_region(int fd) {
  int ret = ashmem_valid(fd);
  if (ret < 0)
    return ret;
  return TEMP_FAILURE_RETRY(ioctl(fd, ASHMEM_GET_PROT_MASK));
}

#ifdef __cplusplus
}
#endif
