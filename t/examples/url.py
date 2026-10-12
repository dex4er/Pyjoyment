import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.URL
    from Pyjo.String.Unicode import u

    url = Pyjo.URL.new('https://github.com/dex4er/Pyjo')
    is_ok(
        str(url.set(scheme='ssh+git', userinfo='git', path=u(url.path) + '.git')),
        'ssh+git://git@github.com/dex4er/Pyjo.git',
        'new github.com url',
    )

    is_ok(
        str(Pyjo.URL.new('http://metacpan.org/search').set(query={'q': 'Mojo::URL', 'size': 20})),
        'http://metacpan.org/search?q=Mojo::URL&size=20',
        'new metacpan.org url',
    )

    done_testing()
