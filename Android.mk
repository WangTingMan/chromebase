# Copyright (C) 2015 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Default values for the USE flags. Override these USE flags from your product
# by setting BRILLO_USE_* values. Note that we define local variables like
# local_use_* to prevent leaking our default setting for other packages.
local_use_dbus := $(if $(BRILLO_USE_DBUS),$(BRILLO_USE_DBUS),0)

LOCAL_PATH := $(call my-dir)

# Common variables
# ========================================================

# Set libchromeUseClang to "true" to force clang or "false" to force gcc.
libchromeUseClang :=
libchromeCommonCppExtension := .cc
libchromeTestCFlags := -Wno-unused-parameter -Wno-unused-function \
	-Wno-missing-field-initializers
libchromeCommonCFlags := -Wall -Werror
libchromeCommonCIncludes := \
	external/valgrind/include \
	external/valgrind \

libchromeExportedCIncludes := $(LOCAL_PATH)

ifeq ($(local_use_dbus),1)

# libchrome-dbus shared library for target
# ========================================================
include $(CLEAR_VARS)
LOCAL_MODULE := libchrome-dbus
LOCAL_SRC_FILES := \
	dbus/bus.cc \
	dbus/dbus_statistics.cc \
	dbus/exported_object.cc \
	dbus/file_descriptor.cc \
	dbus/message.cc \
	dbus/object_manager.cc \
	dbus/object_path.cc \
	dbus/object_proxy.cc \
	dbus/property.cc \
	dbus/scoped_dbus_error.cc \
	dbus/string_util.cc \
	dbus/util.cc \
	dbus/values_util.cc \

LOCAL_CPP_EXTENSION := $(libchromeCommonCppExtension)
LOCAL_CFLAGS := $(libchromeCommonCFlags)
LOCAL_CLANG := $(libchromeUseClang)
LOCAL_C_INCLUDES := $(libchromeCommonCIncludes)
LOCAL_SHARED_LIBRARIES := \
	libchrome \
	libdbus \
	libprotobuf-cpp-lite \

LOCAL_STATIC_LIBRARIES := libgtest_prod
LOCAL_EXPORT_C_INCLUDE_DIRS := $(libchromeExportedCIncludes)
LOCAL_EXPORT_STATIC_LIBRARY_HEADERS := libgtest_prod
LOCAL_EXPORT_SHARED_LIBRARY_HEADERS := libchrome
include $(BUILD_SHARED_LIBRARY)

endif  # local_use_dbus == 1

ifeq ($(local_use_dbus),1)

# Helpers needed for D-Bus unit tests.
# ========================================================
include $(CLEAR_VARS)
LOCAL_MODULE := libchrome_dbus_test_helpers
LOCAL_SHARED_LIBRARIES := libdbus libchrome-dbus
LOCAL_STATIC_LIBRARIES := libgmock
LOCAL_CPP_EXTENSION := $(libchromeCommonCppExtension)
LOCAL_CFLAGS := $(libchromeCommonCFlags) $(libchromeTestCFlags)
LOCAL_CLANG := $(libchromeUseClang)
LOCAL_C_INCLUDES := $(libchromeCommonCIncludes)
LOCAL_SRC_FILES := \
	dbus/mock_bus.cc \
	dbus/mock_exported_object.cc \
	dbus/mock_object_manager.cc \
	dbus/mock_object_proxy.cc \

include $(BUILD_STATIC_LIBRARY)

endif  # local_use_dbus == 1
