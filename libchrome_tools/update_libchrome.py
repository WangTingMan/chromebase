#!/usr/bin/python3

# Copyright (C) 2018 The Android Open Source Project
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

"""Updates libchrome.

This script uprevs the libchrome library with newer Chromium code.
How to use:

Prepare your local Chromium repository with the target revision.
$ cd external/libchrome
$ python3 libchrome_tools/update_libchrome.py \
      --chromium_root=${PATH_TO_YOUR_LOCAL_CHROMIUM_REPO}

This script does following things;
- Clean existing libchrome code, except some manually created files and tools.
- Copy necessary files from original Chromium repository.
- Apply patches to the copied files, if necessary.
"""


import argparse
import fnmatch
import glob
import os
import re
import shutil
import subprocess


_TOOLS_DIR = os.path.dirname(os.path.realpath(__file__))
_LIBCHROME_ROOT = os.path.dirname(_TOOLS_DIR)


# Files in this list or in the directory listed here will be just copied.
# Paths ends with '/' is interpreted as directory.
_IMPORT_LIST = [
    'mojo/',
    'third_party/ply/',
    'third_party/markupsafe/',
    'third_party/jinja2/',
]

# Files which are in the repository, but should not be imported from Chrome
# repository.
_IMPORT_BLACKLIST = [
    # Libchrome specific files.
    '.gitignore',
    'Android.bp',
    'MODULE_LICENSE_BSD',
    'NOTICE',
    'OWNERS',
    'SConstruct',
    'libmojo.pc.in',
    'testrunner.cc',
    '*/DEPS',

    # No Chromium OWNERS should be imported.
    '*/OWNERS',

    # libchrome_tools and soong are out of the update target.
    'libchrome_tools/*',
    'soong/*',

     # No internal directories.
    'mojo/internal/*',

    # Those files should be generated. Please see also buildflag_header.patch.
    'base/allocator/buildflags.h',
    'base/android/java/src/org/chromium/base/BuildConfig.java',
    'base/cfi_buildflags.h',
    'base/debug/debugging_buildflags.h',
    'base/memory/protected_memory_buildflags.h',
    'base/synchronization/synchronization_buildflags.h',
    'gen/*',
    'ipc/ipc_buildflags.h',

    # Blacklist several third party libraries; system libraries should be used.
    'base/third_party/libevent/*',
    'base/third_party/symbolize/*',

    'testing/gmock/*',
    'testing/gtest/*',
    'third_party/ashmem/*',
    'third_party/modp_b64/*',
    'third_party/protobuf/*',
]

def _find_target_files(chromium_root):
  """Returns target files to be upreved."""
  # Files in the repository should be updated.
  output = subprocess.check_output(
      ['git', 'ls-tree', '-r', '--name-only', '--full-name', 'HEAD'],
      cwd=_LIBCHROME_ROOT).decode('utf-8')

  # Files in _IMPORT_LIST are copied in the following section, so
  # exclude them from candidates, here, so that files deleted in chromium
  # repository will be deleted on update.
  candidates = [
      path for path in output.splitlines()
      if not any(path.startswith(import_path) for import_path in _IMPORT_LIST)]

  # All files listed in _IMPORT_LIST should be imported, too.
  for import_path in _IMPORT_LIST:
    import_root = os.path.join(chromium_root, import_path)

    # If it is a file, just add to the candidates.
    if os.path.isfile(import_root):
      candidates.append(import_path)
      continue

    # If it is a directory, traverse all files in the directory recursively
    # and add all of them to candidates.
    for dirpath, dirnames, filenames in os.walk(import_root):
      for filename in filenames:
        filepath = os.path.join(dirpath, filename)
        candidates.append(os.path.relpath(filepath, chromium_root))

  # Apply blacklist.
  exclude_pattern = re.compile('|'.join(
      '(?:%s)' % fnmatch.translate(pattern) for pattern in _IMPORT_BLACKLIST))
  return [filepath for filepath in candidates
          if not exclude_pattern.match(filepath)]


def _clean_existing_dir(output_root):
  """Removes existing libchrome files.

  Args:
    output_root: Path to the output directory.
  """
  os.makedirs(output_root, mode=0o755, exist_ok=True)
  for path in os.listdir(output_root):
    target_path = os.path.join(output_root, path)
    if (not os.path.isdir(target_path) or path in ('.git', 'libchrome_tools', 'soong')):
      continue
    shutil.rmtree(target_path)


def _import_files(chromium_root, output_root):
  """Copies files from Chromium repository into libchrome.

  Args:
    chromium_root: Path to the Chromium's repository.
    output_root: Path to the output directory.
  """
  for filepath in _find_target_files(chromium_root):
    source_path = os.path.join(chromium_root, filepath)
    target_path = os.path.join(output_root, filepath)
    os.makedirs(os.path.dirname(target_path), mode=0o755, exist_ok=True)
    shutil.copy2(source_path, target_path)


def _apply_patch_files(patch_root, output_root):
  """Applies patches.

  libchrome needs some modification from Chromium repository, e.g. supporting
  toolchain which is not used by Chrome, or using system library rather than
  the library checked in the Chromium repository.
  See each *.patch file in libchrome_tools/patch/ directory for details.

  Args:
    patch_root: Path to the directory containing patch files.
    output_root: Path to the output directory.
  """
  for patch_file in glob.iglob(os.path.join(patch_root, '*.patch')):
    with open(patch_file, 'r') as f:
      subprocess.check_call(['patch', '-p1'], stdin=f, cwd=output_root)


def _parse_args():
  """Parses commandline arguments."""
  parser = argparse.ArgumentParser()

  # TODO(hidehiko): Support to specify the Chromium's revision number.
  parser.add_argument(
      '--chromium_root',
      help='Root directory to the local chromium repository.')
  parser.add_argument(
      '--output_root',
      default=_LIBCHROME_ROOT,
      help='Output directory, which is libchrome root directory.')
  parser.add_argument(
      '--patch_dir',
      default=os.path.join(_TOOLS_DIR, 'patch'),
      help='Directory containing patch files to be applied.')

  return parser.parse_args()


def main():
  args = _parse_args()
  _clean_existing_dir(args.output_root)
  _import_files(args.chromium_root, args.output_root)
  _apply_patch_files(args.patch_dir, args.output_root)
  # TODO(hidehiko): Create a git commit with filling templated message.


if __name__ == '__main__':
  main()
