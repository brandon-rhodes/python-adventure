"""Test suite.

Copyright 2010-2015 Brandon Rhodes.  Licensed as free software under the
Apache License, Version 2.0 as detailed in the accompanying README.txt.

"""
import doctest
import os
import shutil
import tempfile

def load_tests(loader, tests, pattern):
    cd = ChdirTemp()
    tests.addTests(doctest.DocFileSuite(
        '../README.txt', optionflags=doctest.NORMALIZE_WHITESPACE,
        setUp=cd.setup, tearDown=cd.teardown))
    tests.addTests(doctest.DocFileSuite('syntax.txt'))
    tests.addTests(doctest.DocFileSuite('vignettes.txt'))
    tests.addTests(doctest.DocFileSuite('walkthrough1.txt'))
    tests.addTests(doctest.DocFileSuite('walkthrough2.txt'))
    tests.addTests(doctest.DocFileSuite('walkthrough3.txt'))
    return tests

class ChdirTemp(object):
    def setup(self, doctest_object):
        self.old_directory = os.getcwd()
        self.tmp_directory = tempfile.mkdtemp()
        os.chdir(self.tmp_directory)

    def teardown(self, doctest_object):
        os.chdir(self.old_directory)
        shutil.rmtree(self.tmp_directory)
