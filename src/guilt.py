"""
Port of git-guilt to Python
"""

import re
import argparse
import subprocess
import collections
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
        self._get_git_root()

    def _get_git_root(self):
        try:
            top_level_dir = self._run_git(GitRunner._toplevel_args)
        except Exception as e:
            # Do something appropriate
            raise e
        else:
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

    def process_args(self):
        self.args = self.parser.parse_args()
        if not (self.args.since and self.args.until):
            raise GitError('bad args')

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
        print("Blame queue", self.blame_queue)
        for blame in self.blame_queue:
            self.runner.blame_locs(blame)

    def _reduce_since_blame(self, author, loc_count):
        until_loc_count = self.until[author] or 0
        loc_delta = until_loc_count - loc_count
        if loc_delta != 0:
            self.loc_deltas.append({'author': author, 'delta': loc_delta})

    def _reduce_until_blame(self, author, loc_count):
        if author not in self.since:
            # We have a new author
            self.loc_deltas.append({'author': author, 'delta': loc_count})

    def reduce_blames(self):
        print('Since', self.since)
        print('Until', self.until)

        for author, loc_count in self.since.items():
            self._reduce_since_blame(author, loc_count)

        for author, loc_count in self.until.items():
            self._reduce_until_blame(author, loc_count)

        print(self.loc_deltas)

    def run(self):
        try:
            self.process_args()
        except GitError as arg_ex:
            sys.stderr.write(str(arg_ex))
            return 1
        else:
            self.map_blames()
            self.reduce_blames()
            return 0

if '__main__' == __name__:
    sys.exit(PyGuilt().run())
