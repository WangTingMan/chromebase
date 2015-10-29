// Copyright (c) 2011 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "base/build_time.h"

// Imports the generated build date, i.e. BUILD_DATE.
#include "base/generated_build_date.h"

#include "base/logging.h"
#include "base/time/time.h"

#if defined(OS_ANDROID)
#include <cutils/properties.h>
#endif

namespace base {

Time GetBuildTime() {
  Time integral_build_time;
#if defined(OS_ANDROID)
  char kDateTime[PROPERTY_VALUE_MAX];
  property_get("ro.build.date", kDateTime, "Sep 02 2008 08:00:00 PST");
#elif defined(DONT_EMBED_BUILD_METADATA) && !defined(OFFICIAL_BUILD)
  DCHECK(result);
  return integral_build_time;
}

}  // namespace base
