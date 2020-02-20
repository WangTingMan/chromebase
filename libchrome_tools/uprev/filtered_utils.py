# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
""" Provides utilities for filtered branch handling. """

import collections
import re
import subprocess

import utils

# Keyword to uniquely identify the beginning of upstream history.
CROS_LIBCHROME_INITIAL_COMMIT = b'CrOS-Libchrome-History-Initial-Commit'
# Keyword to identify original commit in Chromium browser repository.
CROS_LIBCHROME_ORIGINAL_COMMIT = b'CrOS-Libchrome-Original-Commit'


# Stores metadata required for a git commit.
GitCommitMetadata = collections.namedtuple(
    'GitCommitMetadata',
    ['parents', 'original_commits', 'tree', 'authorship', 'title', 'message', 'is_root',]
)


# Stores information for a commit authorship.
GitCommitAuthorship = collections.namedtuple(
    'GitCommitAuthorship',
    ['name', 'email', 'time', 'timezone',]
)


def get_metadata(commit_hash):
  """Returns the metadata of the commit specified by the commit_hash.

  This function parses the commit message of the commit specified by the
  commit_hash, then returns its GitCommitMetadata instance.
  The commit must be on the filtered branch, otherwise some metadata may be
  omitted.
  Returns metadata from the commit message about commit_hash on the filtered
  branch.

  Args:
      commit_hash: the commit hash on the filtered branch.
  """

  ret = subprocess.check_output(['git', 'cat-file', 'commit',
                                 commit_hash]).split(b'\n')
  parents = []
  tree_hash = None
  authorship = None
  author_re = re.compile(rb'^(.*) <(.*)> ([0-9]+) ([^ ])+$')
  while ret:
      line = ret[0]
      ret = ret[1:]
      if not line.strip():
          # End of header. break.
          break
      tag, reminder = line.split(b' ', 1)
      if tag == b'tree':
          tree_hash = reminder
      elif tag == b'author':
          m = author_re.match(reminder)
          assert m, (line, commit_hash)
          authorship = GitCommitAuthorship(m.group(1),
                                           m.group(2),
                                           m.group(3),
                                           m.group(4))
      elif tag == b'parent':
          parents.append(reminder)

  title = ret[0] if ret else None

  original_commits = []
  is_root = False
  for line in ret:
      if line.startswith(CROS_LIBCHROME_ORIGINAL_COMMIT):
          original_commits.append(line.split(b':')[1].strip())
      if line == CROS_LIBCHROME_INITIAL_COMMIT:
          is_root = True
  msg = b'\n'.join(ret)
  return GitCommitMetadata(parents, original_commits, tree_hash, authorship,
                           title, msg, is_root)


def get_commits_map(commit_hash, progress_callback):
    """Returns a map from original commit hashes to filtered commit hashes.

    This function traverses the filtered branch from the commit specified by
    commit_hash to its root, then parses each commit message and constructs the
    map of those commits.

    Args:
        commit_hash: the commit hash on the filtered branch.
        progress_callback: called every commit is being read. Parameters taken
            are (idx, total_commits, current_commit)
    """
    commits_map = {}
    commits_filtered_tree = utils.git_revlist(None, commit_hash)
    for index, commit in enumerate(commits_filtered_tree, start=1):
        if progress_callback:
            progress_callback(index, len(commits_filtered_tree), commit[0])
        meta = get_metadata(commit[0])
        for original_commit in meta.original_commits:
            commits_map[original_commit] = commit[0]
        if meta.is_root:
            assert 'ROOT' not in commits_map
            commits_map['ROOT'] = commit[0]
    return commits_map
