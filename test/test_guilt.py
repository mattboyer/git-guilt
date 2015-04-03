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

import git_guilt.guilt as guilt_module

# FIXME Should probably use mock.patch instead
guilt_module.GitRunner._git_executable = 'nosuchgit'

class DeltaTestCase(TestCase):

    def test_eq(self):
        a = guilt_module.Delta('Alpha', 4, 0)
        b = guilt_module.Delta('Beta', 6, 0)
        self.assertFalse(a == b)
        self.assertTrue(a != b)

        b = guilt_module.Delta('Alpha', 6, 0)
        self.assertFalse(a == b)
        self.assertTrue(a != b)

        b = guilt_module.Delta('Alpha', 4, 0)
        self.assertTrue(a == b)
        self.assertTrue(a <= b)
        self.assertTrue(a >= b)
        self.assertFalse(a != b)

    def test_comparison(self):
        a = guilt_module.Delta('Alpha', 4, 0)

        # a > b because a is guilt_moduleier than b
        b = guilt_module.Delta('Beta', 6, 0)

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

        # a and b are equally guilt_moduley, but a comes before b in a lexicographic
        # sort
        b = guilt_module.Delta('Beta', 4, 0)

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

        b = guilt_module.Delta('Aardvark', 4, 0)
        self.assertFalse(a < b)
        self.assertFalse(a <= b)

        self.assertTrue(a > b)
        self.assertTrue(a >= b)

    def test_repr(self):
        a = guilt_module.Delta('Alpha', 0, 4)
        b = guilt_module.Delta('Beta', 16, 10)
        c = guilt_module.Delta('Gamma', 8, 8)

        self.assertEquals("<Delta \"Alpha\": 4 (0->4)>", repr(a))
        self.assertEquals("<Delta \"Beta\": -6 (16->10)>", repr(b))
        self.assertEquals("<Delta \"Gamma\": 0 (8->8)>", repr(c))

class BinaryDeltaTestCase(TestCase):

    def test_eq(self):
        a = guilt_module.BinaryDelta('Alpha', 4, 0)
        b = guilt_module.BinaryDelta('Beta', 6, 0)
        self.assertFalse(a == b)
        self.assertTrue(a != b)

        b = guilt_module.BinaryDelta('Alpha', 6, 0)
        self.assertFalse(a == b)
        self.assertTrue(a != b)

        b = guilt_module.BinaryDelta('Alpha', 4, 0)
        self.assertTrue(a == b)
        self.assertTrue(a <= b)
        self.assertTrue(a >= b)
        self.assertFalse(a != b)

    def test_comparison(self):
        a = guilt_module.BinaryDelta('Alpha', 4, 0)

        # a > b because a is guilt_moduleier than b
        b = guilt_module.BinaryDelta('Beta', 6, 0)

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

        # a and b are equally guilt_moduley, but a comes before b in a lexicographic
        # sort
        b = guilt_module.BinaryDelta('Beta', 4, 0)

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

        b = guilt_module.BinaryDelta('Aardvark', 4, 0)
        self.assertFalse(a < b)
        self.assertFalse(a <= b)

        self.assertTrue(a > b)
        self.assertTrue(a >= b)

    def test_repr(self):
        a = guilt_module.BinaryDelta('Alpha', 0, 4)
        b = guilt_module.BinaryDelta('Beta', 16, 10)
        c = guilt_module.BinaryDelta('Gamma', 8, 8)

        self.assertEquals("<BinaryDelta \"Alpha\": 4 (0->4)>", repr(a))
        self.assertEquals("<BinaryDelta \"Beta\": -6 (16->10)>", repr(b))
        self.assertEquals("<BinaryDelta \"Gamma\": 0 (8->8)>", repr(c))

