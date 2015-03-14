from setuptools import setup, find_packages
import version

setup(
    name='git-guilt',
    version=version.get_git_version(),
    url='https://github.com/mattboyer/py_git-guilt',
    description='Foo',
    author='Matt Boyer',
    author_email='mboyer@sdf.org',
    license='BSD',
    classifiers=[],
    keywords='git blame guilt',
    packages=find_packages(exclude=['test']),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'git-guilt = src.guilt:main'
        ]
    }
)
