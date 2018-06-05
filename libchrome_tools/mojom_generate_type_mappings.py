#!/usr/bin/python

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

"""Drives mojom typemapping generator.

Usage:

% python libchrome_tools/mojom_generate_type_mappings.py \
      --output ${output_type_mapping_file_path} \
      ${list of .typemap files}
"""

import argparse
import os
import subprocess
import sys

from build import gn_helpers

_GENERATE_TYPE_MAPPINGS_PATH = os.path.join(
    os.path.dirname(__file__),
    '../mojo/public/tools/bindings/generate_type_mappings.py')

def _read_typemap_config(path):
  """Reads .typemap file.

  Args:
    path: File path to the .typemap location.

  Returns:
    A dictionary holding values in .typemap file.
  """

  with open(path) as f:
    # gn_helpers does not handle comment lines.
    content = [line for line in f if not line.strip().startswith('#')]
  return gn_helpers.FromGNArgs(''.join(content))


def _generate_type_mappings(input_paths, output):
  """Generates __type_mappings file from given .typemap files.

  Builds a command line to run generate_type_mappings.py, and executes it.

  Args:
    input_paths: a list of file paths for .typemap files.
    output: a path to output __type_mappings file.
  """
  command = [sys.executable, _GENERATE_TYPE_MAPPINGS_PATH, '--output', output]

  # TODO(hidehiko): Add dependency handling.

  for path in input_paths:
    typemap_config = _read_typemap_config(path)
    command.append('--start-typemap')
    for public_header in typemap_config.get('public_headers', []):
      command.append('public_headers=' + public_header)
    for traits_header in typemap_config.get('traits_headers', []):
      command.append('traits_headers=' + traits_header)
    for type_mapping in typemap_config.get('type_mappings', []):
      command.append('type_mappings=' + type_mapping)

  subprocess.check_call(command)


def _parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('--output', help='Output file path')
  parser.add_argument('input_paths', metavar="INPUT-PATH", nargs='+',
                      help='Input typemap files.')
  return parser.parse_args()


def main():
  args = _parse_args()
  _generate_type_mappings(args.input_paths, args.output)


if __name__ == '__main__':
  main()