class ArgTestCase(TestCase):

    def setUp(self):
        # We need to mock up subprocess.Popen so that the 'git' invocation
        # performed when the GitRunner object is instantiated doesn't result in
        # an actual process being forked
        self._popen_patch = patch('git_guilt.guilt.subprocess.Popen')
        self.mocked_popen = self._popen_patch.start()
        self.mocked_popen.return_value = Mock(
            communicate=Mock(return_value=(b'git version 2.3.4', None)),
            returncode=0,
        )

        # Mock stdout.fileno()
        self._stdout_patch = patch('git_guilt.guilt.sys.stdout')
        self.mocked_stdout = self._stdout_patch.start()
        self.mocked_stdout.return_value = Mock(
            fileno=Mock(return_value=1),
        )

        # ...as well as os.isatty
        self._isatty_patch = patch('git_guilt.guilt.os.isatty')
        self.mocked_isatty = self._isatty_patch.start()
        self.mocked_isatty.return_value = False

        self.guilt = guilt_module.PyGuilt()

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

        self.assertRaises(guilt_module.GitError, self.guilt.process_args)

        self.assertEquals(1, self.guilt.run())
        self.assertEquals('Invalid arguments\n', mock_stderr.getvalue())

        stderr_patch.stop()

    @patch('sys.argv', ['arg0', '--help'])
    def test_help(self):
        self.assertRaises(SystemExit, self.guilt.process_args)

        self.assertRaises(SystemExit, self.guilt.run)


class GitRunnerTestCase(TestCase):

    def setUp(self):
        initial_git_results = [
                (b'git version 1.0.0\n', None),
                (b'/my/arbitrary/path\n', None)
            ]

        def patched_popen(*args):
            try:
                output = initial_git_results.pop()
            except IndexError:
                output = (b'\n', None)
            finally:
                return output

        # We need to mock up subprocess.Popen so that the 'git' invocation
        # performed when the GitRunner object is instantiated doesn't result in
        # an actual process being forked
        self._popen_patch = patch('git_guilt.guilt.subprocess.Popen')
        self.mocked_popen = self._popen_patch.start()
        self.mocked_popen.return_value = Mock(
            communicate=Mock(side_effect=patched_popen),
            returncode=0,
        )

        self.runner = guilt_module.GitRunner()
        self._popen_patch.stop()

    def tearDown(self):
        pass

    @patch('git_guilt.guilt.subprocess.Popen')
    def test_version_retrieval(self, mock_process):
        mock_process.return_value.communicate = Mock(
            return_value=(b'git version 1.1.1', None)
        )
        mock_process.return_value.returncode = 0
        mock_process.return_value.wait = \
                Mock(return_value=None)

        version_tuple = self.runner._get_git_version()

        mock_process.assert_called_once_with(
            ['nosuchgit', '--version'],
            cwd='/my/arbitrary/path',
            stderr=-1,
            stdout=-1
        )
        mock_process.reset_mock()

        self.assertEquals((1,1,1), version_tuple)

        # Git gave us something that isn't a version string
        mock_process.return_value.communicate = Mock(
            return_value=(b'git fdsfyasdifoy', None)
        )
        self.assertRaises(
            guilt_module.GitError,
            self.runner._get_git_version
        )
        mock_process.reset_mock()

        # Git gave us a malformed version
        mock_process.return_value.communicate = Mock(
            return_value=(b'git version X.Y.Z', None)
        )
        self.assertRaises(
            guilt_module.GitError,
            self.runner._get_git_version
        )
        mock_process.reset_mock()

    def test_version_comparison(self):
        self.assertEquals((1, 0, 0), self.runner.version)

        self.runner.version = (1, 7, 1)
        self.assertFalse(self.runner.git_supports_binary_diff())

        self.runner.version = (1, 7, 2)
        self.assertTrue(self.runner.git_supports_binary_diff())

        self.runner.version = (2, 3, 4)
        self.assertTrue(self.runner.git_supports_binary_diff())

    @patch('git_guilt.guilt.subprocess.Popen')
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

    @patch('git_guilt.guilt.subprocess.Popen')
    def test_run_git_no_output_error(self, mock_process):
        mock_process.return_value.returncode = 0
        mock_process.return_value.communicate = \
                Mock(return_value=(b'', b'Some error'))

        self.assertRaises(guilt_module.GitError, self.runner.run_git, ['log'])

    @patch('git_guilt.guilt.subprocess.Popen')
    def test_run_git_no_output_no_error(self, mock_process):
        mock_process.return_value.returncode = 0
        mock_process.return_value.communicate = \
                Mock(return_value=(b'', b''))

        self.assertRaises(ValueError, self.runner.run_git, ['log'])

    @patch('git_guilt.guilt.subprocess.Popen')
    def test_run_git_non_zerp(self, mock_process):
        mock_process.return_value.returncode = 1
        mock_process.return_value.communicate = \
                Mock(return_value=(b'Foo', b'Bar'))

        self.assertRaises(guilt_module.GitError, self.runner.run_git, ['log'])

    @patch('git_guilt.guilt.subprocess.Popen')
    def test_run_git_exception(self, mock_process):
        mock_process.return_value.communicate = Mock(side_effect=OSError)

        self.assertRaises(guilt_module.GitError, self.runner.run_git, ['log'])

    @patch('git_guilt.guilt.subprocess.Popen')
    def test_run_git_stderr(self, mock_process):
        mock_process.return_value.communicate = Mock(return_value=(b'', b'error'))

        self.assertRaises(guilt_module.GitError, self.runner.run_git, ['log'])

    @patch('git_guilt.guilt.subprocess.Popen')
    def test_run_git(self, mock_process):
        mock_process.return_value.returncode = 0
        mock_process.return_value.wait = \
                Mock(return_value=None)
        mock_process.return_value.communicate = \
                Mock(return_value=(b'a\nb\nc', None))

        self.assertEquals(['a', 'b', 'c'], self.runner.run_git(['log']))

    @patch('git_guilt.guilt.subprocess.Popen')
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

    @patch('git_guilt.guilt.subprocess.Popen')
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

    @patch('git_guilt.guilt.subprocess.Popen')
    def test_get_git_root_exception(self, mock_process):
        mock_process.return_value.communicate = Mock(side_effect=OSError)


        stderr_patch = None
        if 2 == sys.version_info[0]:
            stderr_patch = patch('sys.stderr', new_callable=io.BytesIO)
        elif 3 == sys.version_info[0]:
            stderr_patch = patch('sys.stderr', new_callable=io.StringIO)

        mock_stderr = stderr_patch.start()

        self.assertRaises(SystemExit, guilt_module.PyGuilt)
        self.assertEquals("Could not initialise GitRunner - please run from a Git repository.\n", mock_stderr.getvalue())

        stderr_patch.stop()

    @patch('git_guilt.guilt.subprocess.Popen')
    def test_populate_rev_tree(self, mock_process):
        ls_tree_output='''
100644 blob f5231b962039460131a1bd380a3797a24c228801	foo.c
160000 commit b6633ac3fc3177b8d293c2e6ab2f5e576ee70977	git_test_repo
100644 blob 8c7bb63741d85724dd00d3732b636042456f3398	bar.h
        '''.strip()

        # The type returned by Popen.communicate() is version-specific
        if 2 == sys.version_info[0]:
            # Python2's str type is byte-based
            git_output=ls_tree_output
        elif 3 == sys.version_info[0]:
            git_output=bytes(ls_tree_output, encoding='utf_8')

        mock_process.return_value.returncode = 0
        mock_process.return_value.communicate = \
            Mock(
                return_value=(git_output, None)
            )

        self.assertEquals(
            set(['foo.c', 'bar.h']),
            self.runner.populate_tree('HEAD')
        )

