from mock import patch, Mock
from unittest import TestCase

from guilt import *

class ArgTestCase(TestCase):
    def setUp(self):
        self.guilt = PyGuilt()

    @patch('sys.argv', ['--help'])
    def test_help(self):
        self.guilt.run()
