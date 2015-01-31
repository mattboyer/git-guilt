# -*- coding: UTF-8 -*-
"""
Port of git-guilt to Python
"""

import re
import os
import argparse
import subprocess
import collections
import functools
import sys
# Terminal stuff
import fcntl
import termios
import struct


class GitError(Exception):
    pass


class GitRunner(object):
    _toplevel_args = ['rev-parse', '--show-toplevel']
    _author_regex = r'^[^(]*\((.*?) \d{4}-\d{2}-\d{2}'
    _git_executable = 'git'

    def __init__(self):
        self.name_regex = re.compile(GitRunner._author_regex)
        self._git_toplevel = None
        try:
            self._get_git_root()
        except GitError as ex:
            # Do something appropriate
            sys.stderr.write(str(ex))
            raise SystemExit(4)

    def _get_git_root(self):
        # We should probably go beyond just finding the root dir for the Git
        # repo and do some sanity-checking on git itself
        top_level_dir = self._run_git(GitRunner._toplevel_args)
        self._git_toplevel = top_level_dir[0]

    def _run_git(self, args):
        '''
        Runs the git executable with the arguments given and returns a list of
        lines produced on its standard output.
        '''

        popen_kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'universal_newlines': True,
        }

        if self._git_toplevel:
            popen_kwargs['cwd'] = self._git_toplevel

        git_process = subprocess.Popen(  # pylint: disable=W0142
            [GitRunner._git_executable] + args,
            **popen_kwargs
        )

        try:
            out, err = git_process.communicate()
            git_process.wait()
        except Exception as e:
            raise GitError("Couldn't run 'git {args}':{newline}{ex}".format(
                args=' '.join(args),
                newline=os.linesep,
                ex=str(e)
            ))

        if (0 != git_process.returncode) or err:
            raise GitError("'git {args}' failed with:{newline}{err}".format(
                args=' '.join(args),
                newline=os.linesep,
                err=err
            ))

        if not out:
            raise ValueError("No output")
        return out.splitlines()

    def get_delta_files(self, since_rev, until_rev):
        '''
        Returns a list of files which have been modified between since_rev and
        until_rev.
        '''

        diff_args = ['diff', '--name-only', since_rev]
        if until_rev:
            diff_args.append(until_rev)

        file_list = self._run_git(diff_args)
        if 0 == len(file_list):
            raise ValueError()
        return set(file_list)

    def populate_tree(self, rev):
        ls_tree_args = ['ls-tree', '-r', '--name-only', '--', rev]
        try:
            lines = self._run_git(ls_tree_args)
        except GitError as ge:
            raise ge

        return lines

    def blame_locs(self, blame):
        # blame.repo_path may not exist for this particular revision
        # So what do we do then? if the file existed before, then surely all
        # LOCs should be subtracted from their authors' share of guilt
        # If, on the other hand, the file has *never* existed, then it's all
        # good.
        # Either way, that will be handled by the reducer
        blame_args = ['blame', '--', blame.repo_path]
        if blame.rev:
            blame_args.append(blame.rev)

        try:
            lines = self._run_git(blame_args)
        except GitError as ge:
            if 'no such path ' in str(ge):
                return None
            else:
                raise ge

        # TODO For now default to extracting names
        for line in lines:
            matches = self.name_regex.match(line)
            if matches:
                line_author = matches.group(1).strip()
                blame.bucket[line_author] += 1


class BlameTicket(object):
    '''A queued blame. This is a TODO item, really'''

    def __init__(self, bucket, path, rev):
        self.bucket = bucket
        self.repo_path = path
        self.rev = rev

    def __eq__(self, blame):
        return (self.bucket == blame.bucket) \
            and (self.repo_path == blame.repo_path) \
            and (self.bucket == blame.bucket)


class Formatter(object):
    _CSI = r'['
    _green = _CSI + '32m'
    _red = _CSI + '31m'
    _normal = _CSI + '0m'
    _default_width = 80

    def __init__(self, deltas):
        self.deltas = deltas
        self._is_tty = os.isatty(sys.stdout.fileno())
        self._tty_width = self._get_tty_width()

    @property
    def longest_name(self):
        return len(max(
            self.deltas, key=lambda d: len(d.author)
        ).author)

    @property
    def longest_count(self):
        return len(str(max(
            self.deltas, key=lambda d: len(str(d.count))
        ).count))

    @property
    def longest_bargraph(self):
        return abs(max(
            self.deltas, key=lambda d: abs(d.count)
        ).count)

    @property
    def bargraph_max_width(self):
        return self._tty_width - (5 + self.longest_name + self.longest_count)

    def _get_tty_width(self):
        if not self._is_tty:
            return Formatter._default_width

        try:
            (_, w, _, _) = struct.unpack(
                'HHHH',
                fcntl.ioctl(
                    sys.stdout.fileno(),
                    termios.TIOCGWINSZ,
                    struct.pack('HHHH', 0, 0, 0, 0)
                )
            )
        except IOError as e:
            sys.stderr.write(str(e))
            return Formatter._default_width

        if 0 < w:
            return w
        else:
            return Formatter._default_width

    def show_guilt_stats(self):
        # TODO Do something like diffstat's number of files changed, number or
        # insertions and number of deletions
        for delta in self.deltas:
            print(self.format(delta))

    def _scale_bargraph(self, graph_width):
        if 0 == graph_width:
            return 0

        if self.longest_bargraph <= self.bargraph_max_width:
            return graph_width

        scaled_width = 1 + \
            int(graph_width * (self.bargraph_max_width - 1) /
                self.longest_bargraph)

        return scaled_width

    def format(self, delta):
        bargraph = str()

        graph_width = self._scale_bargraph(abs(delta.count))

        if delta.count > 0:
            bargraph = '+' * graph_width
            if self._is_tty:
                bargraph = Formatter._green + bargraph + Formatter._normal
        elif delta.count < 0:
            bargraph = '-' * graph_width
            if self._is_tty:
                bargraph = Formatter._red + bargraph + Formatter._normal

        return " {author} | {count} {bargraph}".format(
            author=delta.author.ljust(self.longest_name),
            count=str(delta.count).rjust(self.longest_count),
            bargraph=bargraph,
        )


