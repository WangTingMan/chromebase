#!/usr/bin/env python3
# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import collections
import datetime
import os
import subprocess
import sys
import time

import filtered_utils
import filters
import lazytree
import utils

# Use avg speed of last TIMING_DISTANCE commits.
_TIMING_DISTANCE = 100
# Verify the tree is consistent (diff-based, and actual) when a commit is made
# after every _VERIFY_INTEGRITY_DISTANCE in browser repository.
# Merge commits are always verified.
_VERIFY_INTEGRITY_DISTANCE = 1000


def timing(timing_deque, update=True):
    """Returns a speed (c/s), and updates timing_deque.

    Args:
        timing_deque: a deque to store the timing of past _TIMING_DISTANCE.
        update: adds current timestamp to timing_deque if True. It needs to set
            to False, if it wants to be called multiple times with the current
            timestamp.
    """
    first = timing_deque[0]
    now = time.time()
    if update:
        timing_deque.append(now)
        if len(timing_deque) > _TIMING_DISTANCE:
            timing_deque.popleft()
    return _TIMING_DISTANCE / (now - first)


def get_start_commit_of_browser_tree(parent_filtered):
    """Returns the last commit committed by the script, and its metadata.

    Args:
        parent_filtered: the commit hash of the tip of the filtered branch.
    """
    current = parent_filtered
    while True:
        meta = filtered_utils.get_metadata(current)
        if meta.original_commits:
            return current, meta
        if not meta.parents:
            return None, None
        # Follow main line only
        current = meta.parents[0]


def find_filtered_commit(commit, commits_map):
    """Finds the corresponding parent of a browser commit in filtered branch.

    If not found, the corresponding commit of its least ancestor is used.

    Args:
        commit: commit hash in browser repository.
        commits_map: commit hash mapping from original commit to the one in the
            filtered branch. commits_map may be altered.
    """
    look_for = commit
    while look_for not in commits_map:
        meta = filtered_utils.get_metadata(look_for)
        assert len(meta.parents) <= 1
        if len(meta.parents) == 1:
            look_for = meta.parents[0]
        else:
            look_for = 'ROOT'
    commits_map[commit] = commits_map[look_for]
    return commits_map[look_for]


def do_commit(treehash, commithash, meta, commits_map):
    """Makes a commit with the given arguments.

    This creates a commit on the filtered branch with preserving the original
    commiter name, email, authored timestamp and the message.
    Also, the special annotation `CrOS-Libchrome-Original-Commit:
    <original-commit-hash>' is appended at the end of commit message.
    The parent commits are identified by the parents of the original commit and
    commits_map.

    Args:
        treehash: tree object id for this commit.
        commithash: original commit hash, used to append to commit message.
        meta: meta data of the original commit.
        commits_map: current known commit mapping. commits_map may be altered.
    """
    parents_parameters = []
    for parent in meta.parents:
        parents_parameters.append('-p')
        parents_parameters.append(find_filtered_commit(parent, commits_map))
    msg = (meta.message + b'\n\n' +
           filtered_utils.CROS_LIBCHROME_ORIGINAL_COMMIT +
           b': ' + commithash + b'\n')
    return subprocess.check_output(
        ['git', 'commit-tree'] + parents_parameters + [treehash],
        env=dict(os.environ,
                 GIT_AUTHOR_NAME=meta.authorship.name,
                 GIT_AUTHOR_EMAIL=meta.authorship.email,
                 GIT_AUTHOR_DATE=b' '.join([meta.authorship.time,
                                            meta.authorship.timezone])),
        input=msg).strip(b'\n')


def verify_commit(original_commit, new_tree):
    """Verifies if new_tree is exactly original_commit after filters.

    Args:
        original_commit: commit hash in Chromium browser tree.
        new_tree: tree hash created for upstream branch commit.
    """
    expected_file_list = filters.filter_file([], utils.get_file_list(original_commit))
    assert utils.git_mktree(expected_file_list) == new_tree


