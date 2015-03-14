# -*- coding: UTF-8 -*-
# Copyright (c) 2015, Matt Boyer
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     1. Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
# 
#     2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
# 
#     3. Neither the name of the copyright holder nor the names of its
#     contributors may be used to endorse or promote products derived from this
#     software without specific prior written permission.
# 
#     THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#     IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#     THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#     PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
#     CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#     EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#     PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#     PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#     LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#     NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#     SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import io
import sys
from mock import patch, Mock, call
from unittest import TestCase
import test.constants

import guilt

# FIXME Should probably use mock.patch instead
guilt.GitRunner._git_executable = 'nosuchgit'

class DeltaTestCase(TestCase):

    def test_eq(self):
        a = guilt.Delta('Alpha', 4, 0)
        b = guilt.Delta('Beta', 6, 0)
        self.assertFalse(a == b)
        self.assertTrue(a != b)

        b = guilt.Delta('Alpha', 6, 0)
        self.assertFalse(a == b)
        self.assertTrue(a != b)

        b = guilt.Delta('Alpha', 4, 0)
        self.assertTrue(a == b)
        self.assertTrue(a <= b)
        self.assertTrue(a >= b)
        self.assertFalse(a != b)

    def test_comparison(self):
        a = guilt.Delta('Alpha', 4, 0)

        # a > b because a is guiltier than b
        b = guilt.Delta('Beta', 6, 0)

        # Test __lt__ and __le__
        self.assertTrue(a < b)
        self.assertTrue(a <= b)
        self.assertFalse(b < a)
        self.assertFalse(b <= a)

        # Test __gt__ and __ge__
        self.assertFalse(a > b)
        self.assertFalse(a >= b)
        self.assertTrue(b > a)
        self.assertTrue(b >= a)

        # a and b are equally guilty, but a comes before b in a lexicographic
        # sort
        b = guilt.Delta('Beta', 4, 0)

        # Test __lt__ and __le__
        self.assertTrue(a < b)
        self.assertTrue(a <= b)
        self.assertFalse(b < a)
        self.assertFalse(b <= a)

        # Test __gt__ and __ge__
        self.assertFalse(a > b)
        self.assertFalse(a >= b)
        self.assertTrue(b > a)
        self.assertTrue(b >= a)

        b = guilt.Delta('Aardvark', 4, 0)
        self.assertFalse(a < b)
        self.assertFalse(a <= b)

        self.assertTrue(a > b)
        self.assertTrue(a >= b)

    def test_repr(self):
        a = guilt.Delta('Alpha', 0, 4)
        b = guilt.Delta('Beta', 16, 10)
        c = guilt.Delta('Gamma', 8, 8)

        self.assertEquals("<Delta \"Alpha\": 4 (0->4)>", repr(a))
        self.assertEquals("<Delta \"Beta\": -6 (16->10)>", repr(b))
        self.assertEquals("<Delta \"Gamma\": 0 (8->8)>", repr(c))


class ArgTestCase(TestCase):

    def setUp(self):
        # We need to mock up subprocess.Popen so that the 'git' invocation
        # performed when the GitRunner object is instantiated doesn't result in
        # an actual process being forked
        self._popen_patch = patch('guilt.subprocess.Popen')
        self.mocked_popen = self._popen_patch.start()
        self.mocked_popen.return_value = Mock(
            communicate=Mock(return_value=(b'bar', None)),
            returncode=0,
        )

        # Mock stdout.fileno()
        self._stdout_patch = patch('guilt.sys.stdout')
        self.mocked_stdout = self._stdout_patch.start()
        self.mocked_stdout.return_value = Mock(
            fileno=Mock(return_value=1),
        )

        # ...as well as os.isatty
        self._isatty_patch = patch('guilt.os.isatty')
        self.mocked_isatty = self._isatty_patch.start()
        self.mocked_isatty.return_value = False

        self.guilt = guilt.PyGuilt()

    def tearDown(self):
        self._popen_patch.stop()
        self._stdout_patch.stop()
        self._isatty_patch.stop()

    @patch('sys.argv', ['arg0', 'foo'])
    def test_bad_args(self):
        stderr_patch = None
        if 2 == sys.version_info[0]:
            stderr_patch = patch('sys.stderr', new_callable=io.BytesIO)
        elif 3 == sys.version_info[0]:
            stderr_patch = patch('sys.stderr', new_callable=io.StringIO)

        mock_stderr = stderr_patch.start()

        self.assertRaises(guilt.GitError, self.guilt.process_args)

        self.assertEquals(1, self.guilt.run())
        self.assertEquals('Invalid arguments\n', mock_stderr.getvalue())

        stderr_patch.stop()

    @patch('sys.argv', ['arg0', '--help'])
    def test_help(self):
        self.assertRaises(SystemExit, self.guilt.process_args)

        self.assertRaises(SystemExit, self.guilt.run)


