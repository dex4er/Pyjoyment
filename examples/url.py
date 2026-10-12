import Pyjo.URL

from Pyjo.String.Unicode import u


# 'ssh+git://git@github.com/dex4er/Pyjoyment.git'
url = Pyjo.URL.new('https://github.com/dex4er/Pyjoyment')
print(url.set(scheme='ssh+git', userinfo='git', path=u(url.path) + '.git'))

# 'http://metacpan.org/search?q=Mojo::URL&size=20'
print(Pyjo.URL.new('http://metacpan.org/search').set(query={'q': 'Mojo::URL', 'size': 20}))
