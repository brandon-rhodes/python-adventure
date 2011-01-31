import os
from distutils.core import setup

README_PATH = os.path.join(os.path.dirname(__file__), 'adventure', 'README.txt')
with open(README_PATH) as f:
    README_TEXT = f.read()

setup(
    name='adventure',
    version='0.3',
    description='Colossal cave adventure game at the Python prompt',
    long_description=README_TEXT,
    author='Brandon Craig Rhodes',
    author_email='brandon@rhodesmill.org',
    url='https://bitbucket.org/brandon/adventure/overview',
    packages=['adventure', 'adventure/tests'],
    package_data={'adventure': ['README.txt', '*.dat', 'tests/*.txt']},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Topic :: Games/Entertainment',
        ],
    )
