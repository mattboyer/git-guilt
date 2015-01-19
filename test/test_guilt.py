import io
from mock import patch, Mock, call
from unittest import TestCase
import test.constants

import guilt

# FIXME Should probably use mock.patch instead
guilt.GitRunner._git_executable = 'nosuchgit'

class DeltaTestCase(TestCase):

    def test_eq(self):
        a = guilt.Delta('Alpha', 4)
        b = guilt.Delta('Beta', 6)
        self.assertFalse(a == b)
        self.assertTrue(a != b)

        b = guilt.Delta('Alpha', 6)
        self.assertFalse(a == b)
        self.assertTrue(a != b)

        b = guilt.Delta('Alpha', 4)
        self.assertTrue(a == b)
        self.assertTrue(a <= b)
        self.assertTrue(a >= b)
        self.assertFalse(a != b)

    def test_comparison(self):
        a = guilt.Delta('Alpha', 4)

        # a > b because a is guiltier than b
        b = guilt.Delta('Beta', -6)

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
        b = guilt.Delta('Beta', 4)

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

        b = guilt.Delta('Aardvark', 4)
        self.assertFalse(a < b)
        self.assertFalse(a <= b)

        self.assertTrue(a > b)
        self.assertTrue(a >= b)

    def test_repr(self):
        a = guilt.Delta('Alpha', -4)
        b = guilt.Delta('Beta', 6)
        c = guilt.Delta('Gamma', 0)

        self.assertEquals("<Delta \"Alpha\": -4>", repr(a))
        self.assertEquals("<Delta \"Beta\": 6>", repr(b))
        self.assertEquals("<Delta \"Gamma\": 0>", repr(c))


    def test_str(self):
        a = guilt.Delta('Alpha', -4)
        b = guilt.Delta('Beta', 6)
        c = guilt.Delta('Gamma', 0)

        self.assertEquals("Alpha [-4]: ----", str(a))
        self.assertEquals("Beta [6]: ++++++", str(b))
        self.assertEquals("Gamma [0]: ", str(c))

class ArgTestCase(TestCase):

    def setUp(self):
        # We need to mock up subprocess.Popen so that the 'git' invocation
        # performed when the GitRunner object is instantiated doesn't result in
        # an actual process being forked
        self._popen_patch = patch('guilt.subprocess.Popen')
        self.mocked_popen = self._popen_patch.start()
        self.mocked_popen.return_value = Mock(
            communicate=Mock(return_value=('bar', None))
        )

        self.guilt = guilt.PyGuilt()

    def tearDown(self):
        self._popen_patch.stop()

    @patch('sys.argv', ['arg0', 'foo'])
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_bad_args(self, mock_stderr):

        with self.assertRaises(guilt.GitError):
            self.guilt.process_args()

        self.assertEquals(1, self.guilt.run())
        self.assertEquals('bad args', mock_stderr.getvalue())

    @patch('sys.argv', ['arg0', '--help'])
    def test_help(self):
        with self.assertRaises(SystemExit):
            self.guilt.process_args()

        with self.assertRaises(SystemExit):
            self.guilt.run()