class TextBlameTests(TestCase):

    def setUp(self):
        initial_git_results = [
                (b'git version 1.0.0\n', None),
                (b'/my/arbitrary/path\n', None)
            ]

        def patched_popen(*args):
            try:
                output = initial_git_results.pop()
            except IndexError:
                output = (b'\n', None)
            finally:
                return output

        # We need to mock up subprocess.Popen so that the 'git' invocation
        # performed when the GitRunner object is instantiated doesn't result in
        # an actual process being forked
        self._popen_patch = patch('git_guilt.guilt.subprocess.Popen')
        self.mocked_popen = self._popen_patch.start()
        self.mocked_popen.return_value = Mock(
            communicate=Mock(side_effect=patched_popen),
            returncode=0,
        )

        self.runner = guilt_module.GitRunner()
        self._popen_patch.stop()

        self.bucket = {'Foo Bar': 0, 'Tim Pettersen': 0}
        self.ver_file = guilt_module.VersionedFile('src/foo.c', 'HEAD')

    def tearDown(self):
        pass

    def test_text_blame_repr(self):
        bucket = {'Foo Bar': 0, 'Tim Pettersen': 0}
        blame = guilt_module.TextBlameTicket(self.runner, bucket, self.ver_file, Mock())
        self.assertEquals(
            '<TextBlame HEAD:"src/foo.c">',
            repr(blame)
        )

    @patch('git_guilt.guilt.GitRunner.run_git')
    def test_blame_locs(self, mock_run_git):
        mock_run_git.return_value = test.constants.blame_author_names.splitlines()

        blame = guilt_module.TextBlameTicket(self.runner, self.bucket, self.ver_file, Mock())

        blame.process()
        self.assertEquals(
            {'Foo Bar': 2, 'Tim Pettersen': 3},
            blame.bucket
        )

    @patch('git_guilt.guilt.GitRunner.run_git')
    def test_blame_locs_file_missing(self, mock_run_git):
        mock_run_git.side_effect = guilt_module.GitError("'git blame arbitrary path failed with:\nfatal: no such path 'src/foo.c' in HEAD")

        blame = guilt_module.TextBlameTicket(self.runner, self.bucket, self.ver_file, Mock())

        self.assertEquals(None, blame.process())
        # The bucket is unchanged
        self.assertEquals(
            {'Foo Bar': 0, 'Tim Pettersen': 0},
            blame.bucket
        )

    @patch('git_guilt.guilt.GitRunner.run_git')
    def test_blame_locs_exception(self, mock_run_git):
        mock_run_git.side_effect = guilt_module.GitError

        blame = guilt_module.TextBlameTicket(self.runner, self.bucket, self.ver_file, Mock())

        self.assertRaises(guilt_module.GitError, blame.process)

    @patch('git_guilt.guilt.GitRunner.run_git')
    def test_blame_locs_empty_file(self, mock_run_git):
        mock_run_git.side_effect = ValueError('No output')

        blame = guilt_module.TextBlameTicket(self.runner, self.bucket, self.ver_file, Mock())
        self.assertEquals(None, blame.process())

        # The bucket is unchanged
        self.assertEquals(
            {'Foo Bar': 0, 'Tim Pettersen': 0},
            blame.bucket
        )