class GitRunnerTestCase(TestCase):

    def setUp(self):
        # We need to mock up subprocess.Popen so that the 'git' invocation
        # performed when the GitRunner object is instantiated doesn't result in
        # an actual process being forked
        self._popen_patch = patch('guilt.subprocess.Popen')
        self.mocked_popen = self._popen_patch.start()
        self.mocked_popen.return_value = Mock(
            communicate=Mock(return_value=(b'bar', None)),
            returncode=0,
        )

        self.runner = guilt.GitRunner()
        self._popen_patch.stop()

    def tearDown(self):
        pass

    @patch('guilt.subprocess.Popen')
    def test_run_git_cwd(self, mock_process):
        mock_process.return_value.communicate = Mock(return_value=(b'bar', None))
        mock_process.return_value.returncode = 0
        mock_process.return_value.wait = \
                Mock(return_value=None)

        self.runner._git_toplevel = None
        self.runner.run_git(['foo'])

        mock_process.assert_called_once_with(['nosuchgit', 'foo'], stderr=-1, stdout=-1)
        mock_process.reset_mock()

        self.runner._git_toplevel = '/my/top/level/git/directory'
        self.runner.run_git(['foo'])
        mock_process.assert_called_once_with(['nosuchgit', 'foo'], cwd='/my/top/level/git/directory', stderr=-1, stdout=-1)

    @patch('guilt.subprocess.Popen')
    def test_run_git_no_output_error(self, mock_process):
        mock_process.return_value.returncode = 0
        mock_process.return_value.communicate = \
                Mock(return_value=(b'', b'Some error'))

        self.assertRaises(guilt.GitError, self.runner.run_git, ['log'])

    @patch('guilt.subprocess.Popen')
    def test_run_git_no_output_no_error(self, mock_process):
        mock_process.return_value.returncode = 0
        mock_process.return_value.communicate = \
                Mock(return_value=(b'', b''))

        self.assertRaises(ValueError, self.runner.run_git, ['log'])

    @patch('guilt.subprocess.Popen')
    def test_run_git_non_zerp(self, mock_process):
        mock_process.return_value.returncode = 1
        mock_process.return_value.communicate = \
                Mock(return_value=(b'Foo', b'Bar'))

        self.assertRaises(guilt.GitError, self.runner.run_git, ['log'])

    @patch('guilt.subprocess.Popen')
    def test_run_git_exception(self, mock_process):
        mock_process.return_value.communicate = Mock(side_effect=OSError)

        self.assertRaises(guilt.GitError, self.runner.run_git, ['log'])

    @patch('guilt.subprocess.Popen')
    def test_run_git_stderr(self, mock_process):
        mock_process.return_value.communicate = Mock(return_value=(b'', b'error'))

        self.assertRaises(guilt.GitError, self.runner.run_git, ['log'])

    @patch('guilt.subprocess.Popen')
    def test_run_git(self, mock_process):
        mock_process.return_value.returncode = 0
        mock_process.return_value.wait = \
                Mock(return_value=None)
        mock_process.return_value.communicate = \
                Mock(return_value=(b'a\nb\nc', None))

        self.assertEquals(['a', 'b', 'c'], self.runner.run_git(['log']))

    @patch('guilt.subprocess.Popen')
    def test_get_delta_files(self, mock_process):
        # The type returned by Popen.communicate() is version-specific
        if 2 == sys.version_info[0]:
            # Python2's str type is byte-based
            git_output='1	2	foo.c\x003	7	foo.h\x00-	-	binary\x00'
        elif 3 == sys.version_info[0]:
            git_output=bytes('1	2	foo.c\x003	7	foo.h\x00-	-	binary\x00', encoding='utf_8')

        mock_process.return_value.returncode = 0
        mock_process.return_value.communicate = \
            Mock(
                return_value=(git_output, None)
            )

        self.assertEquals(
            (set(['foo.c', 'foo.h']), set(['binary'])),
            self.runner.get_delta_files('HEAD~1', 'HEAD')
        )

    @patch('guilt.subprocess.Popen')
    def test_get_delta_no_files(self, mock_process):
        # The type returned by Popen.communicate() is version-specific
        if 2 == sys.version_info[0]:
            # Python2's str type is byte-based
            git_output = '\x00'
        elif 3 == sys.version_info[0]:
            git_output = bytes('\x00', encoding='utf_8')

        mock_process.return_value.returncode = 0
        mock_process.return_value.communicate = \
            Mock(
                return_value=(git_output, None)
            )

        self.assertRaises(ValueError, self.runner.get_delta_files, 'HEAD~1', 'HEAD')

    @patch('guilt.GitRunner.run_git')
    def test_blame_locs(self, mock_run_git):
        mock_run_git.return_value = test.constants.blame_author_names.splitlines()

        #blame = Mock()
        #blame.repo_path = 'src/foo.c'
        #blame.bucket = {'Foo Bar': 0, 'Tim Pettersen': 0}
        runner = guilt.GitRunner()
        bucket = {'Foo Bar': 0, 'Tim Pettersen': 0}
        blame = guilt.TextBlameTicket(runner, bucket, 'src/foo.c', 'HEAD')

        blame.process()
        self.assertEquals(
            {'Foo Bar': 2, 'Tim Pettersen': 3},
            blame.bucket
        )

    @patch('guilt.GitRunner.run_git')
    def test_blame_locs_file_missing(self, mock_run_git):
        # We need to mock out the first call to run_git
        mock_run_git.return_value = '/my/arbitrary/git/root'
        runner = guilt.GitRunner()

        bucket = {'Foo Bar': 0, 'Tim Pettersen': 0}
        blame = guilt.TextBlameTicket(runner, bucket, 'src/foo.c', 'HEAD')

        mock_run_git.side_effect = guilt.GitError("'git blame arbitrary path failed with:\nfatal: no such path 'src/foo.c' in HEAD")

        self.assertEquals(None, blame.process())
        # THe bucket is unchanged
        self.assertEquals(
            {'Foo Bar': 0, 'Tim Pettersen': 0},
            blame.bucket
        )

    @patch('guilt.subprocess.Popen')
    def test_get_git_root_exception(self, mock_process):
        mock_process.return_value.communicate = Mock(side_effect=OSError)


        stderr_patch = None
        if 2 == sys.version_info[0]:
            stderr_patch = patch('sys.stderr', new_callable=io.BytesIO)
        elif 3 == sys.version_info[0]:
            stderr_patch = patch('sys.stderr', new_callable=io.StringIO)

        mock_stderr = stderr_patch.start()

        self.assertRaises(SystemExit, guilt.GitRunner)
        self.assertEquals("Couldn't run 'git rev-parse --show-toplevel':\n\n", mock_stderr.getvalue())

        stderr_patch.stop()


