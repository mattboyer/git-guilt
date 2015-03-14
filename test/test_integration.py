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
# -*- coding: UTF-8 -*-

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
            converted = str(input)
        elif 3 == sys.version_info[0]:
            converted = bytes(input, encoding='utf_8')
        return converted

    def test_usage(self):
        o, e = self.run_cli('-h')
        self.assertEquals(b'', e)

        expected_stdout = '''usage: git guilt [-h] [-w] [-e] [since] [until]

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
        expected_stdout = ''' 张三李四      |  2 ++
 Latin McAscii | -4 ----
'''
        self.assertEquals(self.prepare_expected_string(expected_stdout), o)