class BinaryBlameTests(TestCase):

    def setUp(self):
        initial_git_results = [
                (b'git version 1.0.0\n', None),
                (b'/my/arbitrary/path\n', None)
            ]

        def patched_popen(*args):
            try:
                output = initial_git_results.pop()
            except IndexError:
                output = (b'\n', None)
            finally:
                return output

        # We need to mock up subprocess.Popen so that the 'git' invocation
        # performed when the GitRunner object is instantiated doesn't result in
        # an actual process being forked
        self._popen_patch = patch('git_guilt.guilt.subprocess.Popen')
        self.mocked_popen = self._popen_patch.start()
        self.mocked_popen.return_value = Mock(
            communicate=Mock(side_effect=patched_popen),
            returncode=0,
        )

        self.runner = guilt_module.GitRunner()
        self.bucket = {'Foo Bar': 0, 'Tim Pettersen': 0}
        self.ver_file = guilt_module.VersionedFile('bin/a.out', 'HEAD')
        self._popen_patch.stop()

    def tearDown(self):
        pass

    def test_bin_blame_repr(self):
        bucket = {'Foo Bar': 0, 'Tim Pettersen': 0}
        blame = guilt_module.BinaryBlameTicket(self.runner, bucket, self.ver_file, Mock())
        self.assertEquals(
            '<BinaryBlame HEAD:"bin/a.out">',
            repr(blame)
        )

    @patch('git_guilt.guilt.GitRunner.run_git')
    def test_blame_bytes(self, mock_run_git):
        mock_run_git.return_value = test.constants.blame_author_names.splitlines()

        blame = guilt_module.BinaryBlameTicket(self.runner, self.bucket, self.ver_file, Mock())

        blame.process()
        self.assertEquals(
            {'Foo Bar': 2, 'Tim Pettersen': 3},
            blame.bucket
        )

    @patch('git_guilt.guilt.GitRunner.run_git')
    def test_blame_bytes_file_missing(self, mock_run_git):
        mock_run_git.side_effect = guilt_module.GitError("'git blame arbitrary path failed with:\nfatal: no such path 'src/foo.c' in HEAD")

        blame = guilt_module.BinaryBlameTicket(self.runner, self.bucket, self.ver_file, Mock())

        self.assertEquals(None, blame.process())
        # The bucket is unchanged
        self.assertEquals(
            {'Foo Bar': 0, 'Tim Pettersen': 0},
            blame.bucket
        )

    @patch('git_guilt.guilt.GitRunner.run_git')
    def test_blame_bytes_locs_exception(self, mock_run_git):
        mock_run_git.side_effect = guilt_module.GitError

        blame = guilt_module.BinaryBlameTicket(self.runner, self.bucket, self.ver_file, Mock())

        self.assertRaises(guilt_module.GitError, blame.process)

    @patch('git_guilt.guilt.GitRunner.run_git')
    def test_blame_bytes_empty_file(self, mock_run_git):
        mock_run_git.side_effect = ValueError('No output')

        blame = guilt_module.BinaryBlameTicket(self.runner, self.bucket, self.ver_file, Mock())
        self.assertEquals(None, blame.process())

        # The bucket is unchanged
        self.assertEquals(
            {'Foo Bar': 0, 'Tim Pettersen': 0},
            blame.bucket
        )


