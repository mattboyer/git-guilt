from mock import patch, Mock
from unittest import TestCase

import guilt

class ArgTestCase(TestCase):
    def setUp(self):
        self.guilt = guilt.PyGuilt()

    @patch('guilt.argparse._sys.argv', ['--help'])
    def test_help(self):
        self.guilt.run()
