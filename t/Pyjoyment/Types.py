import Pyjoyment
import Pyjoyment.Types

from Pyjo.Test import *


t = Pyjoyment.Types.new()

with subtest('Basic functionality'):
    is_ok(t.type('json'), 'application/json;charset=UTF-8', 'right type')

    # Not in Mojolicious: YAML and TOML
    is_ok(t.type('yaml'), 'application/yaml;charset=UTF-8', 'right type')
    is_ok(t.type('toml'), 'application/toml;charset=UTF-8', 'right type')
    is_ok(t.type('foo'), None, 'no type')
    t.type('foo', 'foo/bar')
    is_ok(t.type('foo'), 'foo/bar', 'right type')
    t.type('BAR', 'bar/baz')
    is_ok(t.type('Bar'), 'bar/baz', 'right type')

with subtest('Detect common MIME types'):
    is_deeply_ok(t.detect('text/cache-manifest'), ['appcache'], 'right formats')
    is_deeply_ok(t.detect('application/atom+xml'), ['atom'], 'right formats')
    is_deeply_ok(t.detect('application/octet-stream'), ['bin'], 'right formats')
    is_deeply_ok(t.detect('text/css'), ['css'], 'right formats')
    is_deeply_ok(t.detect('image/gif'), ['gif'], 'right formats')
    is_deeply_ok(t.detect('application/x-gzip'), ['gz'], 'right formats')
    is_deeply_ok(t.detect('text/html'), ['htm', 'html'], 'right formats')
    is_deeply_ok(t.detect('image/x-icon'), ['ico'], 'right formats')
    is_deeply_ok(t.detect('image/jpeg'), ['jpeg', 'jpg'], 'right formats')
    is_deeply_ok(t.detect('application/javascript'), ['js'], 'right formats')
    is_deeply_ok(t.detect('application/json'), ['json'], 'right formats')
    is_deeply_ok(t.detect('audio/mpeg'), ['mp3'], 'right formats')
    is_deeply_ok(t.detect('video/mp4'), ['mp4'], 'right formats')
    is_deeply_ok(t.detect('audio/ogg'), ['ogg'], 'right formats')
    is_deeply_ok(t.detect('video/ogg'), ['ogv'], 'right formats')
    is_deeply_ok(t.detect('application/pdf'), ['pdf'], 'right formats')
    is_deeply_ok(t.detect('image/png'), ['png'], 'right formats')
    is_deeply_ok(t.detect('application/rss+xml'), ['rss'], 'right formats')
    is_deeply_ok(t.detect('text/event-stream'), ['sse'], 'right formats')
    is_deeply_ok(t.detect('image/svg+xml'), ['svg'], 'right formats')
    is_deeply_ok(t.detect('font/ttf'), ['ttf'], 'right formats')
    is_deeply_ok(t.detect('text/plain'), ['txt'], 'right formats')
    is_deeply_ok(t.detect('video/webm'), ['webm'], 'right formats')
    is_deeply_ok(t.detect('font/woff'), ['woff'], 'right formats')
    is_deeply_ok(t.detect('font/woff2'), ['woff2'], 'right formats')
    is_deeply_ok(t.detect('application/xml'), ['xml'], 'right formats')
    is_deeply_ok(t.detect('text/xml'), ['xml'], 'right formats')
    is_deeply_ok(t.detect('application/zip'), ['zip'], 'right format')

    # Not in Mojolicious: YAML, of RFC 9512, and the types that it had before
    is_deeply_ok(t.detect('application/yaml'), ['yaml'], 'right format')
    is_deeply_ok(t.detect('text/yaml'), ['yaml'], 'right format')
    is_deeply_ok(t.detect('application/x-yaml'), ['yaml'], 'right format')
    is_deeply_ok(t.detect('text/x-yaml'), ['yaml'], 'right format')
    # Not in Mojolicious: TOML
    is_deeply_ok(t.detect('application/toml'), ['toml'], 'right format')

