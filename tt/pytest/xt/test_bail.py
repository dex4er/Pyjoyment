from Pyjo.Test import bail_out, ok


def test_bail_out():
    bail_out('No database connection')


def test_after():
    ok(True, 'never run')
