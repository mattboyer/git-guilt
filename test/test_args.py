from mock import patch, Mock
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
