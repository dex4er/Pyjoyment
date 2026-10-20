def test_index(t):
    t.get_ok('/').status_is(200).content_is('Hello')


def test_wrong_content(t):
    t.get_ok('/').status_is(200).content_is('Bye')