class GuiltTestCase(TestCase):

    def setUp(self):
        initial_git_results = [
                (b'git version 1.8.7\n', None),
                (b'/my/arbitrary/path\n', None)
            ]

        def patched_popen(*args):
            try:
                output = initial_git_results.pop()
            except IndexError:
                output = (b'\n', None)
            finally:
                return output

        # We need to mock up subprocess.Popen so that the 'git' invocation
        # performed when the GitRunner object is instantiated doesn't result in
        # an actual process being forked
        self._popen_patch = patch('git_guilt.guilt.subprocess.Popen')
        self.mocked_popen = self._popen_patch.start()
        self.mocked_popen.return_value = Mock(
            communicate=Mock(side_effect=patched_popen),
            returncode=0,
        )

        self._stdout_patch = patch('git_guilt.guilt.sys.stdout')
        self.mocked_stdout = self._stdout_patch.start()
        self.mocked_stdout.return_value = Mock(
            fileno=Mock(return_value=1),
        )

        self._isatty_patch = patch('git_guilt.guilt.os.isatty')
        self.mocked_isatty = self._isatty_patch.start()
        self.mocked_isatty.return_value = False

        self.guilt = guilt_module.PyGuilt()

    def tearDown(self):
        self._popen_patch.stop()
        self._stdout_patch.stop()
        self._isatty_patch.stop()

    @patch('git_guilt.guilt.GitRunner.run_git')
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

    def test_reduce_locs(self):
        self.guilt.loc_ownership_since = {'Alice': 5, 'Bob': 3, 'Carol': 4}
        self.guilt.loc_ownership_until = {'Alice': 6, 'Bob': 6, 'Carol': 2, 'Dave': 1, 'Ellen': 2}

        expected_deltas = [
                guilt_module.Delta(until=6, since=3, author='Bob'),
                guilt_module.Delta(until=2, since=0, author='Ellen'),
                guilt_module.Delta(until=6, since=5, author='Alice'),
                guilt_module.Delta(until=1, since=0, author='Dave'),
                guilt_module.Delta(until=2, since=4, author='Carol'),
                ]

        self.guilt.reduce_blames()

        self.assertEquals(
            expected_deltas,
            self.guilt.loc_deltas
        )

    @patch('git_guilt.guilt.GitRunner.get_delta_files')
    def test_file_not_in_since_rev(self, mock_get_files, ):
        mock_get_files.return_value = (set(['in_since_and_until', 'not_in_since']), set([]))

        # Mock up arg namespace
        self.guilt.args = Mock()
        self.guilt.args.since = 'since'
        self.guilt.args.until = 'until'

        self.guilt.trees['since'] = ['in_since_and_until']
        self.guilt.trees['until'] = ['in_since_and_until', 'not_in_since']

        def mock_blame_logic(blame):
            if 'not_in_since' == blame.versioned_file.repo_path:
                if 'since' == blame.versioned_file.git_revision:
                    blame.exists = False
                elif 'until' == blame.versioned_file.git_revision:
                    blame.exists = True
                    blame.bucket['Alice'] += 20
                    blame.bucket['Bob'] += 5
            elif 'in_since_and_until' == blame.versioned_file.repo_path:
                blame.exists = True
                if 'since' == blame.versioned_file.git_revision:
                    blame.bucket['Alice'] += 12
                    blame.bucket['Bob'] += 8
                    blame.bucket['Dave'] += 4
                elif 'until' == blame.versioned_file.git_revision:
                    blame.exists = True
                    blame.bucket['Alice'] += 18
                    blame.bucket['Bob'] += 2
                    blame.bucket['Carol'] += 2

        # FIXME This monkey patching is ugly and should be handled through Mock
        old_process = guilt_module.TextBlameTicket.process
        try:
            guilt_module.TextBlameTicket.process = mock_blame_logic

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
            expected_guilt = [
                    guilt_module.Delta('Alice', 12, 38),
                    guilt_module.Delta('Bob', 8, 7),
                    guilt_module.Delta('Carol', 0, 2),
                    guilt_module.Delta('Dave', 4, 0)
                ]
            expected_guilt.sort()

            self.assertEquals(expected_guilt, self.guilt.loc_deltas)
        finally:
            guilt_module.TextBlameTicket.process = old_process

    @patch('git_guilt.guilt.GitRunner.get_delta_files')
    def test_file_not_in_until_rev(self, mock_get_files):
        mock_get_files.return_value = (set(['in_since_and_until', 'not_in_until']), set([]))

        # Mock up arg namespace
        self.guilt.args = Mock()
        self.guilt.args.since = 'since'
        self.guilt.args.until = 'until'

        self.guilt.trees['since'] = ['in_since_and_until', 'not_in_until']
        self.guilt.trees['until'] = ['in_since_and_until']

    @patch('git_guilt.guilt.GitRunner.get_delta_files')
    def test_map_text_blames(self, mock_get_delta):

        mock_get_delta.return_value = set(['foo.c', 'foo.h']), set([])

        self.guilt.args = Mock(since='HEAD~4', until='HEAD~1')
        self.guilt.trees['HEAD~4'] = ['foo.c', 'foo.h']
        self.guilt.trees['HEAD~1'] = ['foo.c', 'foo.h']


        def mock_blame_logic(blame):
            if 'foo.c' == blame.versioned_file.repo_path:
                if 'HEAD~4' == blame.versioned_file.git_revision:
                    blame.bucket['Alice'] += 20
                    blame.bucket['Bob'] += 5
                elif 'HEAD~1' == blame.versioned_file.git_revision:
                    blame.bucket['Carol'] += 2

            elif 'foo.h' == blame.versioned_file.repo_path:
                if 'HEAD~4' == blame.versioned_file.git_revision:
                    blame.bucket['Alice'] += 12
                elif 'HEAD~1' == blame.versioned_file.git_revision:
                    blame.bucket['Alice'] += 18

        # FIXME This monkey patching is ugly and should be handled through Mock
        old_process = guilt_module.TextBlameTicket.process
        try:
            guilt_module.TextBlameTicket.process = mock_blame_logic

            self.guilt.map_blames()

            # Assert the set of blame "jobs" generated by PyGuilt.map_blames()
            self.assertEquals(4, len(self.guilt.blame_jobs))
            self.assertEquals(
                [
                    guilt_module.TextBlameTicket(self.guilt.runner, self.guilt.loc_ownership_since, guilt_module.VersionedFile('foo.c', 'HEAD~4'), Mock()),
                    guilt_module.TextBlameTicket(self.guilt.runner, self.guilt.loc_ownership_until, guilt_module.VersionedFile('foo.c', 'HEAD~1'), Mock()),
                    guilt_module.TextBlameTicket(self.guilt.runner, self.guilt.loc_ownership_since, guilt_module.VersionedFile('foo.h', 'HEAD~4'), Mock()),
                    guilt_module.TextBlameTicket(self.guilt.runner, self.guilt.loc_ownership_until, guilt_module.VersionedFile('foo.h', 'HEAD~1'), Mock()),
                ],
                self.guilt.blame_jobs
            )

            # Assert the ownership buckets
            self.assertEquals({'Alice': 32, 'Bob': 5}, self.guilt.loc_ownership_since)
            self.assertEquals({'Alice': 18, 'Carol': 2}, self.guilt.loc_ownership_until)
            self.assertEquals({}, self.guilt.byte_ownership_since)
            self.assertEquals({}, self.guilt.byte_ownership_until)

            self.guilt.reduce_blames()

            # Alice's share of the collective guilt has decreased from 32 to 18
            # LOCs
            # Bob's share of the collective guilt has been wiped clean!
            # Carol's share has increased from nothing to 2
            expected_guilt = [
                    guilt_module.Delta('Alice', 32, 18),
                    guilt_module.Delta('Bob', 5, 0),
                    guilt_module.Delta('Carol', 0, 2)
                ]
            expected_guilt.sort()
            self.assertEquals(expected_guilt, self.guilt.loc_deltas)
            self.assertEquals([], self.guilt.byte_deltas)

        finally:
            guilt_module.TextBlameTicket.process = old_process

    @patch('git_guilt.guilt.GitRunner.get_delta_files')
    def test_map_binary_blames(self, mock_get_delta):

        mock_get_delta.return_value = set([]), set(['foo.bin', 'libbar.so.1.8.7'])

        self.guilt.args = Mock(since='HEAD~4', until='HEAD~1')
        self.guilt.trees['HEAD~4'] = ['foo.bin', 'libbar.so.1.8.7']
        self.guilt.trees['HEAD~1'] = ['foo.bin', 'libbar.so.1.8.7']


        def mock_blame_logic(blame):
            if 'foo.bin' == blame.versioned_file.repo_path:
                if 'HEAD~4' == blame.versioned_file.git_revision:
                    blame.bucket['Alice'] += 20
                    blame.bucket['Bob'] += 5
                elif 'HEAD~1' == blame.versioned_file.git_revision:
                    blame.bucket['Carol'] += 2

            elif 'libbar.so.1.8.7' == blame.versioned_file.repo_path:
                if 'HEAD~4' == blame.versioned_file.git_revision:
                    blame.bucket['Alice'] += 12
                elif 'HEAD~1' == blame.versioned_file.git_revision:
                    blame.bucket['Alice'] += 18

        # FIXME This monkey patching is ugly and should be handled through Mock
        old_process = guilt_module.BinaryBlameTicket.process
        try:
            guilt_module.BinaryBlameTicket.process = mock_blame_logic

            self.guilt.map_blames()

            # Assert the set of blame "jobs" generated by PyGuilt.map_blames()
            self.assertEquals(4, len(self.guilt.blame_jobs))
            self.assertEquals(
                [
                    guilt_module.BinaryBlameTicket(self.guilt.runner, self.guilt.byte_ownership_since, guilt_module.VersionedFile('foo.bin', 'HEAD~4'), Mock()),
                    guilt_module.BinaryBlameTicket(self.guilt.runner, self.guilt.byte_ownership_until, guilt_module.VersionedFile('foo.bin', 'HEAD~1'), Mock()),
                    guilt_module.BinaryBlameTicket(self.guilt.runner, self.guilt.byte_ownership_since, guilt_module.VersionedFile('libbar.so.1.8.7', 'HEAD~4'), Mock()),
                    guilt_module.BinaryBlameTicket(self.guilt.runner, self.guilt.byte_ownership_until, guilt_module.VersionedFile('libbar.so.1.8.7', 'HEAD~1'), Mock()),
                ],
                self.guilt.blame_jobs
            )

            # Assert the ownership buckets
            self.assertEquals({}, self.guilt.loc_ownership_since)
            self.assertEquals({}, self.guilt.loc_ownership_until)
            self.assertEquals({'Alice': 32, 'Bob': 5}, self.guilt.byte_ownership_since)
            self.assertEquals({'Alice': 18, 'Carol': 2}, self.guilt.byte_ownership_until)

            self.guilt.reduce_blames()

            # Alice's share of the collective guilt has decreased from 32 to 18
            # bytes
            # Bob's share of the collective guilt has been wiped clean!
            # Carol's share has increased from nothing to 2
            expected_guilt = [
                    guilt_module.Delta('Alice', 32, 18),
                    guilt_module.Delta('Bob', 5, 0),
                    guilt_module.Delta('Carol', 0, 2)
                ]
            expected_guilt.sort()
            self.assertEquals(expected_guilt, self.guilt.byte_deltas)
            self.assertEquals([], self.guilt.loc_deltas)

        finally:
            guilt_module.BinaryBlameTicket.process = old_process


    # Many more testcases are required!!
    @patch('git_guilt.guilt.PyGuilt.populate_trees')
    @patch('git_guilt.guilt.Formatter.show_guilt_stats')
    @patch('git_guilt.guilt.PyGuilt.reduce_blames')
    @patch('git_guilt.guilt.PyGuilt.map_blames')
    @patch('git_guilt.guilt.PyGuilt.process_args')
    def test_show_run(self, mock_process_args, mock_map, mock_reduce, mock_show, mock_pop_trees):

        if 2 == sys.version_info[0]:
            stdout_patch = patch('sys.stdout', new_callable=io.BytesIO)
        elif 3 == sys.version_info[0]:
            stdout_patch = patch('sys.stdout', new_callable=io.StringIO)
        mock_stdout = stdout_patch.start()

        def set_byte_deltas():
            self.guilt.loc_deltas=[guilt_module.Delta('foo', 45, 25)]
            self.guilt.byte_deltas=[guilt_module.BinaryDelta('bar', 5, 78)]
            self.guilt.loc_formatter.deltas = self.guilt.loc_deltas
            self.guilt.byte_formatter.deltas = self.guilt.byte_deltas

        mock_reduce.side_effect = set_byte_deltas

        self.assertEquals(0, self.guilt.run())
        stdout_patch.stop()

        # Assert calls
        mock_process_args.assert_called_once_with()
        mock_pop_trees.assert_called_once_with()
        mock_map.assert_called_once_with()
        mock_reduce.assert_called_once_with()
        self.assertEquals(2, len(mock_show.mock_calls))