class GuiltTestCase(TestCase):

    def setUp(self):
        # We need to mock up subprocess.Popen so that the 'git' invocation
        # performed when the GitRunner object is instantiated doesn't result in
        # an actual process being forked
        self._popen_patch = patch('guilt.subprocess.Popen')
        self.mocked_popen = self._popen_patch.start()
        self.mocked_popen.return_value = Mock(
            communicate=Mock(return_value=(b'bar', None)),
            returncode=0,
        )

        self._stdout_patch = patch('guilt.sys.stdout')
        self.mocked_stdout = self._stdout_patch.start()
        self.mocked_stdout.return_value = Mock(
            fileno=Mock(return_value=1),
        )

        self._isatty_patch = patch('guilt.os.isatty')
        self.mocked_isatty = self._isatty_patch.start()
        self.mocked_isatty.return_value = False

        self.guilt = guilt.PyGuilt()

    def tearDown(self):
        self._popen_patch.stop()
        self._stdout_patch.stop()
        self._isatty_patch.stop()

    @patch('guilt.GitRunner.run_git')
    def test_populate_trees(self, mock_run_git):
        self.guilt.args = Mock(since='HEAD~4', until='HEAD~1')
        mock_run_git.return_value = []

        self.guilt.populate_trees()
        self.assertEquals(
            [
                call(['ls-tree', '-r', '--', 'HEAD~4']),
                call(['ls-tree', '-r', '--', 'HEAD~1']),
            ],
            mock_run_git.mock_calls
        )

    @patch('guilt.GitRunner.get_delta_files')
    def test_map_blames(self, mock_get_delta):
        # We need to mock out the runner
        mock_runner = Mock()

        mock_get_delta.return_value = set(['foo.c', 'foo.h']), set([])
        self.guilt.args = Mock(since='HEAD~4', until='HEAD~1')

        self.guilt.trees['HEAD~4'] = ['foo.c', 'foo.h']
        self.guilt.trees['HEAD~1'] = ['foo.c', 'foo.h']

        self.guilt.map_blames()
        self.assertEquals(4, len(self.guilt.blame_jobs))
        self.assertEquals(
                [
                    guilt.TextBlameTicket(mock_runner, self.guilt.loc_ownership_since, 'foo.c', 'HEAD~4'),
                    guilt.TextBlameTicket(mock_runner, self.guilt.loc_ownership_until, 'foo.c', 'HEAD~1'),
                    guilt.TextBlameTicket(mock_runner, self.guilt.loc_ownership_since, 'foo.h', 'HEAD~4'),
                    guilt.TextBlameTicket(mock_runner, self.guilt.loc_ownership_until, 'foo.h', 'HEAD~1'),
                ],
                self.guilt.blame_jobs
            )

    def test_reduce_locs(self):
        self.guilt.loc_ownership_since = {'Alice': 5, 'Bob': 3, 'Carol': 4}
        self.guilt.loc_ownership_until = {'Alice': 6, 'Bob': 6, 'Carol': 2, 'Dave': 1, 'Ellen': 2}

        expected_deltas = [
                guilt.Delta(until=6, since=3, author='Bob'),
                guilt.Delta(until=2, since=0, author='Ellen'),
                guilt.Delta(until=6, since=5, author='Alice'),
                guilt.Delta(until=1, since=0, author='Dave'),
                guilt.Delta(until=2, since=4, author='Carol'),
                ]

        self.guilt.reduce_blames()

        self.assertEquals(
            expected_deltas,
            self.guilt.loc_deltas
        )

    @patch('guilt.GitRunner.get_delta_files')
    def test_file_not_in_since_rev(self, mock_get_files, ):
        mock_get_files.return_value = (set(['in_since_and_until', 'not_in_since']), set([]))

        # Mock up arg namespace
        self.guilt.args = Mock()
        self.guilt.args.since = 'since'
        self.guilt.args.until = 'until'

        self.guilt.trees['since'] = ['in_since_and_until']
        self.guilt.trees['until'] = ['in_since_and_until', 'not_in_since']

        def mock_blame_logic(blame):
            if 'not_in_since' == blame.repo_path:
                if 'since' == blame.rev:
                    blame.exists = False
                elif 'until' == blame.rev:
                    blame.exists = True
                    blame.bucket['Alice'] += 20
                    blame.bucket['Bob'] += 5
            elif 'in_since_and_until' == blame.repo_path:
                blame.exists = True
                if 'since' == blame.rev:
                    blame.bucket['Alice'] += 12
                    blame.bucket['Bob'] += 8
                    blame.bucket['Dave'] += 4
                elif 'until' == blame.rev:
                    blame.exists = True
                    blame.bucket['Alice'] += 18
                    blame.bucket['Bob'] += 2
                    blame.bucket['Carol'] += 2

        # FIXME This monkey patching is ugly and should be handled through Mock
        old_process = guilt.TextBlameTicket.process
        try:
            guilt.TextBlameTicket.process = mock_blame_logic

            self.guilt.map_blames()
            self.assertEquals({'Alice': 12, 'Bob': 8, 'Dave': 4}, self.guilt.loc_ownership_since)
            self.assertEquals({'Alice': 38, 'Bob': 7, 'Carol': 2}, self.guilt.loc_ownership_until)

            self.guilt.reduce_blames()

            # Alice's share of the collective guilt has increased from 12 LOCs in
            # the since rev to 38 LOCs
            # Bob's share of the collective guilt has decreased from 8 to 7 LOCs
            # (spread across different files)
            # Carol's share of the collective guilt has increased from 0 in the
            # since rev to 2 LOCs
            expected_guilt = [guilt.Delta('Alice', 12, 38), guilt.Delta('Bob', 8, 7), guilt.Delta('Carol', 0, 2), guilt.Delta('Dave', 4, 0)]
            expected_guilt.sort()

            self.assertEquals(expected_guilt, self.guilt.loc_deltas)
        finally:
            guilt.TextBlameTicket.process = old_process

    @patch('guilt.GitRunner.get_delta_files')
    def test_file_not_in_until_rev(self, mock_get_files):
        mock_get_files.return_value = (set(['in_since_and_until', 'not_in_until']), set([]))

        # Mock up arg namespace
        self.guilt.args = Mock()
        self.guilt.args.since = 'since'
        self.guilt.args.until = 'until'

        self.guilt.trees['since'] = ['in_since_and_until', 'not_in_until']
        self.guilt.trees['until'] = ['in_since_and_until']

        def mock_blame_logic(blame):
            if 'not_in_until' == blame.repo_path:
                if 'since' == blame.rev:
                    blame.exists = True
                    blame.bucket['Alice'] += 20
                    blame.bucket['Bob'] += 5
                elif 'until' == blame.rev:
                    blame.exists = False

            elif 'in_since_and_until' == blame.repo_path:
                blame.exists = True
                if 'since' == blame.rev:
                    blame.bucket['Alice'] += 12
                elif 'until' == blame.rev:
                    blame.exists = True
                    blame.bucket['Alice'] += 18
                    blame.bucket['Carol'] += 2

        # FIXME This monkey patching is ugly and should be handled through Mock
        old_process = guilt.TextBlameTicket.process
        try:
            guilt.TextBlameTicket.process = mock_blame_logic

            self.guilt.map_blames()
            self.assertEquals({'Alice': 32, 'Bob': 5}, self.guilt.loc_ownership_since)
            self.assertEquals({'Alice': 18, 'Carol': 2}, self.guilt.loc_ownership_until)

            self.guilt.reduce_blames()

            # Alice's share of the collective guilt has decreased from 32 to 18
            # LOCs
            # Bob's share of the collective guilt has been wiped clean!
            # Carol's share has increased from nothing to 2
            expected_guilt = [
                    guilt.Delta('Alice', 32, 18),
                    guilt.Delta('Bob', 5, 0),
                    guilt.Delta('Carol', 0, 2)
                ]
            expected_guilt.sort()

            self.assertEquals(expected_guilt, self.guilt.loc_deltas)
        finally:
            guilt.TextBlameTicket.process = old_process

    # Many more testcases are required!!
    @patch('guilt.PyGuilt.populate_trees')
    @patch('guilt.Formatter.show_guilt_stats')
    @patch('guilt.PyGuilt.reduce_blames')
    @patch('guilt.PyGuilt.map_blames')
    @patch('guilt.PyGuilt.process_args')
    @patch('sys.stdout', new_callable=io.BytesIO)
    def test_show_run(self, mock_stdout, mock_process_args, mock_map, mock_reduce, mock_show, mock_pop_trees):

        self.assertEquals(0, self.guilt.run())
        mock_process_args.assert_called_once_with()
        mock_pop_trees.assert_called_once_with()
        mock_map.assert_called_once_with()
        mock_reduce.assert_called_once_with()

        self.assertEquals(2, len(mock_show.mock_calls))


