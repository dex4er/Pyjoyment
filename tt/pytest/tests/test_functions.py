from Pyjo.Test import diag, done_testing, is_deeply_ok, is_ok, ok, plan, subtest


def test_pass():
    ok(True, 'true')
    is_ok(1, 1, 'same')
    done_testing()


def test_is_deeply():
    is_deeply_ok({'a': [1, 2]}, {'a': [1, 3]}, 'deep structure')


def test_diag():
    diag('a diagnostic message')
    ok(False, 'after diag')


def test_skip_all():
    plan(skip_all='not today')
    ok(False, 'never')


def test_skip_subtest():
    with subtest('Skipped'):
        plan(skip_all='not in this subtest')
        ok(False, 'never')
    ok(True, 'after the subtest')


def test_chain():
    is_ok('Hello', 'Hello', 'same').like(r'^Bye', 'greeting').is_('Hello', 'never')
