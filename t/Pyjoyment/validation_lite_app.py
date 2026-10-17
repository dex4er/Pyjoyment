"""
__DATA__

@@ index.html.ep
% if validation().has_error('foo') {
  <div>
    %= validation().error('foo')[0]
    %= validation().error('foo')[1]
  </div>
% }
%= form_for('index', begin
  %= label_for('foo', '<Foo>', **{'class': 'custom'})
  %= text_field('foo', **{'class': 'custom'}, id='foo')
  %= text_area('bar')
  %= label_for('baz', begin
    Baz
  %= end, **{'class': 'custom'})
  %= select_field('baz', ['yada', 'yada'], id='baz')
  %= password_field('yada')
%= end)

@@ upload.html.ep
%= form_for('upload', begin
  %= file_field('foo')
  %= submit_button()
%= end)

@@ forgery.html.ep
%= form_for('forgery', begin
  % if validation().has_error('csrf_token') {
    %= 'Wrong or missing CSRF token!'
  % }
  %= csrf_field()
  %= text_field('foo')
%= end)
%= csrf_button_to('Root', '/')
"""

import Pyjo.Asset.Memory
import Pyjo.Test.Pyjo
import Pyjo.Upload
import Pyjoyment.Validator.Validation

from Pyjo.Test import *
from Pyjoyment.Lite import any, app

import re


# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Not in Mojolicious: the templates of the DATA section are in the docstring, as the requests come before the end of
# the script

# Custom check
app.validator.add_check('two', lambda v, name, value, *args: None if len(value) == 2 else f'e:{name}')


@any('/', 'index')
def index(c):
    v = c.validation()
    if not v.has_data:
        return c.render()

    v.required('foo').two().in_('☃☃')
    v.optional('bar').two()
    v.optional('baz').two()
    v.optional('yada').two()


@any('/upload')
def upload(c):
    v = c.validation()
    if not v.has_data:
        return c.render()
    v.required('foo').upload()


@any('/forgery')
def forgery(c):
    v = c.validation()
    if not v.has_data:
        return c.render()
    v.csrf_protect().required('foo')


t = Pyjo.Test.Pyjo.new()

