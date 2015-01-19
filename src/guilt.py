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

    def blame_locs(self, blame):
        blame_args = ['blame', '--', blame.repo_path]
        if blame.rev:
            blame_args.append(blame.rev)
        lines = self._run_git(blame_args)
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

    def __repr__(self):
        return "Will blame \"{0}\" for rev {1} into bucket {2}".format(
            self.repo_path,
            self.rev,
            self.bucket
        )

    def __eq__(self, blame):
        return (self.bucket == blame.bucket) \
            and (self.repo_path == blame.repo_path) \
            and (self.bucket == blame.bucket)


class Delta(object):

    def __init__(self, author, count):
        self.author = author
        self.count = count

    def __repr__(self):
        return "<Delta \"{author}\": {count}>".format(
            author=self.author,
            count=self.count
        )

    def __str__(self):
        display_count = str(self.count)

        pluses = str()
        if self.count < 0:
            pluses = '-' * -self.count
        elif self.count > 0:
            pluses = '+' * self.count

        return "{author} [{count}]: {pluses}".format(
            author=self.author,
            count=display_count,
            pluses=pluses,
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
        self.files = list()

    def process_args(self):
        self.args = self.parser.parse_args()
        if not (self.args.since and self.args.until):
            raise GitError('bad args')

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
            self.runner.blame_locs(blame)

    def _reduce_since_blame(self, deltas, foo):
        author, loc_count = foo
        until_loc_count = self.until[author] or 0
        loc_delta = until_loc_count - loc_count
        if loc_delta != 0:
            deltas.append(Delta(author, loc_delta))

        return deltas

    def _reduce_until_blame(self, deltas, foo):
        author, loc_count = foo
        if author not in self.since:
            # We have a new author
            deltas.append(Delta(author, loc_count))
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
        for delta in self.loc_deltas:
            print(str(delta))
        print("{0} files changed".format(len(self.files)))

    def run(self):
        try:
            self.process_args()
        except GitError as ex:
            sys.stderr.write(str(ex))
            return 1
        else:
            self.map_blames()
            self.reduce_blames()
            self.show_guilt_stats()
            return 0

if '__main__' == __name__:
    sys.exit(PyGuilt().run())
