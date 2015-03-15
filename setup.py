from setuptools import setup, find_packages
import version

setup(
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
    ],
    keywords='git blame guilt',
    packages=find_packages(exclude=['test']),
    data_files = [('man/man1', ['docs/git-guilt.1'])],
    install_requires=[],
    entry_points={
        'console_scripts': [
            'git-guilt = src.guilt:main'
        ]
    }
)
