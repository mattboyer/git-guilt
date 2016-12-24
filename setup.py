import os
from setuptools import setup
from setuptools.command.build_py import build_py as SetupToolsBdistPyCmd
from setuptools.command.sdist import sdist as SetupToolsSdistCmd
import version


class SphinxThenSetuptoolsBdistPyCmd(SetupToolsBdistPyCmd):
    '''
    Ensures that building a "binary distribution" (egg, wheel, etc.) triggers
    the creation of the dynamic Sphinx-generated man page which is referenced
    in ``MANIFEST.in``.
    '''
    def run(self):
        # We want to skip the 'build_sphinx' step when we're run as part of
        # installing a sdist, since the sdist doesn't contain docs/conf.py
        # (docs isn't a package, and we don't explicitly include the file in
        # MANIFEST.in) and it already has the man page anyway.
        build_docs_path = os.path.join(os.getcwd(), 'docs', 'conf.py')
        if os.path.isfile(build_docs_path):
            self.run_command('build_sphinx')
        SetupToolsBdistPyCmd.run(self)


class SphinxThenSetuptoolsSdistCmd(SetupToolsSdistCmd):
    '''
    Ensures that building a "source distribution" triggers the creation of the
    dynamic Sphinx-generated man page which is referenced in ``MANIFEST.in``.
    '''
    def run(self):
        self.run_command('build_sphinx')
        SetupToolsSdistCmd.run(self)

setup(
    cmdclass={
        'sdist': SphinxThenSetuptoolsSdistCmd,
        'build_py': SphinxThenSetuptoolsBdistPyCmd,
    },
    name='git-guilt',
    version=version.get_git_version(),
    url='https://github.com/mattboyer/git-guilt',
    description='git-guilt provides information on the transfer of '
        'ownership in a Git repository',
    author='Matt Boyer',
    author_email='mboyer@sdf.org',
    license='BSD',
    classifiers=[
        'Environment :: Console',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Topic :: Software Development :: Version Control',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='git blame guilt',
    packages=['git_guilt'],
    include_package_data=True,
    data_files=[('man/man1', ['docs/man/git-guilt.1'])],
    install_requires=['argparse'],
    entry_points={
        'console_scripts': [
            'git-guilt = git_guilt.guilt:main'
        ]
    },
    command_options={
        'build_sphinx': {
            'builder': ('foo', 'man'),
            'build_dir': ('foo', 'docs'),
            'config_dir': ('foo', 'docs'),
            'all_files': ('foo', True),
            'fresh_env': ('foo', True),
        },
    },
)