class FormatterTestCase(TestCase):

    def setUp(self):
        # Mock stdout.fileno()
        self._stdout_patch = patch('git_guilt.guilt.sys.stdout')
        self.mocked_stdout = self._stdout_patch.start()
        self.mocked_stdout.return_value = Mock(
            fileno=Mock(return_value=1),
        )

        # Mock os.isatty
        self._isatty_patch = patch('git_guilt.guilt.os.isatty')
        self.mocked_isatty = self._isatty_patch.start()
        self.mocked_isatty.return_value = False

        self.formatter = guilt_module.Formatter([])

    def tearDown(self):
        self._isatty_patch.stop()

    def test_get_width_not_tty(self):
        self.assertEquals(80, self.formatter._get_tty_width())

    def test_red(self):
        self.formatter._is_tty = True
        self.assertEquals('\033[31mRED\033[0m', self.formatter.red('RED'))

        self.formatter._is_tty = False
        self.assertEquals('RED', self.formatter.red('RED'))

    def test_green(self):
        self.formatter._is_tty = True
        self.assertEquals('\033[32mGREEN\033[0m', self.formatter.green('GREEN'))

        self.formatter._is_tty = False
        self.assertEquals('GREEN', self.formatter.green('GREEN'))

    @patch('git_guilt.guilt.fcntl.ioctl')
    def test_get_width_tty(self, mocked_ioctl):
        self._isatty_patch.stop()

        mocked_isatty = self._isatty_patch.start()
        mocked_isatty.return_value = True
        del self.formatter

        mocked_ioctl.return_value = b'\x00\x00\x6e\x00\x00\x00\x00\x00'
        self.formatter = guilt_module.Formatter([])
        self.assertEquals(110, self.formatter._get_tty_width())
        del self.formatter

        # For whatever reason, we get a length of 0 - expect 80
        mocked_ioctl.return_value = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        self.formatter = guilt_module.Formatter([])
        self.assertEquals(80, self.formatter._get_tty_width())
        del self.formatter

        del mocked_ioctl.return_value
        mocked_ioctl.side_effect = IOError
        self.formatter = guilt_module.Formatter([])
        self.assertEquals(80, self.formatter._get_tty_width())
        del self.formatter

    def test_show_text_guilt(self):
        if 2 == sys.version_info[0]:
            stdout_patch = patch('sys.stdout', new_callable=io.BytesIO)
        elif 3 == sys.version_info[0]:
            stdout_patch = patch('sys.stdout', new_callable=io.StringIO)

        mock_stdout = stdout_patch.start()


        self.formatter.deltas.append(guilt_module.Delta(u'short', 30, 45))
        self.formatter.deltas.append(guilt_module.Delta(u'Very Long Name', 10, 7))

        self.formatter.show_guilt_stats()
        self.assertEquals(''' short          | 15 +++++++++++++++
 Very Long Name | -3 ---
''',
            mock_stdout.getvalue()
        )
        stdout_patch.stop()

    def test_show_binary_guilt(self):
        if 2 == sys.version_info[0]:
            stdout_patch = patch('sys.stdout', new_callable=io.BytesIO)
        elif 3 == sys.version_info[0]:
            stdout_patch = patch('sys.stdout', new_callable=io.StringIO)

        mock_stdout = stdout_patch.start()

        self.formatter.deltas.append(guilt_module.BinaryDelta(u'short', 30, 45))
        self.formatter.deltas.append(guilt_module.BinaryDelta(u'Very Long Name', 10, 7))

        self.formatter.show_guilt_stats()
        self.assertEquals(''' short          | Bin 30 -> 45 bytes
 Very Long Name | Bin 10 -> 7 bytes
''',
            mock_stdout.getvalue()
        )
        stdout_patch.stop()
