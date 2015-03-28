from setuptools import setup
from distutils.command.build import build as DistUtilsBuild
import version

class SphinxBuild(DistUtilsBuild):

    def run(self):
        self.run_command('build_sphinx')
        super(SphinxBuild, self).run()


setup(
    cmdclass={'build': SphinxBuild},
    name='git-guilt',
    version=version.get_git_version(),
    url='https://github.com/mattboyer/git-guilt',
    description='git-guilt provides information on the transfer of '\
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
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='git blame guilt',
    packages=['git_guilt'],
    include_package_data=True,
    data_files = [('man/man1', ['docs/man/git-guilt.1'])],
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
            'config-dir': ('foo', 'docs'),
            'all_files': ('foo', True),
            'fresh_env': ('foo', True),
        },
    },
)
