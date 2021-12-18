#!/usr/bin/env python3
# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Utility to apply diffs between given two upstream commit hashes to current
workspace.

This utility diffs files between old_commit and new_commit, with hard-coded
filter rules, and apply the diff to current HEAD with 3-way-merge supported.

This can be used to uprev a libchrome directory when this is not git history for
git merge to work.
"""

import argparse
import subprocess
import sys

import filters
import utils

def main():
    # Init args
    parser = argparse.ArgumentParser(
        description='Copy file from given commits')
    parser.add_argument(
        'old_commit', metavar='old_commit', type=str, nargs=1,
        help='commit hash in upstream branch or browser repository '
             'we want to uprev from')
    parser.add_argument(
        'new_commit', metavar='new_commit', type=str, nargs=1,
        help='commit hash in upstream branch or browser repository '
             'we want ot uprev to')
    parser.add_argument(
        '--dry_run', dest='dry_run', action='store_const', const=True, default=False)
    parser.add_argument(
        '--is_browser', dest='is_browser', action='store_const', const=True, default=False,
        help='is the commit hash in browser repository')
    arg = parser.parse_args(sys.argv[1:])

    # Get old and new files.
    old_files = utils.get_file_list(arg.old_commit[0])
    new_files = utils.get_file_list(arg.new_commit[0])

    if arg.is_browser:
        old_files = filters.filter_file([], old_files)
        new_files = filters.filter_file([], new_files)
        assert filters.filter_file(old_files, []) == []
        assert filters.filter_file(new_files, []) == []

    # Generate a tree object for new files.
    old_tree = utils.git_mktree(old_files)
    new_tree = utils.git_mktree(new_files)
    newroot = utils.git_commit(old_tree, [])
    squashed = utils.git_commit(new_tree, [newroot])

    # Generate patch for git am
    patch = subprocess.check_output(['git', 'format-patch', '--stdout', newroot+b'..'+squashed])

    if arg.dry_run:
        print(patch.decode('utf-8'))
    else:
        subprocess.run(['git', 'am', '-3'], input=patch)


if __name__ == '__main__':
    main()
