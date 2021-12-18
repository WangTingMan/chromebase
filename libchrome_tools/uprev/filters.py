# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Provide filters for libchrome tools."""

import re

# Libchrome wants WANT but not WANT_EXCLUDE
# aka files matching WANT will be copied from upstream_files
WANT = [
    re.compile(rb'base/((?!(allocator|third_party)/).*$)'),
    re.compile(
        rb'base/allocator/(allocator_shim.cc|allocator_shim_override_linker_wrapped_symbols.h|allocator_shim_override_cpp_symbols.h|allocator_shim_override_libc_symbols.h|allocator_shim_default_dispatch_to_glibc.cc|allocator_shim.h|allocator_shim_default_dispatch_to_linker_wrapped_symbols.cc|allocator_extension.cc|allocator_extension.h|allocator_shim_internals.h)$'
    ),
    re.compile(rb'base/third_party/(dynamic_annotation|icu|nspr|valgrind)'),
    re.compile(rb'build/(android/(gyp/util|pylib/([^/]*$|constants))|[^/]*\.(h|py)$)'),
    re.compile(rb'mojo/'),
    re.compile(rb'dbus/'),
    re.compile(rb'ipc/.*(\.cc|\.h|\.mojom)$'),
    re.compile(rb'ui/gfx/(gfx_export.h|geometry|range)'),
    re.compile(rb'testing/[^/]*\.(cc|h)$'),
    re.compile(rb'third_party/(jinja2|markupsafe|ply)'),
    re.compile(
        rb'components/(json_schema|policy/core/common/[^/]*$|policy/policy_export.h|timers)'
    ),
    re.compile(
        rb'device/bluetooth/bluetooth_(common|advertisement|uuid|export)\.*(h|cc)'
    ),
    re.compile(
        rb'device/bluetooth/bluez/bluetooth_service_attribute_value_bluez.(h|cc)'
    ),
]

# WANT_EXCLUDE will be excluded from WANT
WANT_EXCLUDE = [
    re.compile(rb'(.*/)?BUILD.gn$'),
    re.compile(rb'(.*/)?PRESUBMIT.py$'),
    re.compile(rb'(.*/)?OWNERS$'),
    re.compile(rb'(.*/)?SECURITY_OWNERS$'),
    re.compile(rb'(.*/)?DEPS$'),
    re.compile(rb'base/(.*/)?(ios|win|fuchsia|mac|openbsd|freebsd|nacl)/.*'),
    re.compile(rb'.*_(ios|win|mac|fuchsia|openbsd|freebsd|nacl)[_./]'),
    re.compile(rb'.*/(ios|win|mac|fuchsia|openbsd|freebsd|nacl)_'),
    re.compile(rb'dbus/(test_serv(er|ice)\.cc|test_service\.h)$')
]

# Files matching KEEP should not be touched.
# aka files matching KEEP will keep its our_files version,
# and it will be kept even it doesn't exist in upstream.
# KEEP-KEEP_EXCLUDE must NOT intersect with WANT-WANT_EXCLUDE
KEEP = [
    re.compile(
        b'(Android.bp|BUILD.gn|crypto|libchrome_tools|MODULE_LICENSE_BSD|NOTICE|OWNERS|PRESUBMIT.cfg|soong|testrunner.cc|third_party)(/.*)?$'
    ),
    re.compile(rb'[^/]*$'),
    re.compile(rb'.*buildflags.h'),
    re.compile(rb'base/android/java/src/org/chromium/base/BuildConfig.java'),
    re.compile(rb'testing/(gmock|gtest)/'),
    re.compile(rb'base/third_party/(libevent|symbolize)'),
]

# KEEP_EXCLUDE wil be excluded from KEEP.
KEEP_EXCLUDE = [
    re.compile(rb'third_party/(jinja2|markupsafe|ply)'),
]


def _want_file(path):
    """Returns whether the path wants to be a new file."""
    wanted = False
    for want_file_regex in WANT:
        if want_file_regex.match(path):
            wanted = True
            break
    for exclude_file_regex in WANT_EXCLUDE:
        if exclude_file_regex.match(path):
            wanted = False
            break
    return wanted


def _keep_file(path):
    """Returns whether the path wants to be kept untouched in local files."""
    keep = False
    for keep_file_regex in KEEP:
        if keep_file_regex.match(path):
            keep = True
            break
    for exclude_file_regex in KEEP_EXCLUDE:
        if exclude_file_regex.match(path):
            keep = False
            break
    return keep


def filter_file(our_files, upstream_files):
    """Generates a list of files we want based on hard-coded rules.

    File list must be a list of GitFile.

    Args:
        our_files: files in Chromium OS libchrome repository.
        upstream_files: files in Chromium browser repository.
    """

    files = []
    for upstream_file in upstream_files:
      if _want_file(upstream_file.path):
            files.append(upstream_file)
    for our_file in our_files:
      if _keep_file(our_file.path):
            files.append(our_file)
    return files


def filter_diff(diff):
    """Returns a subset of diff, after running filters.

    Args:
        diff: diff to filter. diff contains list of utils.GitDiffTree
    """
    filtered = []
    for change in diff:
        path = change.file.path
        if _want_file(path):
            assert not _keep_file(path)
            filtered.append(change)
    return filtered
