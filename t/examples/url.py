if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.URL

    url = Pyjo.URL.new('https://github.com/dex4er/Pyjo')
    is_ok(
        str(url.set(scheme='ssh+git', userinfo='git', path=f'{url.path}.git')),
        'ssh+git://git@github.com/dex4er/Pyjo.git',
        'new github.com url',
    )

    url = Pyjo.URL.new('https://pypi.org/search/')
    is_ok(
        str(url.set(query=[('q', 'Pyjoyment'), ('o', ''), ('c', 'Programming Language :: Python')])),
        'https://pypi.org/search/?q=Pyjoyment&o=&c=Programming+Language+%3A%3A+Python',
        'new pypi.org url',
    )

    done_testing()
