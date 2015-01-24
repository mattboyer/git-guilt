"""
Port of git-guilt to Python
"""

import re
import argparse
import subprocess
import collections
import functools
import sys


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

        print(args)
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
        except Exception as e:
            raise GitError("Couldn't run git: " + str(e))

        if err:
            raise GitError("Git failed with " + err)

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

    def _populate_tree(self, rev):
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
                blame.exists = False
                return None
            else:
                raise ge

        # TODO For now default to extracting names
        blame.exists = True
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
        self.exists = None

    def __eq__(self, blame):
        return (self.bucket == blame.bucket) \
            and (self.repo_path == blame.repo_path) \
            and (self.bucket == blame.bucket)


class Delta(object):
    _CSI = r'['
    _green = _CSI + '32m'
    _red = _CSI + '31m'
    _normal = _CSI + '0m'

    def __init__(self, author, adds, dels):
        self.author = author
        self.until_locs = adds
        self.since_locs = dels
        # We should probably keep track of until_locs and since_locs separately?

    def __repr__(self):
        return "<Delta \"{author}\": {count} ({a}-{d})>".format(
            author=self.author,
            count=self.count,
            a=self.until_locs,
            d=self.since_locs,
        )

    @property
    def count(self):
        return self.until_locs - self.since_locs

    def format(self, max_author_len, max_count_len, show_base=False):
        bargraph = str()
        if show_base:
            bargraph += '=' * self.since_locs

        if self.count > 0:
            bargraph += Delta._green + '+' * (self.until_locs - self.since_locs) + Delta._normal
        elif self.count < 0:
            bargraph += Delta._red + '-' * (self.since_locs - self.until_locs) + Delta._normal

        return " {author} | {count} {bargraph} ({wtf})".format(
            author=self.author.ljust(max_author_len),
            count=str(self.count).rjust(max_count_len),
            bargraph=bargraph,
            wtf=str(self.since_locs) + '->' + str(self.until_locs),
        )

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

        # TODO Do we still need this?
        self.files = list()

    def process_args(self):
        self.args = self.parser.parse_args()
        if not (self.args.since and self.args.until):
            raise GitError('bad args')

    def populate_trees(self):
        self.trees[self.args.since] = self.runner._populate_tree(self.args.since)
        self.trees[self.args.until] = self.runner._populate_tree(self.args.until)

    def map_blames(self):
        """Prepares the list of blames to tabulate"""

        for repo_path in self.runner.get_delta_files(
                self.args.since, self.args.until
                ):
            self.files.append(repo_path)

            self.blame_queue.append(
                BlameTicket(self.since, repo_path, self.args.since)
            )

            self.blame_queue.append(
                BlameTicket(self.until, repo_path, self.args.until)
            )

        # TODO This should be made parallel
        for blame in self.blame_queue:
            if blame.repo_path in self.trees[blame.rev]:
                blame.exists = True
                self.runner.blame_locs(blame)
            else:
                blame.exists = False

    def _reduce_since_blame(self, deltas, since_blame):
        author, loc_count = since_blame
        until_loc_count = self.until[author] or 0
        # LOC counts are always >=0
        deltas.append(Delta(author, until_loc_count, loc_count))
        return deltas

    def _reduce_until_blame(self, deltas, until_blame):
        author, loc_count = until_blame
        if author not in self.since:
            # We have a new author
            deltas.append(Delta(author, loc_count, 0))
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

    def show_guilt_stats(self):
        # TODO Do something like diffstat's number of files changed, number or
        # insertions and number of deletions
        longest_name = len(max(
            self.loc_deltas,
            key=lambda d: len(d.author)
        ).author)

        longest_delta = len(str(max(
            self.loc_deltas,
            key=lambda d: len(str(d.count))
        ).count))

        for delta in self.loc_deltas:
            print(delta.format(longest_name, longest_delta))

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
            self.show_guilt_stats()
            return 0

if '__main__' == __name__:
    sys.exit(PyGuilt().run())
