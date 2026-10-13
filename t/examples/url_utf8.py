if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import Pyjo.URL

    url1 = Pyjo.URL.new('http://pl.wikipedia.org').set(
        path='/w/index.php', query=[('title', 'Wikipedia:Strona_główna'), ('action', 'history')]
    )
    is_ok(
        str(url1),
        'http://pl.wikipedia.org/w/index.php?title=Wikipedia%3AStrona_g%C5%82%C3%B3wna&action=history',
        'url1',
    )

    url2 = Pyjo.URL.new('http://pl.wikipedia.org').set(path='/wiki/Wikipedia:Strona_główna')
    is_ok(str(url2), 'http://pl.wikipedia.org/wiki/Wikipedia:Strona_g%C5%82%C3%B3wna', 'url2')

    url3 = Pyjo.URL.new('http://żółwie.pl')
    is_ok(str(url3), 'http://xn--wie-fna90bfl.pl', 'url3')

    url4 = Pyjo.URL.new('http://localhost').set(userinfo='gęślą:jaźń')
    is_ok(str(url4), 'http://g%C4%99%C5%9Bl%C4%85:ja%C5%BA%C5%84@localhost', 'url4')

    done_testing()