with subtest('Required and optional values'):
    v = t.app.validation().set(input={'foo': 'bar', 'baz': 'yada'})
    is_deeply_ok(v.passed, [], 'no names')
    is_deeply_ok(v.failed, [], 'no names')
    is_ok(v.param('foo'), None, 'no value')
    is_deeply_ok(v.every_param('foo'), [], 'no values')
    ok(v.required('foo').is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')
    is_ok(v.param(), 'bar', 'right value')
    is_ok(v.param('foo'), 'bar', 'right value')
    is_deeply_ok(v.every_param(), ['bar'], 'right values')
    is_deeply_ok(v.every_param('foo'), ['bar'], 'right values')
    is_deeply_ok(v.passed, ['foo'], 'right names')
    ok(not v.has_error(), 'no error')
    ok(v.optional('baz').is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': 'bar', 'baz': 'yada'}, 'right result')
    is_ok(v.param('baz'), 'yada', 'right value')
    is_deeply_ok(v.passed, ['baz', 'foo'], 'right names')
    ok(not v.has_error(), 'no error')
    ok(not v.optional('does_not_exist').is_valid(), 'not valid')
    is_deeply_ok(v.output, {'foo': 'bar', 'baz': 'yada'}, 'right result')
    ok(not v.has_error(), 'no error')
    ok(not v.required('does_not_exist').is_valid(), 'not valid')
    is_deeply_ok(v.output, {'foo': 'bar', 'baz': 'yada'}, 'right result')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('does_not_exist'), ['required'], 'right error')
    v = t.app.validation().set(input={'foo': [], 'bar': ['a'], 'baz': None, 'yada': [None]})
    ok(not v.optional('foo').is_valid(), 'not valid')
    is_deeply_ok(v.output, {}, 'right result')
    ok(not v.has_error(), 'no error')
    ok(not v.optional('baz').is_valid(), 'not valid')
    is_deeply_ok(v.output, {}, 'right result')
    ok(not v.has_error(), 'no error')
    ok(not v.optional('yada').is_valid(), 'not valid')
    is_deeply_ok(v.output, {}, 'right result')
    ok(not v.has_error(), 'no error')
    ok(v.optional('bar').is_valid(), 'valid')
    is_deeply_ok(v.output, {'bar': 'a'}, 'right result')
    ok(not v.in_('c').is_valid(), 'not valid')
    is_deeply_ok(v.output, {}, 'right result')
    ok(v.has_error(), 'has error')

with subtest('Empty string'):
    v = t.app.validation().set(input={'foo': ''})
    ok(v.optional('foo').is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': ''}, 'right result')

with subtest('Equal to'):
    v = t.app.validation().set(input={'foo': 'bar', 'baz': 'bar', 'yada': 'yada'})
    ok(v.optional('foo').equal_to('baz').is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')
    ok(not v.has_error(), 'no error')
    ok(not v.optional('baz').equal_to('does_not_exist').is_valid(), 'not valid')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('baz'), ['equal_to', 1, 'does_not_exist'], 'right error')
    ok(not v.optional('yada').equal_to('foo').is_valid(), 'not valid')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('yada'), ['equal_to', 1, 'foo'], 'right error')
    is_deeply_ok(v.failed, ['baz', 'yada'], 'right names')

with subtest('In'):
    v = t.app.validation().set(input={'foo': ['bar', 'whatever'], 'baz': ['yada', 'ohoh']})
    ok(v.required('foo').in_('23', 'bar', 'whatever').is_valid(), 'valid')
    is_deeply_ok(v.every_param('foo'), ['bar', 'whatever'], 'right results')
    is_ok(v.param('foo'), 'whatever', 'right result')
    is_deeply_ok(v.output, {'foo': ['bar', 'whatever']}, 'right result')
    ok(not v.has_error(), 'no error')
    ok(not v.required('baz').in_('yada', 'whatever').is_valid(), 'not valid')
    is_deeply_ok(v.output, {'foo': ['bar', 'whatever']}, 'right result')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('baz'), ['in', 1, 'yada', 'whatever'], 'right error')
    is_deeply_ok(v.failed, ['baz'], 'right names')

with subtest('Like'):
    v = t.app.validation().set(input={'foo': 'bar', 'baz': 'yada'})
    ok(v.required('foo').like(re.compile(r'^b')).is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')
    ok(not v.has_error(), 'no error')
    re_ = re.compile(r'ar$')
    ok(not v.required('baz').like(re_).is_valid(), 'not valid')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('baz'), ['like', 1, re_], 'right error')

with subtest('Num'):
    v = t.app.validation().set(input={'foo': 23, 'bar': 0, 'baz': 'fail'})
    ok(v.required('foo').num().is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': 23}, 'right result')
    ok(v.required('bar').num().is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': 23, 'bar': 0}, 'right result')
    ok(not v.has_error(), 'no error')
    ok(not v.required('baz').num().is_valid(), 'not valid')
    is_deeply_ok(v.error('baz'), ['num', 1], 'right error')
    is_deeply_ok(v.failed, ['baz'], 'right names')
    v = t.app.validation().set(input={'foo': 23})
    ok(v.required('foo').num(22, 24).is_valid(), 'valid')
    v = t.app.validation().set(input={'foo': 23})
    ok(v.required('foo').num(23, 24).is_valid(), 'valid')
    v = t.app.validation().set(input={'foo': 23})
    ok(v.required('foo').num(22, 23).is_valid(), 'valid')
    v = t.app.validation().set(input={'foo': 23})
    ok(not v.required('foo').num(24, 25).is_valid(), 'not valid')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('foo'), ['num', 1, 24, 25], 'right error')
    v = t.app.validation().set(input={'foo': 23})
    ok(v.required('foo').num(22, None).is_valid(), 'valid')
    v = t.app.validation().set(input={'foo': 23})
    ok(v.required('foo').num(23, None).is_valid(), 'valid')
    v = t.app.validation().set(input={'foo': 23})
    ok(not v.required('foo').num(24, None).is_valid(), 'not valid')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('foo'), ['num', 1, 24, None], 'right error')
    v = t.app.validation().set(input={'foo': 23})
    ok(v.required('foo').num(None, 24).is_valid(), 'valid')
    v = t.app.validation().set(input={'foo': 23})
    ok(v.required('foo').num(None, 23).is_valid(), 'valid')
    v = t.app.validation().set(input={'foo': 23})
    ok(not v.required('foo').num(None, 22).is_valid(), 'not valid')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('foo'), ['num', 1, None, 22], 'right error')
    v = t.app.validation().set(input={'foo': -5})
    ok(v.required('foo').num().is_valid(), 'valid')
    ok(v.required('foo').num(None, -1).is_valid(), 'valid')
    ok(v.required('foo').num(-10, 10).is_valid(), 'valid')
    ok(v.required('foo').num(-20, None).is_valid(), 'valid')

