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

from unittest import TestCase
import subprocess
import sys
import os

class IntegrationTests(TestCase):

    def run_cli(self, args):
        test_repo_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "..",  "git_test_repo")
        )
        if not isinstance(args, list):
            args = args.split()

        guilt_process = subprocess.Popen(
            ["git-guilt"] + args,
            cwd=test_repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            out, err = guilt_process.communicate()
            guilt_process.wait()
        except Exception as e:
            raise GitError("Couldn't run 'git {args}':{newline}{ex}".format(
                args=' '.join(args),
                newline=os.linesep,
                ex=str(e)
            ))
        else:
            return out, err

    def prepare_expected_string(self, input):
        if 2 == sys.version_info[0]:
            converted = unicode(input).encode('utf_8')
        elif 3 == sys.version_info[0]:
            converted = bytes(input, encoding='utf_8')
        return converted

    def test_usage(self):
        o, e = self.run_cli('-h')
        self.assertEquals(b'', e)

        expected_stdout = u'''usage: git guilt [-h] [-w] [-e] [since] [until]

positional arguments:
  since
  until

optional arguments:
  -h, --help        show this help message and exit
  -w, --whitespace
  -e, --email
'''

        self.assertEquals(self.prepare_expected_string(expected_stdout), o)

    def test_01(self):
        o, e = self.run_cli('49288d8af7984ad62073d447fd94531c0123034f f410635b54ad97bbeb0d28c8ac32ada55d92fcf2')
        self.assertEquals(b'', e)
        expected_stdout = u''' 张三李四      |  2 ++
 Latin McAscii | -4 ----
'''
        self.assertEquals(self.prepare_expected_string(expected_stdout), o)

    def test_02(self):
        o, e = self.run_cli('49288d8af7984ad62073d447fd94531c0123034f 45c19e994880fda771c03a98e8f38cce877cfe91')
        self.assertEquals(b'', e)
        expected_stdout = u''' 张三李四      |  2 ++
 Latin McAscii | -4 ----

 Latin McAscii | 512 (0->512) bytes
'''
        self.assertEquals(self.prepare_expected_string(expected_stdout), o)

    def test_03(self):
        o, e = self.run_cli('49288d8af7984ad62073d447fd94531c0123034f b6633ac3fc3177b8d293c2e6ab2f5e576ee70977')
        self.assertEquals(b'', e)
        expected_stdout = u''' 张三李四      |  2 ++
 Latin McAscii | -4 ----

 Latin McAscii | 501 (0->501) bytes
 张三李四      |  11 (0->11) bytes
'''
        self.assertEquals(self.prepare_expected_string(expected_stdout), o)

    def test_04(self):
        # From f4106 to 45c1, the only transfer that's occurred is the new
        # bytes authored by LMcA - the in-line changes performed by that author
        # do not impact their overall ownership of the repository
        o, e = self.run_cli('f410635b54ad97bbeb0d28c8ac32ada55d92fcf2 45c19e994880fda771c03a98e8f38cce877cfe91')
        self.assertEquals(b'', e)
        expected_stdout = u'''
 Latin McAscii | 512 (0->512) bytes
'''
        self.assertEquals(self.prepare_expected_string(expected_stdout), o)

    def test_05(self):
        # From f4106 to b6633
        o, e = self.run_cli('f410635b54ad97bbeb0d28c8ac32ada55d92fcf2 b6633ac3fc3177b8d293c2e6ab2f5e576ee70977')

        self.assertEquals(b'', e)
        expected_stdout = u'''
 Latin McAscii | 501 (0->501) bytes
 张三李四      |  11 (0->11) bytes
'''
        self.assertEquals(self.prepare_expected_string(expected_stdout), o)

    def test_06(self):
        # From 45c19 to b6633
        o, e = self.run_cli('f410635b54ad97bbeb0d28c8ac32ada55d92fcf2 b6633ac3fc3177b8d293c2e6ab2f5e576ee70977')

        self.assertEquals(b'', e)
        expected_stdout = u'''
 Latin McAscii | 501 (0->501) bytes
 张三李四      |  11 (0->11) bytes
'''
        self.assertEquals(self.prepare_expected_string(expected_stdout), o)

    def test_07(self):
        o, e = self.run_cli('b6633ac3fc3177b8d293c2e6ab2f5e576ee70977 49288d8af7984ad62073d447fd94531c0123034f')
        self.assertEquals(b'', e)
        expected_stdout = u''' 张三李四      |  2 ++
 Latin McAscii | -4 ----

 Latin McAscii | 501 (0->501) bytes
 张三李四      |  11 (0->11) bytes
'''
        self.assertEquals(self.prepare_expected_string(expected_stdout), o)
