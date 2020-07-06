#!/usr/bin/env python3
# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Utility to copy missing files from Chromium tree to Chromium OS libchrome tree
based on hard coded rules.

This utility is used to diff current HEAD against given commit in Chromium
browser master branch, copy missing files after hard-coded filter rules and
remove unnecessary files. libchrome original files in hard-coded filter rules
will be untounched.
"""

import argparse
import os
import os.path
import subprocess
import sys

import filters
import utils

def main():
    # Init args
    parser = argparse.ArgumentParser(
        description='Copy file from given commits')
    parser.add_argument(
        'commit_hash',
        metavar='commit',
        type=str,
        nargs=1,
        help='commit hash to copy files from')
    parser.add_argument(
        '--dry_run',
        dest='dry_run',
        action='store_const',
        const=True,
        default=False)
    arg = parser.parse_args(sys.argv[1:])

    # Read file list from HEAD and upstream commit.
    upstream_files = utils.get_file_list(arg.commit_hash[0])
    our_files = utils.get_file_list('HEAD')

    # Calculate target file list
    target_files = filters.filter_file(our_files, upstream_files)

    # Calculate operations needed
    ops = utils.gen_op(our_files, target_files)

    if arg.dry_run:
        # Print ops only on dry-run mode.
        print('\n'.join(repr(x) for x in ops))
        return
    for op, f in ops:
        # Ignore if op is REP because we only want to copy missing files, not to
        # revert custom Chromium OS libchrome patch.
        assert type(op) == utils.DiffOperations
        if op == utils.DiffOperations.DEL:
            subprocess.check_call(['git', 'rm', f.path]),
        elif op == utils.DiffOperations.ADD:
            # Create directory recursively if not exist.
            os.makedirs(os.path.dirname(f.path), exist_ok=True)
            # Read file by git cat-file with blob object id to avoid heavy git checkout.
            with open(f.path, 'wb') as outfile:
                subprocess.check_call(['git', 'cat-file', 'blob', f.id],
                                      stdout=outfile)
            # Add to git index
            subprocess.check_call(['git', 'add', f.path])

if __name__ == '__main__':
    main()
