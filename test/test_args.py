from mock import patch, Mock, call
from unittest import TestCase

import guilt

# FIXME Should probably use mock.patch instead
guilt.GitRunner._git_executable = 'nosuchgit'

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
    def test_bad_args(self):
        with self.assertRaises(guilt.ArgumentError):
            self.guilt.process_args()

        self.assertEquals(1, self.guilt.run())

    @patch('sys.argv', ['arg0', '--help'])
    def test_help(self):
        with self.assertRaises(SystemExit):
            self.guilt.process_args()

        with self.assertRaises(SystemExit):
            self.guilt.run()


class GitRunnerTestCase(TestCase):

    def setUp(self):
        pass

    @patch('guilt.subprocess.Popen')
    def test_run_git_cwd(self, mock_process):
        mock_process.return_value.communicate = Mock(return_value=('bar', None))

        runner = guilt.GitRunner()
        runner._git_toplevel = None
        runner._run_git(['foo'])

        mock_process.assert_called_once_with(['nosuchgit', 'foo'], stderr=-1, stdout=-1, universal_newlines=True)
        mock_process.reset_mock()

        runner._git_toplevel = '/my/top/level/git/directory'
        runner._run_git(['foo'])
        mock_process.assert_called_once_with(['nosuchgit', 'foo'], cwd='/my/top/level/git/directory', stderr=-1, stdout=-1, universal_newlines=True)
