#!/usr/bin/env python3
# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import re
import subprocess

import utils


GIT_LSTREE_RE_LINE = re.compile(rb'^([^ ]*) ([^ ]*) ([^ ]*)\t(.*)$')


class LazyTree:
    """LazyTree does git mktree lazily."""

    def __init__(self, treehash=None):
        """Initializes a LazyTree.

        If treehash is not None, it initializes as the tree object.

        Args:
            treehash: tree object id. please do not use a treeish, it will fail
                later.
        """
        if treehash:
            self._treehash = treehash # tree object id of current tree
            self._subtrees = None # map from directory name to sub LazyTree
            self._files = None # map from file naem to utils.GitFile
            return
        # Initialize an empty LazyTree
        self._treehash = None
        self._subtrees = {}
        self._files = {}

    def _loadtree(self):
        """Loads _treehash into _subtrees and _files."""
        if self._files is not None: # _subtrees is also not None too here.
            return
        output = subprocess.check_output(['git', 'ls-tree', self._treehash]).split(b'\n')
        self._files = {}
        self._subtrees = {}
        for line in output:
            if not line:
                continue
            m = GIT_LSTREE_RE_LINE.match(line)
            mode, gittype, objecthash, name = m.groups()
            assert gittype == b'blob' or gittype == b'tree'
            assert name not in self._files and name not in self._subtrees
            if gittype == b'blob':
                self._files[name] = utils.GitFile(None, mode, objecthash)
            elif gittype == b'tree':
                self._subtrees[name] = LazyTree(objecthash)

    def _remove(self, components):
        """Removes components from self tree.

        Args:
            components: the path to remove, relative to self. Each element means
                one level of directory tree.
        """
        self._loadtree()
        self._treehash = None
        if len(components) == 1:
            del self._files[components[0]]
            return

        # Remove from subdirectory
        dirname, components = components[0], components[1:]
        subdir = self._subtrees[dirname]
        subdir._remove(components)
        if subdir.is_empty():
            del self._subtrees[dirname]

    def __delitem__(self, path):
        """Removes path from self tree.

        Args:
            path: the path to remove, relative to self.
        """
        components = path.split(b'/')
        self._remove(components)

    def _get(self, components):
        """Returns a file at components in utils.GitFile from self tree.

        Args:
            components: path in list instead of separated by /.
        """
        self._loadtree()
        if len(components) == 1:
            return self._files[components[0]]

        dirname, components = components[0], components[1:]
        return self._subtrees[dirname]._get(components)

    def __getitem__(self, path):
        """Returns a file at path in utils.GitFile from tree.

        Args:
            path: path of the file to read.
        """
        components = path.split(b'/')
        return self._get(components)

    def _set(self, components, f):
        """Adds or replace a file.

        Args:
            components: the path to set, relative to self. Each element means
                one level of directory tree.
            f: a utils.GitFile object.
        """

        self._loadtree()
        self._treehash = None
        if len(components) == 1:
            self._files[components[0]] = f
            return

        # Add to subdirectory
        dirname, components = components[0], components[1:]
        if dirname not in self._subtrees:
            self._subtrees[dirname] = LazyTree()
        self._subtrees[dirname]._set(components, f)

    def __setitem__(self, path, f):
        """Adds or replaces a file.

        Args:
            path: the path to set, relative to self
            f: a utils.GitFile object
        """
        assert f.path.endswith(path)
        components = path.split(b'/')
        self._set(components, f)

    def is_empty(self):
        """Returns if self is an empty tree."""
        return not self._subtrees and not self._files

    def hash(self):
        """Returns the hash of current tree object.

        If the object doesn't exist, create it.
        """
        if not self._treehash:
            self._treehash = self._mktree()
        return self._treehash

    def _mktree(self):
        """Recreates a tree object recursively.

        Lazily if subtree is unchanged.
        """
        keys = list(self._files.keys()) + list(self._subtrees.keys())
        mktree_input = []
        for name in sorted(keys):
            file = self._files.get(name)
            if file:
                mktree_input.append(b'%s blob %s\t%s' % (file.mode, file.id,
                                                         name))
            else:
                mktree_input.append(
                    b'040000 tree %s\t%s' % (self._subtrees[name].hash(), name))
        return subprocess.check_output(
            ['git', 'mktree'],
            input=b'\n'.join(mktree_input)).strip(b'\n')
