import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import any, get, post, under


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()


@any(['POST', 'PUT'], '/json/echo', {'format': None}, format=['json'])
def json_echo(c):
    c.respond_to(json={'json': c.req.json()})


@get('/accepts', {'format': None}, format=['html', 'json', 'txt', 'xml'])
def accepts(c):
    c.render(json={'best': c.accepts('html', 'json', 'txt')})


@get('/wants_json', {'format': None}, format=['json', 'xml'])
def wants_json(c):
    # Unlike Mojolicious: True and False, where Mojo has the references \1 and \0 of JSON booleans
    c.render(json={'wants_json': True if c.accepts('', 'json') else False})


under('/rest')


@get({'format': None}, format=['json', 'html', 'xml'])
def rest_get(c):
    c.respond_to(
        json=lambda c: c.render(json={'just': 'works'}),
        html=lambda c: c.render(data='<html><body>works'),
        xml=lambda c: c.render(data='<just>works</just>'),
    )


@post({'format': None}, format=['json', 'html', 'xml', 'png'])
def rest_post(c):
    c.respond_to(
        json={'json': {'just': 'works too'}},
        html={'text': '<html><body>works too'},
        xml={'data': '<just>works too</just>'},
        any={'text': 'works too', 'status': 201},
    )


t = Pyjo.Test.Pyjo.new()

with subtest('Hash without format'):
    t.post_ok('/json/echo', json={'hello': 'world'}).status_is(204).content_is('')

with subtest('Hash with "json" format'):
    (
        t.post_ok('/json/echo', {'Accept': 'application/json'}, json={'hello': 'world'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'hello': 'world'})
    )
    tx = t.ua.build_tx('PUT', '/json/echo', {'Accept': 'application/json'}, json={'hello': 'world'})
    t.request_ok(tx).status_is(200).content_type_is('application/json;charset=UTF-8').json_is({'hello': 'world'})

with subtest('Array with "json" format'):
    tx = t.ua.build_tx('PUT', '/json/echo', {'Accept': 'application/json'}, json=[1, 2, 3])
    t.request_ok(tx).status_is(200).content_type_is('application/json;charset=UTF-8').json_is([1, 2, 3])

with subtest('Nothing'):
    t.get_ok('/accepts').status_is(200).json_is({'best': 'html'})

with subtest('Unsupported'):
    t.get_ok('/accepts.xml').status_is(200).json_is({'best': None})

with subtest('"json" format'):
    t.get_ok('/accepts.json').status_is(200).json_is({'best': 'json'})

with subtest('"txt" query'):
    t.get_ok('/accepts?_format=txt').status_is(200).json_is({'best': 'txt'})

with subtest('Accept "txt"'):
    t.get_ok('/accepts', {'Accept': 'text/plain'}).status_is(200).json_is({'best': 'txt'})

with subtest('Accept "txt" with everything'):
    t.get_ok('/accepts.json?_format=txt', {'Accept': 'text/html'}).status_is(200).json_is({'best': 'txt'})

with subtest('Nothing'):
    t.get_ok('/wants_json').status_is(200).json_is({'wants_json': False})

with subtest('Unsupported'):
    t.get_ok('/wants_json.xml').status_is(200).json_is({'wants_json': False})

with subtest('Accept "json"'):
    t.get_ok('/wants_json', {'Accept': 'application/json'}).status_is(200).json_is({'wants_json': True})

with subtest('Ajax'):
    ajax = 'text/html;q=0.1,application/json'
    (
        t.get_ok('/accepts', {'Accept': ajax, 'X-Requested-With': 'XMLHttpRequest'})
        .status_is(200)
        .json_is({'best': 'json'})
    )

with subtest('Nothing'):
    t.get_ok('/rest').status_is(200).content_type_is('text/html;charset=UTF-8').text_is('html > body', 'works')

with subtest('"html" format'):
    t.get_ok('/rest.html').status_is(200).content_type_is('text/html;charset=UTF-8').text_is('html > body', 'works')