class FormatterTestCase(TestCase):

    def setUp(self):
        # Mock stdout.fileno()
        self._stdout_patch = patch('guilt.sys.stdout')
        self.mocked_stdout = self._stdout_patch.start()
        self.mocked_stdout.return_value = Mock(
            fileno=Mock(return_value=1),
        )

        # Mock os.isatty
        self._isatty_patch = patch('guilt.os.isatty')
        self.mocked_isatty = self._isatty_patch.start()
        self.mocked_isatty.return_value = False

        self.formatter = guilt.Formatter([])

    def tearDown(self):
        self._isatty_patch.stop()

    def test_get_width_not_tty(self):
        self.assertEquals(80, self.formatter._get_tty_width())

    @patch('guilt.fcntl.ioctl')
    def test_get_width_tty(self, mocked_ioctl):
        self._isatty_patch.stop()

        mocked_isatty = self._isatty_patch.start()
        mocked_isatty.return_value = True
        del self.formatter

        mocked_ioctl.return_value = b'\x00\x00\x6e\x00\x00\x00\x00\x00'
        self.formatter = guilt.Formatter([])
        self.assertEquals(110, self.formatter._get_tty_width())
        del self.formatter

        # For whatever reason, we get a length of 0 - expect 80
        mocked_ioctl.return_value = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        self.formatter = guilt.Formatter([])
        self.assertEquals(80, self.formatter._get_tty_width())
        del self.formatter

        del mocked_ioctl.return_value
        mocked_ioctl.side_effect = IOError
        self.formatter = guilt.Formatter([])
        self.assertEquals(80, self.formatter._get_tty_width())
        del self.formatter

    def test_show_guilt(self):
        if 2 == sys.version_info[0]:
            stdout_patch = patch('sys.stdout', new_callable=io.BytesIO)
        elif 3 == sys.version_info[0]:
            stdout_patch = patch('sys.stdout', new_callable=io.StringIO)

        mock_stdout = stdout_patch.start()


        self.formatter.deltas.append(guilt.Delta(u'short', 30, 45))
        self.formatter.deltas.append(guilt.Delta(u'Very Long Name', 10, 7))

        self.formatter.show_guilt_stats()
        self.assertEquals(''' short          | 15 +++++++++++++++
 Very Long Name | -3 ---
''',
            mock_stdout.getvalue()
        )
        stdout_patch.stop()
