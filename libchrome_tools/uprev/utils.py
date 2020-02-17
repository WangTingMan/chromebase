# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Provide some basic utility functions for libchrome tools."""

import collections
import enum
import os
import re
import subprocess

class DiffOperations(enum.Enum):
    """
    Describes operations on files
    """
    ADD = 1
    DEL = 2
    REP = 3

GitFile = collections.namedtuple(
    'GitFile',
    ['path', 'mode', 'id',]
)


def _reverse(files):
    """
    Creates a reverse map from file path to file.
    Assert if a file path exist only once in files.

    files: list of files.
    """
    files_map = {}
    for i in files:
        if i.path in files_map:
            assert i.path not in files_map
        files_map[i.path] = i
    return files_map


def get_file_list(commit):
    """
    Gets list of files of a commit

    commit: commit hash or refs
    """

    output = subprocess.check_output(['git', 'ls-tree', '-r',
                                      commit]).split(b'\n')
    files = []
    # Line looks like
    # mode<space>type<space>id<tab>file name
    # split by tab first, and by space.
    re_line = re.compile(rb'^([^ ]*) ([^ ]*) ([^ ]*)\t(.*)$')
    for line in output:
        if not line:
            continue
        match = re_line.match(line)
        mode, gittype, blobhash, path = match.groups()
        if gittype == b'commit':
            continue
        assert gittype == b'blob', '%s\n\n%s' % (str(output), line)
        files.append(GitFile(path, mode, blobhash))
    return files


def gen_op(current_files, target_files):
    """
    Generates list of operations (add/delete/replace files) if we want to
    convert current_files in directory to target_files

    current_files: list of files in current directory.
    target_files: list of files we want it to be in current directory.
    """
    current_file_map = _reverse(current_files)
    target_file_map = _reverse(target_files)
    op = []
    for i in sorted(current_file_map):
        if i not in target_file_map:
            op.append((DiffOperations.DEL, current_file_map[i]))
    for i in sorted(target_file_map):
        if i in current_file_map and current_file_map[i] != target_file_map[i]:
            op.append((DiffOperations.REP, target_file_map[i]))
        elif i not in current_file_map:
            op.append((DiffOperations.ADD, target_file_map[i]))
    return op


def git_mktree(files):
    """
    Returns a git tree object hash after mktree recursively
    """

    def recursive_default_dict():
        return collections.defaultdict(recursive_default_dict)

    tree = recursive_default_dict()
    for f in files:
        directories = f.path.split(b'/')
        directories, filename = directories[:-1], directories[-1]
        cwd = tree
        for directory in directories:
            # If cwd is a GitFile, which means a file and a directory shares the
            # same name.
            assert type(cwd) == collections.defaultdict
            cwd = cwd[directory]
        assert filename not in cwd
        cwd[filename] = f

    def _mktree(prefix, node):
        objects = []
        for name, val in node.items():
            prefix.append(name)
            if isinstance(val, collections.defaultdict):
                tree_hash = _mktree(prefix, val)
                objects.append(b'\t'.join(
                    [b' '.join([b'040000', b'tree', tree_hash]), name]))
            else:
                path = b'/'.join(prefix)
                assert path == val.path, '%s\n%s' % (str(path), str(val.path))
                objects.append(b'\t'.join(
                    [b' '.join([val.mode, b'blob', val.id]), name]))
            prefix.pop(-1)
        return subprocess.check_output(['git', 'mktree'],
                                       input=b'\n'.join(objects)).strip(b'\n')

    return _mktree([], tree)


def git_commit(tree, parents):
    """
    Create commit

    tree: tree object id
    parents: parent commit id
    """
    parent_args = []
    for parent in parents:
        parent_args.append('-p')
        parent_args.append(parent)
    return subprocess.check_output(
        ['git', 'commit-tree', tree] + parent_args,
        stdin=subprocess.DEVNULL).strip(b'\n')
