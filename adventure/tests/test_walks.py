import doctest
import os

def load_tests(loader, tests, pattern):
    if os.path.exists('advent.save'):
        os.unlink('advent.save')  # to avoid an error during README.txt
    tests.addTests(doctest.DocFileSuite(
            '../README.txt', optionflags=doctest.NORMALIZE_WHITESPACE))
    tests.addTests(doctest.DocFileSuite('syntax.txt'))
    tests.addTests(doctest.DocFileSuite('vignettes.txt'))
    tests.addTests(doctest.DocFileSuite('walkthrough1.txt'))
    tests.addTests(doctest.DocFileSuite('walkthrough2.txt'))
    return tests