class GitRunnerTestCase(TestCase):

    def setUp(self):
        # We need to mock up subprocess.Popen so that the 'git' invocation
        # performed when the GitRunner object is instantiated doesn't result in
        # an actual process being forked
        self._popen_patch = patch('guilt.subprocess.Popen')
        self.mocked_popen = self._popen_patch.start()
        self.mocked_popen.return_value = Mock(
            communicate=Mock(return_value=('bar', None))
        )

        self.runner = guilt.GitRunner()
        self._popen_patch.stop()

    def tearDown(self):
        pass

    @patch('guilt.subprocess.Popen')
    def test_run_git_cwd(self, mock_process):
        mock_process.return_value.communicate = Mock(return_value=('bar', None))

        self.runner._git_toplevel = None
        self.runner._run_git(['foo'])

        mock_process.assert_called_once_with(['nosuchgit', 'foo'], stderr=-1, stdout=-1, universal_newlines=True)
        mock_process.reset_mock()

        self.runner._git_toplevel = '/my/top/level/git/directory'
        self.runner._run_git(['foo'])
        mock_process.assert_called_once_with(['nosuchgit', 'foo'], cwd='/my/top/level/git/directory', stderr=-1, stdout=-1, universal_newlines=True)

    @patch('guilt.subprocess.Popen')
    def test_run_git_no_output(self, mock_process):
        mock_process.return_value.communicate = Mock(return_value=('', None))

        with self.assertRaises(ValueError):
            self.runner._run_git(['log'])

    @patch('guilt.subprocess.Popen')
    def test_run_git_exception(self, mock_process):
        mock_process.return_value.communicate = Mock(side_effect=OSError)

        with self.assertRaises(guilt.GitError):
            self.runner._run_git(['log'])

    @patch('guilt.subprocess.Popen')
    def test_run_git_stderr(self, mock_process):
        mock_process.return_value.communicate = Mock(return_value=('', 'error'))

        with self.assertRaises(guilt.GitError):
            self.runner._run_git(['log'])

    @patch('guilt.subprocess.Popen')
    def test_run_git(self, mock_process):
        mock_process.return_value.communicate = Mock(return_value=('a\nb\nc', None))

        self.assertEquals(['a', 'b', 'c'], self.runner._run_git(['log']))

    @patch('guilt.GitRunner._run_git')
    def test_get_delta_files(self, mock_run_git):
        mock_run_git.return_value = ['foo.c', 'foo.h']

        self.assertEquals(
            set(['foo.c', 'foo.h']),
            self.runner.get_delta_files('HEAD~1', 'HEAD')
        )

    @patch('guilt.GitRunner._run_git')
    def test_get_delta_no_files(self, mock_run_git):
        mock_run_git.return_value = []

        with self.assertRaises(ValueError):
            self.runner.get_delta_files('HEAD~1', 'HEAD')

    @patch('guilt.GitRunner._run_git')
    def test_blame_locs(self, mock_run_git):
        mock_run_git.return_value = test.constants.blame_author_names.splitlines()

        blame = Mock()
        blame.repo_path = 'src/foo.c'
        blame.bucket = {'Foo Bar': 0, 'Tim Pettersen': 0}

        self.runner.blame_locs(blame)
        self.assertEquals(
            {'Foo Bar': 2, 'Tim Pettersen': 3},
            blame.bucket
        )

    @patch('guilt.subprocess.Popen')
    def test_get_git_root_exception(self, mock_process):
        mock_process.return_value.communicate = Mock(side_effect=OSError)

        with self.assertRaises(SystemExit):
            new_runner = guilt.GitRunner()


class GuiltTestCase(TestCase):

    def setUp(self):
        # We need to mock up subprocess.Popen so that the 'git' invocation
        # performed when the GitRunner object is instantiated doesn't result in
        # an actual process being forked
        self._popen_patch = patch('guilt.subprocess.Popen')
        self.mocked_popen = self._popen_patch.start()
        self.mocked_popen.return_value = Mock(
            communicate=Mock(return_value=('bar', None))
        )

        self.guilt = guilt.PyGuilt()

    def tearDown(self):
        self._popen_patch.stop()

    @patch('guilt.GitRunner.get_delta_files')
    def test_map_blames(self, mock_get_delta):
        mock_get_delta.return_value = ['foo.c', 'foo.h']
        self.guilt.args = Mock(since='HEAD~4', until='HEAD~1')

        self.guilt.map_blames()
        self.assertEquals(4, len(self.guilt.blame_queue))
        self.assertEquals(
                [
                    guilt.BlameTicket(self.guilt.since, 'foo.c', 'HEAD~4'),
                    guilt.BlameTicket(self.guilt.until, 'foo.c', 'HEAD~1'),
                    guilt.BlameTicket(self.guilt.since, 'foo.h', 'HEAD~4'),
                    guilt.BlameTicket(self.guilt.until, 'foo.h', 'HEAD~1'),
                ],
                self.guilt.blame_queue
            )



    def test_reduce_locs(self):
        self.guilt.since = {'Alice': 5, 'Bob': 3, 'Carol': 4}
        self.guilt.until = {'Alice': 6, 'Bob': 6, 'Carol': 2, 'Dave': 1, 'Ellen': 2}

        expected_deltas = [
                guilt.Delta(count=3, author='Bob'),
                guilt.Delta(count=2, author='Ellen'),
                guilt.Delta(count=1, author='Alice'),
                guilt.Delta(count=1, author='Dave'),
                guilt.Delta(count=-2, author='Carol'),
                ]

        deltas = self.guilt.reduce_blames()

        self.assertEquals(
            expected_deltas,
            deltas
        )

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_show_guilt(self, mock_stdout):
        self.guilt.loc_deltas = [guilt.Delta('foo', 15)]
        self.guilt.files = ['a', 'b']

        self.guilt.show_guilt_stats()
        self.assertEquals('''
foo [15]: +++++++++++++++
2 files changed
'''.lstrip(),
            mock_stdout.getvalue()
        )