def process_commits(pending_commits, commits_map, progress_callback, commit_callback):
    """Processes new commits in browser repository.

    Returns the commit hash of the last commit made.

    Args:
        pending_commits: list of tuple (commit hash, parent hashes) to process,
            in topological order.
        commits_map: current known commit mapping. may be altered.
            progress_callback: callback for every commit in pending_commits. It
            should take (idx, total, orig_commit_hash, meta) as parameters.
        commit_callback: callback when a commit is made to filtered branch. It
            should take (orig_commit_hash, new_commit_hash, meta) as parameters.
    """
    last_commit = None
    last_verified = -1
    for i, commit in enumerate(pending_commits, start=1):
        meta = filtered_utils.get_metadata(commit[0])
        if progress_callback:
            progress_callback(i, len(pending_commits), commit[0], meta)
        diff_with_parent = filters.filter_diff(utils.git_difftree(
            meta.parents[0] if meta.parents else None, commit[0]))
        git_lazytree = lazytree.LazyTree(
            filtered_utils.get_metadata(
                find_filtered_commit(meta.parents[0], commits_map)).tree
            if meta.parents else None)
        if len(meta.parents) <= 1 and len(diff_with_parent) == 0:
            # not merge commit    AND no diff
            if len(meta.parents) == 1 and meta.parents[0] in commits_map:
                commits_map[commit[0]] = commits_map[meta.parents[0]]
            continue
        for op, f in diff_with_parent:
            if op == utils.DiffOperations.ADD or op == utils.DiffOperations.REP:
                git_lazytree[f.path] = f
            elif op == utils.DiffOperations.DEL:
                del git_lazytree[f.path]
        treehash_after_diff_applied = git_lazytree.hash()
        filtered_commit = do_commit(treehash_after_diff_applied, commit[0],
                                    meta, commits_map)
        if commit_callback:
            commit_callback(commit[0], filtered_commit, meta)
        commits_map[commit[0]] = filtered_commit
        last_commit = filtered_commit
        if len(meta.parents) > 1 or (i - last_verified >=
                                     _VERIFY_INTEGRITY_DISTANCE):
            # merge commit    OR  every _VERIFY_INTEGRITY_DISTANCE
            last_verified = i
            verify_commit(commit[0], treehash_after_diff_applied)
    # Verify last commit
    verify_commit(pending_commits[-1][0], filtered_utils.get_metadata(last_commit).tree)
    return last_commit


def main():
    # Init args
    parser = argparse.ArgumentParser(
        description='Copy file from given commits')
    parser.add_argument(
        'parent_filtered', metavar='parent_filtered', type=str, nargs=1,
        help='commit hash in filtered branch to continue from. usually HEAD of that branch.')
    parser.add_argument(
        'goal_browser', metavar='goal_browser', type=str, nargs=1,
        help='commit hash in browser master branch.')
    parser.add_argument(
        '--dry_run', dest='dry_run', action='store_const', const=True, default=False)
    arg = parser.parse_args(sys.argv[1:])

    # Look for last known commit made by the script in filtered branch.
    print('Looking for last known commit from', arg.parent_filtered[0])
    last_known, meta_last_known = get_start_commit_of_browser_tree(
        arg.parent_filtered[0])
    if last_known:
        print('Continuing from', last_known, meta_last_known)
    else:
        print('No known last commit')
    print('parent on filter branch', arg.parent_filtered[0])

    # Get a mapping between browser repository and filtered branch for commits
    # in filtered branch.
    print('reading commits details for commits mapping')
    timing_deque = collections.deque([time.time()])
    commits_map = filtered_utils.get_commits_map(
        arg.parent_filtered[0],
        lambda cur_idx, tot_cnt, cur_hash:
        (
            print('Reading', cur_hash, '%d/%d' % (cur_idx, tot_cnt),
                  '%f c/s' % timing(timing_deque),
                  end='\r', flush=True),
        ))
    if not 'ROOT' in commits_map:
        commits_map['ROOT'] =subprocess.check_output(
            ['git', 'commit-tree', '-p', arg.parent_filtered[0],
             utils.git_mktree([])],
            input=filtered_utils.CROS_LIBCHROME_INITIAL_COMMIT).strip(b'\n')
    print()
    print('loaded commit mapping of', len(commits_map), 'commit')

    # Process newer commits in browser repository from
    # last_known.original_commits
    print('search for commits to filter')
    timing_deque= collections.deque([time.time()])
    pending_commits = utils.git_revlist(
        meta_last_known.original_commits[0] if meta_last_known else None,
        arg.goal_browser[0])
    print(len(pending_commits), 'commits to process')
    new_head = process_commits(
        pending_commits,
        commits_map,
        # Print progress
        lambda cur_idx, tot_cnt, cur_hash, cur_meta: (
            print('Processing',
                  cur_hash, '%d/%d' % (cur_idx, tot_cnt),
                  '%f c/s' % timing(timing_deque, update=False),
                  'eta %s' % (
                      datetime.timedelta(
                          seconds=int((tot_cnt - cur_idx) / timing(timing_deque)))),
                  cur_meta.title[:50],
                  end='\r', flush=True),
        ),
        # Print new commits
        lambda orig_hash, new_hash, commit_meta:
            print(b'%s is commited as %s: %s' % (orig_hash, new_hash,
                                                 commit_meta.title[:50]))
    )
    print()
    print('New HEAD should be', new_head.decode('ascii'))


if __name__ == '__main__':
    main()
