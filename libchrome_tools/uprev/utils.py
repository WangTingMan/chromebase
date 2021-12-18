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

GitDiffTree = collections.namedtuple(
    'GitDiffTree',
    ['op', 'file',]
)

GitBlameLine = collections.namedtuple(
    'GitBlameLine',
    ['data', 'commit', 'old_line', 'new_line',]
)


GIT_DIFFTREE_RE_LINE = re.compile(rb'^:([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*)\t(.*)$')


def _reverse(files):
    """Creates a reverse map from file path to file.

    Asserts if a file path exist only once in files.

    Args:
        files: list of files.
    """
    files_map = {}
    for i in files:
        if i.path in files_map:
            assert i.path not in files_map
        files_map[i.path] = i
    return files_map


def get_file_list(commit):
    """Gets a list of the files of the commit.

    Args:
        commit: commit hash or refs.
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


def git_difftree(treeish1, treeish2):
    """Gets diffs between treeish1 and treeish2.

    It returns a list of GitDiffTree, each GitDiffTree contains an ADD, DEL or
    REP operation and a GitFile.

    Args:
        treeish1, treeish2: treeish to diff.
            treeish can be tree hash or commit hash. If treeish1 is None, it
            generate difftrees with its parent.
    """
    out = None
    if treeish1 is None:
        # Remove first line since it's tree hash printed.
        out = subprocess.check_output(['git', 'diff-tree', '-r',
                                       treeish2]).split(b'\n')[1:]
    else:
        out = subprocess.check_output(['git', 'diff-tree', '-r',
                                       treeish1, treeish2]).split(b'\n')
    diff = []
    for line in out:
        if not line:
            continue
        match = GIT_DIFFTREE_RE_LINE.match(line)
        oldmode, newmode, oldhash, newhash, typeofchange, path = match.groups()
        assert typeofchange in b'ADMT', (treeish1, treeish2, line)
        if typeofchange == b'A':
            diff.append(
                GitDiffTree(DiffOperations.ADD,
                            GitFile(path, newmode, newhash)))
        elif typeofchange == b'D':
            diff.append(
                GitDiffTree(DiffOperations.DEL,
                            GitFile(path, oldmode, oldhash)))
        elif typeofchange == b'M' or typeofchange == b'T':
            diff.append(
                GitDiffTree(DiffOperations.REP,
                            GitFile(path, newmode, newhash)))
        else:
            raise Exception(b"Unsupported type: " + line)
    return diff


def gen_op(current_files, target_files):
    """Returns an operation list to convert files to target_files.

    Generates list of operations (add/delete/replace files) if we want to
    convert current_files in directory to target_files

    Args:
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
    """Returns a git tree object hash after mktree recursively."""

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


def git_commit(tree, parents, message=b"", extra_env={}):
    """Creates a commit.

    Args:
        tree: tree object id.
        parents: parent commit id.
        message: commit message.
        extra_env: extra environment variables passed to git.
    """
    parent_args = []
    for parent in parents:
        parent_args.append('-p')
        parent_args.append(parent)
    return subprocess.check_output(
        ['git', 'commit-tree', tree] + parent_args,
        input=message,
        env=dict(os.environ, **extra_env)).strip(b'\n')


def git_revlist(from_commit, to_commit):
    """Returns a list of commits and their parents.

    Each item in the list is a tuple, containing two elements.
    The first element is the commit hash; the second element is a list of parent
    commits' hash.
    """

    commits = []
    ret = None
    if from_commit is None:
        ret = subprocess.check_output(['git', 'rev-list', to_commit,
                                       '--topo-order', '--parents'])
    else:
        # b'...'.join() later requires all variable to be binary-typed.
        if type(from_commit) == str:
            from_commit = from_commit.encode('ascii')
        if type(to_commit) == str:
            to_commit = to_commit.encode('ascii')
        commit_range = b'...'.join([from_commit, to_commit])
        ret = subprocess.check_output(['git', 'rev-list', commit_range,
                                       '--topo-order', '--parents'])
    ret = ret.split(b'\n')
    for line in ret:
        if not line:
            continue
        hashes = line.split(b' ')
        commits.append((hashes[0], hashes[1:]))
    return list(reversed(commits))


def git_blame(commit, filepath):
    """Returns line-by-line git blame.

    Return value is represented by a list of GitBlameLine.

    Args:
        commit: commit hash to blame at.
        filepath: file to blame.
    """
    output = subprocess.check_output(['git', 'blame', '-p',
                                      commit, filepath])
    commit, old_line, new_line = None, None, None
    blames = []
    COMMIT_LINE_PREFIX = re.compile(b'^[0-9a-f]* ')
    for line in output.split(b'\n'):
        if not line:
            continue
        if line[0] == ord(b'\t'):
            assert commit != None
            blames.append(GitBlameLine(line[1:], commit, old_line, new_line))
            commit, old_line, new_line = None, None, None
        elif COMMIT_LINE_PREFIX.match(line):
            commit, old_line, new_line = line.split(b' ', 3)[0:3]
    return blames