class Delta(object):
    def __init__(self, author, since, until):
        self.author = author
        self.since_locs = since
        self.until_locs = until

    def __repr__(self):
        return "<Delta \"{author}\": {count} ({since}->{until})>".format(
            author=self.author,
            count=self.count,
            since=self.since_locs,
            until=self.until_locs,
        )

    @property
    def count(self):
        return self.until_locs - self.since_locs

    def __eq__(self, rhs):
        return (self.author == rhs.author) \
            and (self.count == rhs.count)

    def __ne__(self, rhs):
        return not (self == rhs)

    def __lt__(self, rhs):
        if self.count > rhs.count:
            return True
        elif self.count == rhs.count:
            # Compare the authors' names
            return self.author < rhs.author
        else:
            return False

    def __le__(self, rhs):
        return (self < rhs) or (self == rhs)

    def __gt__(self, delta):
        if self.count < delta.count:
            return True
        elif self.count == delta.count:
            # Compare the authors' names
            return self.author > delta.author
        else:
            return False

    def __ge__(self, rhs):
        return (self > rhs) or (self == rhs)


class PyGuilt(object):
    """Implements crap"""

    def __init__(self):
        self.runner = GitRunner()
        # This should probably be spun out
        self.parser = argparse.ArgumentParser(prog='git guilt')
        self.parser.add_argument(
            '-w',
            '--whitespace',
            action='store_true',
        )
        self.parser.add_argument('-e', '--email', action='store_true')
        self.parser.add_argument('since', nargs='?')
        # Surely until should default to something sensible
        self.parser.add_argument('until', nargs='?')
        self.args = None

        self.blame_queue = list()
        # This is a port of the JS blame object. The since and until members
        # are 'buckets'
        self.since = collections.defaultdict(int)
        self.until = collections.defaultdict(int)
        self.loc_deltas = list()

        self.trees = dict()
        self.formatter = Formatter(self.loc_deltas)

    def process_args(self):
        self.args = self.parser.parse_args()
        if not (self.args.since and self.args.until):
            raise GitError('bad args')

    def populate_trees(self):
        self.trees[self.args.since] = self.runner.populate_tree(
            self.args.since
        )
        self.trees[self.args.until] = self.runner.populate_tree(
            self.args.until
        )

    def map_blames(self):
        """Prepares the list of blames to tabulate"""

        for repo_path in self.runner.get_delta_files(
                self.args.since, self.args.until
                ):

            self.blame_queue.append(
                BlameTicket(self.since, repo_path, self.args.since)
            )

            self.blame_queue.append(
                BlameTicket(self.until, repo_path, self.args.until)
            )

        # TODO This should be made parallel
        for blame in self.blame_queue:
            if blame.repo_path in self.trees[blame.rev]:
                self.runner.blame_locs(blame)

    def _reduce_since_blame(self, deltas, since_blame):
        author, loc_count = since_blame
        until_loc_count = self.until[author] or 0
        # LOC counts are always >=0
        deltas.append(Delta(author, loc_count, until_loc_count))
        return deltas

    def _reduce_until_blame(self, deltas, until_blame):
        author, loc_count = until_blame
        if author not in self.since:
            # We have a new author
            deltas.append(Delta(author, 0, loc_count))
        else:
            # TODO We may need to write off some guilt
            pass
        return deltas

    def reduce_blames(self):
        self.loc_deltas = functools.reduce(
            self._reduce_since_blame,
            self.since.items(),
            self.loc_deltas
        )

        self.loc_deltas = functools.reduce(
            self._reduce_until_blame,
            self.until.items(),
            self.loc_deltas
        )

        self.loc_deltas.sort()
        return self.loc_deltas

    def run(self):
        try:
            self.process_args()
        except GitError as ex:
            sys.stderr.write(str(ex))
            return 1
        else:
            self.populate_trees()

            self.map_blames()
            self.reduce_blames()
            self.formatter.show_guilt_stats()
            return 0


def main():
    sys.exit(PyGuilt().run())

if '__main__' == __name__:
    main()
