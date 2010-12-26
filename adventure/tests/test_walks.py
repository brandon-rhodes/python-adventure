import doctest

def load_tests(loader, tests, pattern):
    kw = dict(optionflags=doctest.NORMALIZE_WHITESPACE)
    tests.addTests(doctest.DocFileSuite('walkthrough1.txt', **kw))
    tests.addTests(doctest.DocFileSuite('walkthrough2.txt', **kw))
    return tests
