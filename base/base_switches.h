// Copyright (c) 2012 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// Defines all the "base" command-line switches.

#ifndef BASE_BASE_SWITCHES_H_
#define BASE_BASE_SWITCHES_H_

#include "build/build_config.h"

namespace switches {

#if defined(OS_WIN)
// Delays execution of base::TaskPriority::BACKGROUND tasks until shutdown.
inline constexpr char const* kDisableBackgroundTasks = "disable-background-tasks";

// Disables the crash reporting.
inline constexpr char const* kDisableBreakpad = "disable-breakpad";

// Comma-separated list of feature names to disable. See also kEnableFeatures.
inline constexpr char const* kDisableFeatures = "disable-features";

// Indicates that crash reporting should be enabled. On platforms where helper
// processes cannot access to files needed to make this decision, this flag is
// generated internally.
inline constexpr char const* kEnableCrashReporter = "enable-crash-reporter";

// Comma-separated list of feature names to enable. See also kDisableFeatures.
inline constexpr char const* kEnableFeatures = "enable-features";

// Generates full memory crash dump.
inline constexpr char const* kFullMemoryCrashReport = "full-memory-crash-report";

// Force low-end device mode when set.
inline constexpr char const* kEnableLowEndDeviceMode = "enable-low-end-device-mode";

// Force disabling of low-end device mode when set.
inline constexpr char const* kDisableLowEndDeviceMode = "disable-low-end-device-mode";

// This option can be used to force field trials when testing changes locally.
// The argument is a list of name and value pairs, separated by slashes. If a
// trial name is prefixed with an asterisk, that trial will start activated.
// For example, the following argument defines two trials, with the second one
// activated: "GoogleNow/Enable/*MaterialDesignNTP/Default/" This option can
// also be used by the browser process to send the list of trials to a
// non-browser process, using the same format. See
// FieldTrialList::CreateTrialsFromString() in field_trial.h for details.
inline constexpr char const* kForceFieldTrials = "force-fieldtrials";

// Suppresses all error dialogs when present.
inline constexpr char const* kNoErrorDialogs = "noerrdialogs";

// When running certain tests that spawn child processes, this switch indicates
// to the test framework that the current process is a child process.
inline constexpr char const* kTestChildProcess = "test-child-process";

// When running certain tests that spawn child processes, this switch indicates
// to the test framework that the current process should not initialize ICU to
// avoid creating any scoped handles too early in startup.
inline constexpr char const* kTestDoNotInitializeIcu = "test-do-not-initialize-icu";

// Gives the default maximal active V-logging level; 0 is the default.
// Normally positive values are used for V-logging levels.
inline constexpr char const* kV = "v";

// Gives the per-module maximal V-logging levels to override the value
// given by --v.  E.g. "my_module=2,foo*=3" would change the logging
// level for all code in source files "my_module.*" and "foo*.*"
// ("-inl" suffixes are also disregarded for this matching).
//
// Any pattern containing a forward or backward slash will be tested
// against the whole pathname and not just the module.  E.g.,
// "*/foo/bar/*=2" would change the logging level for all code in
// source files under a "foo/bar" directory.
inline constexpr char const* kVModule = "vmodule";

// Will wait for 60 seconds for a debugger to come to attach to the process.
inline constexpr char const* kWaitForDebugger = "wait-for-debugger";

// Sends trace events from these categories to a file.
// --trace-to-file on its own sends to default categories.
inline constexpr char const* kTraceToFile = "trace-to-file";

// Specifies the file name for --trace-to-file. If unspecified, it will
// go to a default file name.
inline constexpr char const* kTraceToFileName = "trace-to-file-name";

// Specifies a location for profiling output. This will only work if chrome has
// been built with the gyp variable profiling=1 or gn arg enable_profiling=true.
//
//   {pid} if present will be replaced by the pid of the process.
//   {count} if present will be incremented each time a profile is generated
//           for this process.
// The default is chrome-profile-{pid} for the browser and test-profile-{pid}
// for tests.
inline constexpr char const* kProfilingFile = "profiling-file";

#else

extern const char kDisableBackgroundTasks[];
extern const char kDisableBreakpad[];
extern const char kDisableFeatures[];
extern const char kDisableLowEndDeviceMode[];
extern const char kEnableCrashReporter[];
extern const char kEnableFeatures[];
extern const char kEnableLowEndDeviceMode[];
extern const char kForceFieldTrials[];
extern const char kFullMemoryCrashReport[];
extern const char kNoErrorDialogs[];
extern const char kProfilingFile[];
extern const char kTestChildProcess[];
extern const char kTestDoNotInitializeIcu[];
extern const char kTraceToFile[];
extern const char kTraceToFileName[];
extern const char kV[];
extern const char kVModule[];
extern const char kWaitForDebugger[];
#endif

#if defined(OS_WIN)
inline constexpr char const* kDisableUsbKeyboardDetect = "disable-usb-keyboard-detect";
#endif

#if defined(OS_LINUX) && !defined(OS_CHROMEOS)
extern const char kDisableDevShmUsage[];
#endif

#if defined(OS_POSIX)
extern const char kEnableCrashReporterForTesting[];
#endif

#if defined(OS_ANDROID)
extern const char kOrderfileMemoryOptimization[];
#endif

}  // namespace switches

#endif  // BASE_BASE_SWITCHES_H_
