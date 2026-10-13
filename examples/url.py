import Pyjo.URL

from Pyjo.String.Unicode import u


# 'ssh+git://git@github.com/dex4er/Pyjoyment.git'
url = Pyjo.URL.new('https://github.com/dex4er/Pyjoyment')
print(url.set(scheme='ssh+git', userinfo='git', path=u(url.path) + '.git'))

# 'https://pypi.org/search/?q=Pyjoyment&o=&c=Programming+Language+%3A%3A+Python'
url = Pyjo.URL.new('https://pypi.org/search/')
print(url.set(query=[('q', 'Pyjoyment'), ('o', ''), ('c', 'Programming Language :: Python')]))