with subtest('Size'):
    v = t.app.validation().set(input={'foo': 'bar', 'baz': 'yada', 'yada': 'yada'})
    ok(v.required('foo').size(1, 3).is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')
    ok(not v.has_error(), 'no error')
    ok(not v.required('baz').size(1, 3).is_valid(), 'not valid')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('baz'), ['size', 1, 1, 3], 'right error')
    ok(not v.required('yada').size(5, 10).is_valid(), 'not valid')
    is_ok(v.topic, 'yada', 'right topic')
    ok(v.has_error('baz'), 'has error')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('yada'), ['size', 1, 5, 10], 'right error')
    ok(v.required('foo').size(1, None).is_valid(), 'valid')
    ok(not v.required('foo').size(4, None).is_valid(), 'not valid')
    ok(v.required('foo').size(None, 4).is_valid(), 'valid')
    ok(v.required('foo').size(None, 3).is_valid(), 'valid')
    ok(not v.required('foo').size(None, 2).is_valid(), 'not valid')

with subtest('Upload'):
    v = t.app.validation().set(
        input={
            'foo': Pyjo.Upload.new(),
            'bar': [Pyjo.Upload.new(), Pyjo.Upload.new()],
            'baz': [Pyjo.Upload.new(), 'just another test'],
        }
    )
    ok(v.required('foo').upload().is_valid(), 'valid')
    ok(v.required('bar').upload().is_valid(), 'valid')
    ok(v.required('baz').is_valid(), 'valid')
    ok(not v.has_error(), 'no error')
    ok(not v.upload().is_valid(), 'not valid')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('baz'), ['upload', 1], 'right error')
    is_deeply_ok(v.failed, ['baz'], 'right names')

with subtest('Upload size'):
    v = t.app.validation().set(
        input={
            'foo': [Pyjo.Upload.new(asset=Pyjo.Asset.Memory.new().add_chunk(b'valid'))],
            'bar': [Pyjo.Upload.new(asset=Pyjo.Asset.Memory.new().add_chunk(b'not valid'))],
        }
    )
    ok(v.required('foo').upload().size(1, 6).is_valid(), 'valid')
    ok(not v.has_error(), 'no error')
    ok(not v.required('bar').upload().size(1, 6).is_valid(), 'not valid')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('bar'), ['size', 1, 1, 6], 'right error')
    is_deeply_ok(v.failed, ['bar'], 'right names')

