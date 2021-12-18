#!/usr/bin/env python3
# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Utility to disconnect history of files from a branch, and reconnect with base on
a different branch.
"""

import argparse
import collections
import subprocess
import sys

import filtered_utils
import lazytree
import utils


class CommitMetadataFactory(dict):
    """Dict-like class to read commit metadata"""

    def __missing__(self, key):
        """Reads commit metadata if missing"""
        value = filtered_utils.get_metadata(key)
        self.__setitem__(key, value)
        return value


def disconnect(source_commit, ref_commit):
    """Creates a commit that disconnects files from source_commit.

    All files existing in ref_commit will be removed from source_commit.

    Args:
        source_commit: commit hash to disconnect from.
        ref_commit: commit hash to be a file list reference.
    """
    source_files = utils.get_file_list(source_commit)
    ref_files = utils.get_file_list(ref_commit)
    ref_files_set = set(ref.path for ref in ref_files)
    kept_files = [ref for ref in source_files if ref.path not in ref_files_set]
    tree = utils.git_mktree(kept_files)
    return utils.git_commit(
        tree, [source_commit],
        message=b'Disconnect history from %s' % (source_commit.encode('ascii')))


def connect_base(current_commit, base_commit):
    """Creates a merge commit that takes files from base_commit.

    Literally it's identical to git merge base_commit in current_commit.

    Args:
        current_commit: commit hashes on where to commit to.
        base_commit: commit hashes contains file histories.
    """
    current_files = utils.get_file_list(current_commit)
    base_files = utils.get_file_list(base_commit)
    tree = utils.git_mktree(current_files + base_files)
    return utils.git_commit(
        tree, [current_commit, base_commit],
        message=b'Connect history with base %s' % (base_commit.encode('ascii')))


def blame_files(commithash, files):
    """Blames files on givven commithash"""
    blames = {}
    for path in files:
        blames[path] = utils.git_blame(commithash, path)
    return blames


def search_blame_line(blames, amend_commits, target_commit_hash):
    """Searches blames matching target_commit_hash in amend_commits

    Returns a map from file path to a list of tuple, each tuple has
    len(amend_commits) + 1 elements.  0-th element is the line in blames. and
    1st to n-th element are corresponding lines in amend_commits blaems.

    Args:
        blames: a dict from path to list of GitBlameLine, for files blamed on
            target_commit_hash.
        amend_commits: a list of commit hashes to provide actual history.
        target_commit_hash: commit hash that blames are blaemd on.
    """
    blames_combined = {}
    for blame_file_path, blame_file in blames.items():
        blames_amend = [
            utils.git_blame(commit, blame_file_path) for commit in amend_commits
        ]
        blames_combined[blame_file_path] = [
            blame_combined for blame_combined in zip(blame_file, *blames_amend)
            if blame_combined[0].commit == target_commit_hash
        ]
    return blames_combined


def get_track_from_blames(blames_combined, virtual_goal_commit, amend_commits,
                          commit_choice_cache, commit_msg_cache):
    """Blames diffs and locate the amend commits.

    Returns a tuple containing:
     - a set of commit hashes in amend_commits tree;
     - a line-by-line mapping for files in diff to commit hashes in
       amend_commits tree of diffed lines.

    Args:
        blames_combined: a map from path to a list of tuple. each tuple reflect
            one line, and has len(amend_commits)+1 elements. See more details in
            search_blame_line.
        virtual_goal_commit: a commit that contains no useful history for diffs.
        amend_commits: list of HEAD commit hashes that refers to tree that can
            amend the diffs.
        commit_choice_cache: caches user choice on which amend commit to use.
        commit_msg_cache: caches commit metadata.
    """
    blame_untracked_lines = {}
    commits_to_track = set()

    for blame_file_path, blame_lines in blames_combined.items():
        blame_untracked_lines[blame_file_path] = []
        for blame_line in blame_lines:
            original_commits = tuple(
                blame_amend.commit for blame_amend in list(blame_line)[1:])
            chosen = commit_choice_cache.get(original_commits)
            if chosen is None:
                for idx, original_commit in enumerate(original_commits):
                    print('%d: %s' % (idx,
                                      commit_msg_cache[original_commit].title))
                # No validation on user_choice since no untrusted user.
                # Also the developer can rerun if entered wrongly by accident.
                user_choice = int(input('Choose patch: '))
                chosen = original_commits[user_choice]
                commit_choice_cache[original_commits] = chosen
            commits_to_track.add(chosen)
            blame_untracked_lines[blame_file_path].append((blame_line[0],
                                                           chosen))

    return commits_to_track, blame_untracked_lines


def reconstruct_file(blame_goal, blame_base, lines_to_reconstruct,
                     virtual_goal_commit):
    """Reconstrucs a file to reflect changes in lines_to_reconstruct.

    Takes lines to blame_base, and blame_goal it belongs lines_to_reconstruct.
    It also deletes removed lines nearby.

    Returns a binary for the new file content.

    Args:
        blame_goal: a list of utils.GitBlameLine blaming the file on
            virtual_goal_commit.
        blame_base: a list of utils.GitBlameLine blaming the file on last
            commited commit.
        lines_to_reconstruct: only to reconstruct these lines, instead of
            everything in blame_goal. It is represented in a list of
            GitBlameLine.
        virtual_goal_commit: commit hash where blame_goal is based on.
    """
    idx_base, idx_goal = 0, 0
    reconstructed_file = []

    print('Changed lines are', [line.data for line in lines_to_reconstruct])
    line_iter = iter(lines_to_reconstruct)
    line = next(line_iter, None)
    while idx_base < len(blame_base) or idx_goal< len(blame_goal):
        # Both sides are idendical. We can't compare blame_base, and line
        # directly due to blame commit difference could end up different lineno.
        if (idx_base < len(blame_base) and
                blame_base[idx_base].data == blame_goal[idx_goal].data and
                blame_base[idx_base].commit == blame_goal[idx_goal].commit):
            # We append this line if both sides are identical.
            reconstructed_file.append(blame_base[idx_base].data)
            idx_base += 1
            idx_goal += 1
            should_skip_base = False
        elif line and blame_goal[idx_goal] == line:
            # We append the line from goal, if blame_goal[idx_goal] is the line
            # we're interested in.
            reconstructed_file.append(line.data)
            line = next(line_iter, None)
            idx_goal += 1
            should_skip_base = True
        elif blame_goal[idx_goal].commit == virtual_goal_commit:
            # We skip the line from goal, if the change in not in the commit
            # we're interested. Thus, changed lines in other commits will not be
            # reflected.
            idx_goal += 1
        else:
            # We should skip base if we just appended some lines from goal.
            # This would treat modified lines and append first and skip later.
            # If we didn't append something from goal, lines from base should be
            # preserved because the modified lines are not in the commit we're
            # currently interested in.
            if not should_skip_base:
                reconstructed_file.append(blame_base[idx_base].data)
            idx_base += 1

    return b''.join([line + b'\n' for line in reconstructed_file])


def reconstruct_files(track_commit, blame_untracked_lines, blames,
                      current_base_commit, virtual_goal_commit):
    """Reconstructs files to reflect changes in track_commit.

    Returns a map from file path to file content for reconstructed files.

    Args:
        track_commit: commit hashes to track, and reconstruct from.
        blame_untracked_lines: a line-by-line mapping regarding selected amend
            commits for diffs. see get_track_from_blames for more.
        blames: a map from filename to list of utils.GitBlameLine
        current_base_commit: commit hashes for HEAD of base that contains base
            history + already committed amend history.
        virtual_goal_commit: commit hash for one giant commit that has no
            history.  virtual_goal_commit is one commit ahead of
            current_base_commit.
    """
    lines_to_track = collections.defaultdict(list)
    for file, lines in blame_untracked_lines.items():
        for line in lines:
            if line[1] == track_commit:
                lines_to_track[file].append(line[0])
    constructed_files = {}
    for current_file, current_file_lines in lines_to_track.items():
        print('Reconstructing', current_file, 'for', track_commit)
        blame_base = utils.git_blame(current_base_commit, current_file)
        constructed_files[current_file] = reconstruct_file(
            blames[current_file], blame_base, current_file_lines,
            virtual_goal_commit)
    return constructed_files


def main():
    # Init args
    parser = argparse.ArgumentParser(description='Reconnect git history')
    parser.add_argument(
        'disconnect_from',
        metavar='disconnect_from',
        type=str,
        nargs=1,
        help='disconnect history from this commit')
    parser.add_argument(
        'base_commit',
        metavar='base_commit',
        type=str,
        nargs=1,
        help='base commit to use the history')
    parser.add_argument(
        'amend_commits',
        metavar='amend_commits',
        type=str,
        nargs='+',
        help='commits to amend histories from base_commit')

    arg = parser.parse_args(sys.argv[1:])
    empty_commit = disconnect(arg.disconnect_from[0], arg.base_commit[0])
    connected_base = connect_base(empty_commit, arg.base_commit[0])

    commit_msg_cache = CommitMetadataFactory()
    commit_choice_cache = {}
    last_commit = connected_base
    # In each iteration of the loop, it
    #  - re-create the new goal commit, (base + committed history + (one giant)
    #  uncommited history).
    #  - blame on new goal commit and tot of amend commits. map line-by-line
    #  from uncommited to past histories.
    #  - choose one of the past commits, reconstruct files to reflect changes in
    #  that commit, and create a new commits.
    # last_commit, commit_msg_cache, commit_choice_cache will be persistent
    # across iteratins.
    while True:
        # One commit is processed per iteration.

        # Create virtual target commit, and its diff.
        virtual_goal = utils.git_commit(arg.disconnect_from[0] + '^{tree}',
                                        [last_commit])
        diffs = utils.git_difftree(None, virtual_goal)
        if not diffs:
            print('No diffs are found between %s and goal.' %
                  (last_commit.decode('ascii'),))
            break

        blames = blame_files(virtual_goal,
                             [diff.file.path for diff in diffs])
        blames_combined = search_blame_line(blames, arg.amend_commits,
                                            virtual_goal)

        commits_to_track, blame_untracked_lines = get_track_from_blames(
            blames_combined, virtual_goal, arg.amend_commits,
            commit_choice_cache, commit_msg_cache)
        if not commits_to_track:
            print('no commits to track, stopping')
            break

        # Stablely choose one commit from commits_to_track, and reconstruct it.
        track_commit = min(commits_to_track)
        print('Reconstructing commit %s: %s' %
              (track_commit, commit_msg_cache[track_commit].title))
        constructed_files = reconstruct_files(track_commit,
                                              blame_untracked_lines, blames,
                                              last_commit, virtual_goal)

        # Mktree and commit with re-constructed_files.
        tree = lazytree.LazyTree(filtered_utils.get_metadata(last_commit).tree)
        for filename, filedata in constructed_files.items():
            blob = subprocess.check_output(
                ['git', 'hash-object', '-w', '/dev/stdin'],
                input=filedata).strip()
            tree[filename] = utils.GitFile(filename, tree[filename].mode, blob)
        meta = commit_msg_cache[track_commit]
        last_commit = utils.git_commit(
            tree.hash(), [last_commit],
            (meta.message + b'\n(Reconstructed from ' + track_commit + b')\n'),
            dict(
                GIT_AUTHOR_NAME=meta.authorship.name,
                GIT_AUTHOR_EMAIL=meta.authorship.email,
                GIT_AUTHOR_DATE=b' '.join(
                    [meta.authorship.time, meta.authorship.timezone])))
        print('Reconstructed as', last_commit)
    # Make last commit for history reconstruction.
    print(
        utils.git_commit(
            filtered_utils.get_metadata(arg.disconnect_from[0]).tree,
            [last_commit],
            b'Finished history reconstruction\n\nRemoving unnecessary lines\n'))


if __name__ == '__main__':
    main()
