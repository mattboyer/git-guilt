from mock import patch, Mock, call
from unittest import TestCase

import guilt

class ArgTestCase(TestCase):

    def setUp(self):
        self.guilt = guilt.PyGuilt()

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
        # We call get_root from __init__!!!
        self.runner = guilt.GitRunner()


    @patch('guilt.GitRunner._get_git_root')
    def test_get_root_is_called(self, mock_get_root):
        runner = guilt.GitRunner()
        mock_get_root.assert_called_once()


    @patch('guilt.subprocess.Popen')
    def test_run_git_cwd(self, mock_process):
        mock_process.return_value.communicate = Mock(return_value=('bar', None))

        self.runner._git_toplevel = None
        self.runner._run_git(['foo'])

        self.assertEquals(
            [call('git')],
            mock_process.mock_calls
        )
