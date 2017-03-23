// Copyright 2016 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "base/compiler_specific.h"
#include "base/trace_event/trace_event_filter.h"

namespace base {
namespace trace_event {

TraceEventFilter::TraceEventFilter() {}
TraceEventFilter::~TraceEventFilter() {}

void TraceEventFilter::EndEvent(const char* category_name,
                                const char* event_name) const {
  ALLOW_UNUSED_PARAM(category_name);
  ALLOW_UNUSED_PARAM(event_name);
}

}  // namespace trace_event
}  // namespace base
