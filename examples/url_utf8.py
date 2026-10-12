import Pyjo.URL


url1 = Pyjo.URL.new('http://pl.wikipedia.org').set(
    path='/w/index.php', query=[('title', 'Wikipedia:Strona_główna'), ('action', 'history')]
)
print(url1)

url2 = Pyjo.URL.new('http://pl.wikipedia.org').set(path='/wiki/Wikipedia:Strona_główna')
print(url2)

url3 = Pyjo.URL.new('http://żółwie.pl')
print(url3)

url4 = Pyjo.URL.new('http://localhost').set(userinfo='gęślą:jaźń')
print(url4)