with subtest('Detect special cases'):
    is_deeply_ok(t.detect('Application/Xml'), ['xml'], 'right formats')
    is_deeply_ok(t.detect(' Text/Xml '), ['xml'], 'right formats')
    is_deeply_ok(t.detect('APPLICATION/XML'), ['xml'], 'right formats')
    is_deeply_ok(t.detect('TEXT/XML'), ['xml'], 'right formats')
    is_deeply_ok(t.detect('text/html;q=0.9'), ['htm', 'html'], 'right formats')
    is_deeply_ok(t.detect('TEXT/HTML;Q=0.9'), ['htm', 'html'], 'right formats')
    is_deeply_ok(t.detect('text/event-stream, application/json'), ['json', 'sse'], 'right formats')

with subtest('Alternatives'):
    t.type('json', ['application/json', 'text/x-json'])
    is_ok(t.mapping['json'][0], 'application/json', 'right type')
    is_ok(t.mapping['json'][1], 'text/x-json', 'right type')
    is_ok(len(t.mapping['json']), 2, 'no type')
    is_deeply_ok(t.mapping['htm'], ['text/html'], 'right type')
    is_deeply_ok(t.mapping['html'], ['text/html;charset=UTF-8'], 'right type')
    is_deeply_ok(t.detect('application/json'), ['json'], 'right formats')
    is_deeply_ok(t.detect('text/x-json'), ['json'], 'right formats')
    is_deeply_ok(t.detect('TEXT/X-JSON;q=0.1'), ['json'], 'right formats')
    is_deeply_ok(t.detect('APPLICATION/JsoN'), ['json'], 'right formats')
    is_deeply_ok(t.detect('text/html'), ['htm', 'html'], 'right formats')
    is_ok(t.type('json'), 'application/json', 'right type')
    is_ok(t.type('htm'), 'text/html', 'right type')
    is_ok(t.type('html'), 'text/html;charset=UTF-8', 'right type')

with subtest('Prioritize'):
    is_deeply_ok(t.detect('text/plain'), ['txt'], 'right formats')
    is_deeply_ok(t.detect('text/plain,text/html'), ['htm', 'html', 'txt'], 'right formats')
    is_deeply_ok(t.detect('TEXT/HTML; q=0.8 '), ['htm', 'html'], 'right formats')
    is_deeply_ok(t.detect('TEXT/HTML  ;  q  =  0.8 '), ['htm', 'html'], 'right formats')
    is_deeply_ok(t.detect('TEXT/HTML;Q=0.8,text/plain;Q=0.9'), ['txt', 'htm', 'html'], 'right formats')
    is_deeply_ok(t.detect(' TEXT/HTML , text/plain;Q=0.9'), ['htm', 'html', 'txt'], 'right formats')
    is_deeply_ok(t.detect('text/plain;q=0.5, text/xml, application/xml;q=0.1'), ['xml', 'txt', 'xml'], 'right formats')
    is_deeply_ok(t.detect('application/json, text/javascript, */*; q=0.01'), ['json'], 'right formats')

with subtest('File types'):
    is_ok(t.file_type('foo/bar.png'), 'image/png', 'right type')
    is_ok(t.file_type('foo/bar.js'), 'application/javascript', 'right type')
    is_ok(t.file_type('foo/bar'), None, 'no type')
    is_ok(t.file_type('foo/.vimrc'), None, 'no type')
    is_ok(t.file_type('foo/.js'), None, 'no type')
    is_ok(t.file_type('foo/.test.js'), 'application/javascript', 'right type')
    is_ok(t.file_type('.vimrc'), None, 'no type')
    is_ok(t.file_type('.js'), None, 'no type')
    is_ok(t.file_type('.test.js'), 'application/javascript', 'right type')

with subtest('Content types'):
    c = Pyjoyment.new().build_controller()
    t.content_type(c, ext='json')
    is_ok(c.res.headers.content_type, 'application/json', 'right type')
    t.content_type(c, ext='txt')
    is_ok(c.res.headers.content_type, 'application/json', 'type not changed')
    c.res.headers.remove('Content-Type')
    t.content_type(c, ext='html')
    is_ok(c.res.headers.content_type, 'text/html;charset=UTF-8', 'right type')
    c.res.headers.remove('Content-Type')
    t.content_type(c, ext='unknown')
    is_ok(c.res.headers.content_type, 'application/octet-stream', 'right type')
    c.res.headers.remove('Content-Type')
    t.content_type(c, file='foo/bar.png')
    is_ok(c.res.headers.content_type, 'image/png', 'right type')

done_testing()
