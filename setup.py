import os
import sys
from distutils.core import setup

if sys.version_info < (3,):
    print('\nSorry, but Adventure can only be installed under Python 3.\n')
    sys.exit(1)

README_PATH = os.path.join(os.path.dirname(__file__), 'adventure', 'README.txt')
with open(README_PATH, encoding="utf-8") as f:
    README_TEXT = f.read()

setup(
    name='adventure',
    version='1.6',
    description='Colossal Cave adventure game at the Python prompt',
    long_description=README_TEXT,
    author='Brandon Craig Rhodes',
    author_email='brandon@rhodesmill.org',
    url='https://github.com/brandon-rhodes/python-adventure',
    packages=['adventure', 'adventure/tests'],
    package_data={'adventure': ['README.txt', '*.dat', 'tests/*.txt']},
    classifiers=[
        'Development Status :: 6 - Mature',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Topic :: Games/Entertainment',
    ],
)