with subtest('Accept "html"'):
    (
        t.get_ok('/rest', {'Accept': 'text/html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works')
    )

with subtest('Accept "html" again'):
    (
        t.get_ok('/rest', {'Accept': 'Text/Html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works')
    )

with subtest('Accept "html" with format'):
    (
        t.get_ok('/rest.html', {'Accept': 'text/html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works')
    )

with subtest('Accept "html" with quality'):
    (
        t.get_ok('/rest', {'Accept': 'text/html;q=9'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works')
    )

with subtest('"html" query'):
    (
        t.get_ok('/rest?_format=html')
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works')
    )

with subtest('"html" format with query'):
    (
        t.get_ok('/rest.html?_format=html')
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works')
    )

with subtest('Accept "html" with query'):
    (
        t.get_ok('/rest?_format=html', {'Accept': 'text/html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works')
    )

with subtest('Accept "html" with everything'):
    (
        t.get_ok('/rest.html?_format=html', {'Accept': 'text/html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works')
    )

with subtest('"json" format'):
    (t.get_ok('/rest.json').status_is(200).content_type_is('application/json;charset=UTF-8').json_is({'just': 'works'}))

with subtest('Accept "json"'):
    (
        t.get_ok('/rest', {'Accept': 'application/json'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works'})
    )

with subtest('Accept "json" again'):
    (
        t.get_ok('/rest', {'Accept': 'APPLICATION/JSON'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works'})
    )

with subtest('Accept "json" with format'):
    (
        t.get_ok('/rest.json', {'Accept': 'application/json'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works'})
    )

with subtest('Accept "json" with quality'):
    (
        t.get_ok('/rest', {'Accept': 'application/json;q=9'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works'})
    )

with subtest('"json" query'):
    (
        t.get_ok('/rest?_format=json')
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works'})
    )

with subtest('"json" format with query'):
    (
        t.get_ok('/rest.json?_format=json')
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works'})
    )

with subtest('Accept "json" with query'):
    (
        t.get_ok('/rest?_format=json', {'Accept': 'application/json'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works'})
    )

with subtest('Accept "json" with everything'):
    (
        t.get_ok('/rest.json?_format=json', {'Accept': 'application/json'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works'})
    )

with subtest('"xml" format'):
    t.get_ok('/rest.xml').status_is(200).content_type_is('application/xml').text_is('just', 'works')

with subtest('Accept "xml"'):
    (
        t.get_ok('/rest', {'Accept': 'application/xml'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works')
    )

with subtest('Accept "xml" again'):
    (
        t.get_ok('/rest', {'Accept': 'APPLICATION/XML'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works')
    )

with subtest('Accept "xml" with format'):
    (
        t.get_ok('/rest.xml', {'Accept': 'application/xml'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works')
    )

with subtest('Accept "xml" with quality'):
    (
        t.get_ok('/rest', {'Accept': 'application/xml;q=9'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works')
    )

with subtest('"xml" query'):
    t.get_ok('/rest?_format=xml').status_is(200).content_type_is('application/xml').text_is('just', 'works')

with subtest('"xml" format with query'):
    t.get_ok('/rest.xml?_format=xml').status_is(200).content_type_is('application/xml').text_is('just', 'works')

with subtest('Accept "json" with query'):
    (
        t.get_ok('/rest?_format=xml', {'Accept': 'application/xml'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works')
    )

with subtest('Accept "json" with everything'):
    (
        t.get_ok('/rest.xml?_format=xml', {'Accept': 'application/xml'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works')
    )

with subtest('Unsupported accept'):
    t.get_ok('/rest', {'Accept': 'image/png'}).status_is(204).content_is('')

with subtest('Nothing'):
    t.post_ok('/rest').status_is(200).content_type_is('text/html;charset=UTF-8').text_is('html > body', 'works too')

with subtest('"html" format'):
    (
        t.post_ok('/rest.html')
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('Accept "html"'):
    (
        t.post_ok('/rest', {'Accept': 'text/html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('Accept "html" again'):
    (
        t.post_ok('/rest', {'Accept': 'Text/Html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('Accept "html" with format'):
    (
        t.post_ok('/rest.html', {'Accept': 'text/html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('Accept "html" with quality'):
    (
        t.post_ok('/rest', {'Accept': 'text/html;q=9'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('"html" query'):
    (
        t.post_ok('/rest?_format=html')
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('"html" format with query'):
    (
        t.post_ok('/rest.html?_format=html')
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('Accept html with query'):
    (
        t.post_ok('/rest?_format=html', {'Accept': 'text/html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('Accept "html" with everything'):
    (
        t.post_ok('/rest.html?_format=html', {'Accept': 'text/html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('"html" form'):
    (
        t.post_ok('/rest', form={'_format': 'html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('"html" format with form'):
    (
        t.post_ok('/rest.html', form={'_format': 'html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('Accept "html" with form'):
    (
        t.post_ok('/rest', {'Accept': 'text/html'}, form={'_format': 'html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('Accept "html" with everything, form alternative'):
    (
        t.post_ok('/rest.html', {'Accept': 'text/html'}, form={'_format': 'html'})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works too')
    )

with subtest('"json" format'):
    (
        t.post_ok('/rest.json')
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('Accept "json"'):
    (
        t.post_ok('/rest', {'Accept': 'application/json'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('Accept "json" again'):
    (
        t.post_ok('/rest', {'Accept': 'APPLICATION/JSON'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('Accept "json" with format'):
    (
        t.post_ok('/rest.json', {'Accept': 'application/json'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('Accept "json" with quality'):
    (
        t.post_ok('/rest', {'Accept': 'application/json;q=9'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('"json" query'):
    (
        t.post_ok('/rest?_format=json')
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('"json" format with query'):
    (
        t.post_ok('/rest.json?_format=json')
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('Accept "json" with query'):
    (
        t.post_ok('/rest?_format=json', {'Accept': 'application/json'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('Accept "json" with everything'):
    (
        t.post_ok('/rest.json?_format=json', {'Accept': 'application/json'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('"json" form'):
    (
        t.post_ok('/rest', form={'_format': 'json'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('"json" format with form'):
    (
        t.post_ok('/rest.json', form={'_format': 'json'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('Accept "json" with form'):
    (
        t.post_ok('/rest', {'Accept': 'application/json'}, form={'_format': 'json'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('Accept "json" with everything, form alternative'):
    (
        t.post_ok('/rest.json', {'Accept': 'application/json'}, form={'_format': 'json'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works too'})
    )

with subtest('"xml" format'):
    t.post_ok('/rest.xml').status_is(200).content_type_is('application/xml').text_is('just', 'works too')

with subtest('Accept "xml"'):
    (
        t.post_ok('/rest', {'Accept': 'application/xml'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works too')
    )

with subtest('Accept "xml" again'):
    (
        t.post_ok('/rest', {'Accept': 'APPLICATION/XML'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works too')
    )

with subtest('Accept "xml" with format'):
    (
        t.post_ok('/rest.xml', {'Accept': 'application/xml'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works too')
    )

with subtest('Accept "xml" with quality'):
    (
        t.post_ok('/rest', {'Accept': 'application/xml;q=9'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works too')
    )

with subtest('"xml" query'):
    t.post_ok('/rest?_format=xml').status_is(200).content_type_is('application/xml').text_is('just', 'works too')

with subtest('"xml" format with query'):
    (t.post_ok('/rest.xml?_format=xml').status_is(200).content_type_is('application/xml').text_is('just', 'works too'))

with subtest('Accept "json" with query'):
    (
        t.post_ok('/rest?_format=xml', {'Accept': 'application/xml'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works too')
    )

with subtest('Accept "json" with everything'):
    (
        t.post_ok('/rest.xml?_format=xml', {'Accept': 'application/xml'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works too')
    )

with subtest('"xml" form'):
    (
        t.post_ok('/rest', form={'_format': 'xml'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works too')
    )

with subtest('"xml" format with form'):
    (
        t.post_ok('/rest.xml', form={'_format': 'xml'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works too')
    )

with subtest('Accept "json" with form'):
    (
        t.post_ok('/rest', {'Accept': 'application/xml'}, form={'_format': 'xml'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works too')
    )

with subtest('Accept "json" with everything, form alternative'):
    (
        t.post_ok('/rest.xml', {'Accept': 'application/xml'}, form={'_format': 'xml'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works too')
    )

with subtest('Unsupported accept'):
    (
        t.post_ok('/rest', {'Accept': 'image/png'})
        .status_is(201)
        .content_type_is('text/html;charset=UTF-8')
        .content_is('works too')
    )

with subtest('Unsupported everything'):
    (
        t.post_ok('/rest.png?_format=jpg', {'Accept': 'image/whatever'})
        .status_is(201)
        .content_type_is('text/html;charset=UTF-8')
        .content_is('works too')
    )

with subtest('Unsupported format'):
    t.post_ok('/rest.png').status_is(201).content_type_is('text/html;charset=UTF-8').content_is('works too')

with subtest('Unsupported format and query'):
    (
        t.post_ok('/rest.png?_format=png')
        .status_is(201)
        .content_type_is('text/html;charset=UTF-8')
        .content_is('works too')
    )

with subtest('Does not exist'):
    t.get_ok('/nothing', {'Accept': 'image/png'}).status_is(404)

with subtest('Ajax'):
    ajax = 'text/html;q=0.1,application/xml'
    (
        t.get_ok('/rest', {'Accept': ajax, 'X-Requested-With': 'XMLHttpRequest'})
        .status_is(200)
        .content_type_is('application/xml')
        .text_is('just', 'works')
    )

with subtest('Chrome 64'):
    chrome = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    (
        t.get_ok('/rest.html', {'Accept': chrome})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works')
    )

with subtest('Chrome 11 with query'):
    chrome = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    (
        t.get_ok('/rest?_format=html', {'Accept': chrome})
        .status_is(200)
        .content_type_is('text/html;charset=UTF-8')
        .text_is('html > body', 'works')
    )

with subtest('jQuery 1.8'):
    jquery = 'application/json, text/javascript, */*; q=0.01'
    (
        t.get_ok('/rest', {'Accept': jquery, 'X-Requested-With': 'XMLHttpRequest'})
        .status_is(200)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'just': 'works'})
    )

done_testing()
