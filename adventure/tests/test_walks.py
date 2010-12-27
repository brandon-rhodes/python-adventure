import doctest

def load_tests(loader, tests, pattern):
    tests.addTests(doctest.DocFileSuite('walkthrough1.txt'))
    tests.addTests(doctest.DocFileSuite('walkthrough2.txt'))
    return tests