with subtest('Trim'):
    v = t.app.validation().set(input={'foo': ' bar', 'baz': ['  0 ', 1]})
    ok(v.required('foo', 'trim').in_('bar').is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')
    ok(not v.optional('missing', 'trim').is_valid(), 'not valid')
    ok(v.optional('baz', 'trim').like(re.compile(r'^\d$')).is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': 'bar', 'baz': ['0', '1']}, 'right result')

    v = t.app.validation().set(input={'nothing': '  ', 'more': [None]})
    ok(v.required('nothing', 'trim').is_valid(), 'valid')
    is_deeply_ok(v.output, {'nothing': ''}, 'right result')
    ok(v.required('nothing').is_valid(), 'valid')
    is_deeply_ok(v.output, {'nothing': '  '}, 'right result')
    ok(not v.optional('more', 'trim').is_valid(), 'not valid')
    is_deeply_ok(v.output, {'nothing': '  '}, 'right result')

with subtest('Not empty'):
    v = t.app.validation().set(input={'foo': 'bar', 'baz': ''})
    ok(v.required('foo', 'not_empty').in_('bar').is_valid(), 'valid')
    ok(not v.required('baz', 'not_empty').is_valid(), 'not valid')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('baz'), ['required'], 'right error')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')

    v = t.app.validation().set(input={'foo': [' bar'], 'baz': ['', '  ', None]})
    ok(v.optional('foo', 'trim', 'not_empty').is_valid(), 'valid')
    ok(not v.optional('baz', 'trim', 'not_empty').is_valid(), 'not valid')
    ok(not v.has_error(), 'no error')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')

with subtest('Comma separated'):
    v = t.app.validation().set(input={'foo': 'bar , baz,yada', 'baz': ['one, two', 'three']})
    ok(v.required('foo', 'comma_separated').is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': ['bar', 'baz', 'yada']}, 'right result')
    ok(v.optional('baz', 'comma_separated').is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': ['bar', 'baz', 'yada'], 'baz': ['one', 'two', 'three']}, 'right result')

    v = t.app.validation().set(input={'foo': ['One,, Two,', 'Three']})
    ok(v.required('foo', 'comma_separated').is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': ['One', '', 'Two', '', 'Three']}, 'right result')

    v = t.app.validation().set(input={'foo': ['one,, two,', 'three']})
    ok(v.required('foo', 'comma_separated', 'trim', 'not_empty').is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': ['one', 'two', 'three']}, 'right result')

with subtest('Custom filter'):
    t.app.validator.add_filter('quote', lambda v, name, value: f'{name}="{value}"')
    v = t.app.validation().set(input={'foo': [' bar', 'baz']})
    ok(v.required('foo', 'trim', 'quote').like(re.compile(r'"')).is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': ['foo="bar"', 'foo="baz"']}, 'right result')

with subtest('Multiple empty values'):
    v = t.app.validation()
    ok(not v.has_data, 'no data')
    v.input = {'foo': ['', 'bar', ''], 'bar': ['', 'baz', None]}
    ok(v.has_data, 'has data')
    ok(v.required('foo').is_valid(), 'valid')
    ok(not v.required('bar').is_valid(), 'not valid')
    is_deeply_ok(v.output, {'foo': ['', 'bar', '']}, 'right result')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('bar'), ['required'], 'right error')

with subtest('0'):
    v = t.app.validation().set(input={'0': 0})
    ok(v.has_data, 'has data')
    ok(v.required('0').size(1, 1).is_valid(), 'valid')
    is_deeply_ok(v.output, {'0': 0}, 'right result')
    is_ok(v.param('0'), 0, 'right value')

with subtest('Custom error'):
    v = t.app.validation().set(input={'foo': 'bar'})
    ok(not v.required('foo').has_error(), 'no error')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')
    ok(v.error('foo', ['custom_check']).has_error(), 'has error')
    is_deeply_ok(v.output, {}, 'right result')
    is_deeply_ok(v.size(1, 2).error('foo'), ['custom_check'], 'right error')

with subtest('CSRF protection'):
    # Masked token with an all-zero mask, so it unmasks to the session token
    session = 'a' * 40
    token = ('0' * 40) + session

    v = t.app.validation().set(input={'foo': 'bar'}).csrf_protect()
    ok(v.has_data, 'has data')
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('csrf_token'), ['csrf_protect'], 'right error')
    v = t.app.validation().set(input={'csrf_token': token})
    ok(v.has_data, 'has data')
    ok(v.csrf_protect().has_error(), 'has error')
    ok(v.has_data, 'has data')
    is_deeply_ok(v.error('csrf_token'), ['csrf_protect'], 'right error')
    v = t.app.validation().set(input={'csrf_token': token, 'foo': 'bar'}, csrf_token='b' * 40).csrf_protect()
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('csrf_token'), ['csrf_protect'], 'right error')
    v = t.app.validation().set(input={'csrf_token': session, 'foo': 'bar'}, csrf_token=session).csrf_protect()
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('csrf_token'), ['csrf_protect'], 'right error')
    tampered = re.sub(r'.$', 'f', token)
    v = t.app.validation().set(input={'csrf_token': tampered, 'foo': 'bar'}, csrf_token=session).csrf_protect()
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('csrf_token'), ['csrf_protect'], 'right error')
    v = t.app.validation().set(input={'csrf_token': token, 'foo': 'bar'}, csrf_token=session).csrf_protect()
    ok(not v.has_error(), 'no error')
    ok(v.required('foo').is_valid(), 'valid')
    is_deeply_ok(v.output, {'foo': 'bar'}, 'right result')
    v = t.app.validation().set(input={'csrf_token': [token, token]}, csrf_token=session).csrf_protect()
    ok(v.has_error(), 'has error')
    is_deeply_ok(v.error('csrf_token'), ['csrf_protect'], 'right error')

with subtest('Missing method and function (AUTOLOAD)'):
    package = 'Pyjoyment.Validator.Validation.Pyjoyment_Validator_Validation'
    try:
        t.app.validation().missing
    except AttributeError as e:
        like_ok(str(e), rf'^Can\'t locate object method "missing" via package "{re.escape(package)}"', 'right error')
    try:
        Pyjoyment.Validator.Validation.missing()
    except AttributeError as e:
        like_ok(str(e), r"^module 'Pyjoyment.Validator.Validation' has no attribute 'missing'", 'right error')

with subtest('No validation'):
    (
        t.get_ok('/')
        .status_is(200)
        .element_exists_not('div:root')
        .text_is('label[for="foo"]', '<Foo>')
        .element_exists('input[type="text"]')
        .element_exists('textarea')
        .text_like('label[for="baz"]', r'Baz')
        .element_exists('select')
        .element_exists('input[type="password"]')
    )

with subtest('Successful validation'):
    (
        t.get_ok('/', form={'foo': '☃☃'})
        .status_is(200)
        .element_exists_not('div:root')
        .text_is('label[for="foo"]', '<Foo>')
        .element_exists('input[type="text"]')
        .element_exists('textarea')
        .text_like('label[for="baz"]', r'Baz')
        .element_exists('select')
        .element_exists('input[type="password"]')
    )

with subtest('Validation failed for required fields'):
    (
        t.post_ok('/', form={'foo': 'no'})
        .status_is(200)
        .text_like('div:root', (r'in.+1', 's'))
        .text_is('label.custom.field-with-error[for="foo"]', '<Foo>')
        .element_exists('input.custom.field-with-error[type="text"][value="no"]')
        .element_exists_not('textarea.field-with-error')
        .element_exists_not('label.custom.field-with-error[for="baz"]')
        .element_exists_not('select.field-with-error')
        .element_exists_not('input.field-with-error[type="password"]')
        .element_count_is('.field-with-error', 2)
        .element_count_is('.field-with-error', 2, 'with description')
    )

with subtest('Successful file upload'):
    t.post_ok('/upload', form={'foo': {'content': 'bar', 'filename': 'test.txt'}}).element_exists_not(
        '.field-with-error'
    )

with subtest('Successful file upload (multiple files)'):
    t.post_ok(
        '/upload',
        form={
            'foo': [
                {'content': 'First test file content', 'filename': 'one.txt'},
                {'content': 'Second test file content', 'filename': 'two.txt'},
            ]
        },
    ).element_exists_not('.field-with-error')

with subtest('Failed file upload'):
    t.post_ok('/upload', form={'foo': 'bar'}).element_exists('.field-with-error')

with subtest('Failed file upload (multiple files)'):
    t.post_ok('/upload', form={'foo': ['one', 'two']}).element_exists('.field-with-error')

with subtest('Missing CSRF token'):
    (
        t.get_ok('/forgery', form={'foo': 'bar'})
        .status_is(200)
        .content_like(r'Wrong or missing CSRF token!')
        .element_exists('[value=bar]')
        .element_exists_not('.field-with-error')
    )

with subtest('Correct CSRF token'):
    token = t.ua.get('/forgery').res.dom().at('[name=csrf_token]').val
    (
        t.post_ok('/forgery', form={'csrf_token': token, 'foo': 'bar'})
        .status_is(200)
        .content_unlike(r'Wrong or missing CSRF token!')
        .element_exists('[value=bar]')
        .element_exists_not('.field-with-error')
        .element_count_is('[name=csrf_token]', 2)
        .element_count_is('form', 2)
        .element_exists('form > input[name=csrf_token] + input[type=submit]')
    )
    isnt_ok(
        t.tx.res.dom().find('[name=csrf_token]')[0].val,
        t.tx.res.dom().find('[name=csrf_token]')[1].val,
        'different masked tokens',
    )

with subtest('Different masked CSRF token for every request'):
    first = t.ua.get('/forgery').res.dom().at('[name=csrf_token]').val
    second = t.ua.get('/forgery').res.dom().at('[name=csrf_token]').val
    isnt_ok(first, second, 'different tokens')
    like_ok(first, r'^[0-9a-f]{80}$', 'token is masked')
    like_ok(second, r'^[0-9a-f]{80}$', 'token is masked')
    t.post_ok('/forgery', form={'csrf_token': first, 'foo': 'bar'}).status_is(200).content_unlike(
        r'Wrong or missing CSRF token!'
    )
    t.post_ok('/forgery', form={'csrf_token': second, 'foo': 'bar'}).status_is(200).content_unlike(
        r'Wrong or missing CSRF token!'
    )

with subtest('Correct CSRF token (header)'):
    token = t.ua.get('/forgery').res.dom().at('[name=csrf_token]').val
    (
        t.post_ok('/forgery', {'X-CSRF-Token': token}, form={'foo': 'bar'})
        .status_is(200)
        .content_unlike(r'Wrong or missing CSRF token!')
        .element_exists('[value=bar]')
        .element_exists_not('.field-with-error')
    )

with subtest('Wrong CSRF token (header)'):
    (
        t.post_ok('/forgery', {'X-CSRF-Token': 'abc'}, form={'foo': 'bar'})
        .status_is(200)
        .content_like(r'Wrong or missing CSRF token!')
        .element_exists('[value=bar]')
        .element_exists_not('.field-with-error')
    )

with subtest('Missing CSRF token and form'):
    (
        t.get_ok('/forgery')
        .status_is(200)
        .content_unlike(r'Wrong or missing CSRF token!')
        .element_exists_not('.field-with-error')
    )

with subtest('Correct CSRF token and missing form'):
    token = t.ua.get('/forgery').res.dom().at('[name=csrf_token]').val
    (
        t.post_ok('/forgery', {'X-CSRF-Token': token})
        .status_is(200)
        .content_unlike(r'Wrong or missing CSRF token!')
        .element_exists('.field-with-error')
    )

with subtest('Failed validation for all fields (with custom helper)'):

    @t.app.helper('tag_with_error')
    def tag_with_error(c, tag, content=None, /, **attrs):
        attrs['class'] = f'{attrs["class"]} my-field-with-error' if attrs.get('class') else 'my-field-with-error'
        return c.tag(tag, content, **attrs)

    (
        t.get_ok('/?foo=too_long&bar=too_long_too&baz=way_too_long&yada=whatever')
        .status_is(200)
        .text_like('div:root', (r'two.+e:foo', 's'))
        .text_is('label.custom.my-field-with-error[for="foo"]', '<Foo>')
        .element_exists('input.custom.my-field-with-error[type="text"]')
        .element_exists('textarea.my-field-with-error')
        .text_like('label.custom.my-field-with-error[for="baz"]', r'Baz')
        .element_exists('select.my-field-with-error')
        .element_exists('input.my-field-with-error[type="password"]')
    )

done_testing()
