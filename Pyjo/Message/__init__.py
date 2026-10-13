"""
Pyjo.Message - HTTP message base class
======================================
::

    import Pyjo.Message

    class MyMessage(Pyjo.Message.object):

        def cookies(self):
            ...

        def extract_start_line(self, buf):
            ...

        def get_start_line_chunk(self):
            ...

:mod:`Pyjo.Message` is an abstract base class for HTTP messages based on
:rfc:`7230`,
:rfc:`7231` and
:rfc:`2388`.

Events
------

:mod:`Pyjo.Message` inherits all events from :mod:`Pyjo.EventEmitter` and can emit
the following new ones.

finish
~~~~~~
::

    @msg.on
    def finish(msg):
        ...

Emitted after message building or parsing is finished. ::

    from Pyjo.Util import steady_time
    before = steady_time()

    @msg.on
    def finish(msg):
        msg.headers.header('X-Parser-Time', int(steady_time() - before))

progress
~~~~~~~~
::

    @msg.on
    def progress(msg, state, offset):
        ...

Emitted when message building or parsing makes progress. ::

    # Building
    @msg.on
    def progress(msg, state, offset):
        print("Building {0} at offset {1}".format(state, offset))

    # Parsing
    @msg.on
    def progress(msg, state, offset):
        length = msg.headers.content_length
        if length:
            size = msg.content.progress
            print("Progress: {0}%".format(100 if size == length
                                          else int(size / (length / 100))))

Classes
-------
"""

import Pyjo.Asset.Memory
import Pyjo.Content.Single
import Pyjo.DOM
import Pyjo.EventEmitter
import Pyjo.JSON.Pointer
import Pyjo.Parameters
import Pyjo.Upload

from Pyjo.JSON import j
from Pyjo.Regexp import r
from Pyjo.Util import convert, decode, getenv, not_implemented, notnone, u


re_filename = r(r'[; ]filename="((?:\\"|[^"])*)"')
re_name = r(r'[; ]name="((?:\\"|[^;"])*)"')


class Pyjo_Message(Pyjo.EventEmitter.object):
    """
    :mod:`Pyjo.Message` inherits all attributes and methods from
    :mod:`Pyjo.EventEmitter` and implements the following new ones.
    """

    def __init__(self, **kwargs):
        super().__init__()

        self.content = notnone(kwargs.get('content'), lambda: Pyjo.Content.Single.new())
        """::

            content = msg.content
            msg.content = Pyjo.Content.Single.new()

        Message content, defaults to a :mod:`Pyjo.Content.Single` object.
        """

        self.default_charset = kwargs.get('default_charset', 'utf-8')
        """::

            charset = msg.default_charset
            msg.default_charset = 'utf-8'

        Default charset used by :attr:`text` and to extract data from
        ``application/x-www-form-urlencoded`` or ``multipart/form-data`` message body,
        defaults to ``utf-8``.
        """

        self.max_line_size = notnone(
            kwargs.get('max_line_size'), lambda: convert(getenv('PYJO_MAX_LINE_SIZE'), int) or 8192
        )
        """::

            size = msg.max_line_size
            msg.max_line_size = 8192

        Maximum start-line size in bytes, defaults to the value of the
        ``PYJO_MAX_LINE_SIZE`` environment variable or ``8192`` (8KB).
        """

        self.max_message_size = notnone(
            kwargs.get('max_message_size'), lambda: notnone(convert(getenv('PYJO_MAX_MESSAGE_SIZE'), int), 16777216)
        )
        """::

            size = msg.max_message_size
            msg.max_message_size = 16777216

        Maximum message size in bytes, defaults to the value of the
        ``PYJO_MAX_MESSAGE_SIZE`` environment variable or ``16777216`` (16MB). Setting
        the value to ``0`` will allow messages of indefinite size. Note that increasing
        this value can also drastically increase memory usage, should you for example
        attempt to parse an excessively large message body with the :attr:`body_params`,
        :meth:`dom` or :meth:`json` methods.
        """

        self.version = kwargs.get('version', '1.1')
        """::

            version = msg.version
            msg.version = '1.1'

        HTTP version of message, defaults to ``1.1``.
        """

        self._body_params = None
        self._buffer = bytearray()
        self._cookies = {}
        self._dom = None
        self._error = {}
        self._finished = False
        self._fixed = False
        self._json = None
        self._limited = False
        self._raw_size = 0
        self._state = None
        self._uploads = {}

    @property
    def body(self):
        """::

            bytes = msg.body
            msg.body = b'Hello!'

        Slurp or replace :attr:`content`, :mod:`Mojo.Content.MultiPart` will be
        automatically downgraded to :mod:`Pyjo.Content.Single`.
        """
        content = self._downgrade_content()
        return content.asset.slurp()

    @body.setter
    def body(self, value):
        content = self._downgrade_content()
        return content.set(asset=Pyjo.Asset.Memory.new().add_chunk(value))

    @property
    def body_params(self):
        """::

            params = msg.body_params

        ``POST`` parameters extracted from ``application/x-www-form-urlencoded`` or
        ``multipart/form-data`` message body, usually a :mod:`Pyjo.Parameters` object. Note
        that this method caches all data, so it should not be called before the entire
        message body has been received. Parts of the message body need to be loaded
        into memory to parse ``POST`` parameters, so you have to make sure it is not
        excessively large, there's a 16MB limit by default. ::

            # Get POST parameter names and values
            params_dict = msg.body_params.to_dict()
        """
        if self._body_params:
            return self._body_params

        params = Pyjo.Parameters.new()
        self._body_params = params
        params.charset = self.content.charset or self.default_charset

        # "application/x-www-form-urlencoded"
        content_type = notnone(self.headers.content_type, '')
        if content_type.lower().find('application/x-www-form-urlencoded') >= 0:
            params.parse(self.content.asset.slurp())

        # "multipart/form-data"
        elif content_type.lower().find('multipart/form-data') >= 0:
            for name, value, _ in self._parse_formdata():
                params.append(
                    (name, u(value, params.charset)),
                )

        return params

    @property
    def body_size(self):
        """::

            size = msg.body_size

        Content size in bytes.
        """
        return self.content.body_size

    def build_body(self):
        """::

            chunk = msg.build_body()

        Render whole body.
        """
        return self._build('get_body_chunk')

    def build_headers(self):
        """::

            chunk = msg.build_headers()

        Render all headers.
        """
        return self._build('get_header_chunk')

    def build_start_line(self):
        """::

            chunk = msg.build_start_line()

        Render start-line.
        """
        return self._build('get_start_line_chunk')

    def cookie(self, name):
        """::

            cookie = msg.cookie('foo')

        Access message cookies, usually :mod:`Pyjo.Cookie.Request` or
        :mod:`Pyjo.Cookie.Response` objects. If there are multiple cookies sharing the
        same name, and you want to access more than just the last one, you can use
        :meth:`every_cookie`. Note that this method caches all data, so it should not be
        called before all headers have been received. ::

            # Get cookie value
            print(msg.cookie('foo').value)
        """
        return self._cache('cookie', False, name)

    @not_implemented
    def cookies(self):
        """::

            cookies = msg.cookies

        Access message cookies. Meant to be overloaded in a subclass.
        """
        pass

    def dom(self, pattern=None):
        r"""::

            dom = msg.dom()
            collection = msg.dom('a[href]')

        Retrieve message body from :attr:`text` and turn it into a :mod:`Pyjo.DOM` object,
        an optional selector can be used to call the method :meth:`Pyjo.DOM.find` on it
        right away, which then returns a :mod:`Pyjo.Collection` object. Note that this
        method caches all data, so it should not be called before the entire message
        body has been received. The whole message body needs to be loaded into memory
        to parse it, so you have to make sure it is not excessively large, there's a
        16MB limit by default. ::

            # Perform "find" right away
            print(msg.dom('h1, h2, h3').map('text').join("\n"))

            # Use everything else Mojo::DOM has to offer
            print(msg.dom.at('title').text)
            print(msg.dom.at('body').children().map('tag').uniq().join("\n"))
        """
        if self.content.is_multipart:
            return
        else:
            if self._dom is None:
                self._dom = Pyjo.DOM.new(self.text)
            dom = self._dom
            if pattern is None:
                return dom
            else:
                return dom.find(pattern)

    @property
    def error(self):
        """::

            err = msg.error

        Get message error, a ``None`` return value indicates that there is no
        error.
        """
        return self._error

    def every_cookie(self, name):
        """::

            cookies = msg.every_cookie('foo')

        Similar to :meth:`cookie`, but returns all message cookies sharing the same name
        as an array reference. ::

            # Get first cookie value
            print(msg.every_cookie('foo')[0].value)
        """
        return self._cache('cookie', True, name)

    def every_upload(self, name):
        """::

            uploads = msg.every_upload('foo')

        Similar to :meth:`upload`, but returns all file uploads sharing the same name as
        an array reference. ::

            # Get content of first uploaded file
            print(msg.every_upload('foo')[0].asset.slurp())
        """
        return self._cache('upload', True, name)

    @not_implemented
    def extract_start_line(self, buf):
        """::

            boolean = msg.extract_start_line(buf)

        Extract start-line from string. Meant to be overloaded in a subclass.
        """
        pass

    def finish(self):
        """::

            msg = msg.finish()

        Finish message parser/generator.
        """
        self._state = 'finished'
        if self._finished:
            return self
        else:
            self._finished = True
            return self.emit('finish')

    def fix_headers(self):
        """::

            msg = msg.fix_headers()

        Make sure message has all required headers.
        """
        if self._fixed:
            return self

        self._fixed = True

        # Content-Length or Connection (unless chunked transfer encoding is used)
        content = self.content
        headers = content.headers
        if content.is_multipart:
            headers.remove('Content-Length')
        elif content.is_chunked or headers.content_length:
            return self
        if content.is_dynamic:
            headers.connection = 'close'
        else:
            headers.content_length = self.body_size

        return self

    def get_body_chunk(self, offset):
        """::

            chunk = msg.get_body_chunk(offset)

        Get a chunk of body data starting from a specific position.
        """
        self.emit('progress', 'body', offset)
        chunk = self.content.get_body_chunk(offset)
        if chunk is not None and not len(chunk):
            self.finish()
        return chunk

    def get_header_chunk(self, offset):
        """::

            chunk = msg.get_header_chunk(offset)

        Get a chunk of header data, starting from a specific position.
        """
        self.emit('progress', 'headers', offset)
        return self.fix_headers().content.get_header_chunk(offset)

    @not_implemented
    def get_start_line_chunk(self, offset):
        """::

            chunk = msg.get_start_line_chunk(offset)

        Get a chunk of start-line data starting from a specific position. Meant to be
        overloaded in a subclass.
        """
        pass

    @property
    def header_size(self):
        """::

            size = msg.header_size

        Size of headers in bytes.
        """
        return self.fix_headers().content.header_size

    @property
    def headers(self):
        """::

            headers = msg.headers

        Message headers, usually a :mod:`Pyjo.Headers` object. ::

            # Longer version
            headers = msg.content.headers
        """
        return self.content.headers

    @property
    def is_finished(self):
        """::

            boolean = msg.is_finished

        Check if message parser/generator is finished.
        """
        return self._state == 'finished'

    @property
    def is_limit_exceeded(self):
        """::

            boolean = msg.is_limit_exceeded

        Check if message has exceeded :attr:`max_line_size`, :attr:`max_message_size`,
        :attr:`Pyjo.Content.max_buffer_size` or :attr:`Pyjo.Headers.max_line_size`.
        """
        return self._limited

    def json(self, pointer=None):
        """::

            value = msg.json()
            value = msg.json('/foo/bar')

        Decode JSON message body directly using :mod:`Pyjo.JSON` if possible, an ``None``
        return value indicates a bare ``null`` or that decoding failed. An optional JSON
        Pointer can be used to extract a specific value with :mod:`Pyjo.JSON.Pointer`.
        Note that this method caches all data, so it should not be called before the
        entire message body has been received. The whole message body needs to be
        loaded into memory to parse it, so you have to make sure it is not excessively
        large, there's a 16MB limit by default. ::

            # Extract JSON values
            print(msg.json()['foo']['bar'][23])
            print(msg.json('/foo/bar/23'))
        """
        if self.content.is_multipart:
            return

        if self._json is None:
            self._json = j(self.body)

        data = self._json
        if pointer:
            return Pyjo.JSON.Pointer.new(data).get(pointer)
        else:
            return data

    def parse(self, chunk=b''):
        """::

            msg = msg.parse('HTTP/1.1 200 OK...')

        Parse message chunk.
        """
        if self._error:
            return self
        self._raw_size += len(chunk)
        self._buffer += chunk

        # Start-line
        if not self._state:
            # Check start-line size
            try:
                l = self._buffer.index(b'\x0a')
            except ValueError:
                l = len(self._buffer)
            if l > self.max_line_size:
                return self._limit('Maximum start-line size exceeded')

            if self.extract_start_line(self._buffer):
                self._state = 'content'

        # Content
        if self._state == 'content' or self._state == 'finished':
            self.content = self.content.parse(self._buffer)
            self._buffer = bytearray()

        # Check message size
        max_size = self.max_message_size
        if max_size and max_size < self._raw_size:
            return self._limit('Maximum message size exceeded')

        # Check header size
        if self.headers.is_limit_exceeded:
            return self._limit('Maximum header size exceeded')

        # Check buffer size
        if self.content.is_limit_exceeded:
            return self._limit('Maximum buffer size exceeded')

        if self.emit('progress', 'parse', 0).content.is_finished:
            return self.finish()
        else:
            return self

    def set_error(self, message=None, code=None):
        """::

            msg = msg.set_error(message, code)

        Set message error, a ``None`` for message indicates that there is no
        error. ::

            # Connection or parser error
            msg.set_error(message='Connection refused')

            # 4xx/5xx response
            msg.set_error(message='Internal Server Error', code=500)
        """
        if message:
            self._error = {
                'message': message,
                'code': code,
            }
            return self.finish()
        else:
            self._error = {}
            return self

    @property
    def start_line_size(self):
        """::

            size = msg.start_line_size

        Size of the start-line in bytes.
        """
        return len(self.build_start_line())

    @property
    def text(self):
        """::

            string = msg.text

        Retrieve :attr:`body` and try to decode it with :attr:`Pyjo.Content.charset` or
        :attr:`default_charset`.
        """
        body = self.body
        charset = self.content.charset or 'utf-8'
        try:
            return bytes(body).decode(charset)
        except UnicodeDecodeError:
            return body.decode('iso-8859-1')

    def to_bytes(self):
        """::

            bstring = msg.to_bytes()

        Render whole message.
        """
        return bytes(self.build_start_line() + self.build_headers() + self.build_body())

    def upload(self, name):
        """::

            upload = msg.upload('foo')

        Access ``multipart/form-data`` file uploads, usually :mod:`Pyjo.Upload` objects. If
        there are multiple uploads sharing the same name, and you want to access more
        than just the last one, you can use :meth:`every_upload`. Note that this method
        caches all data, so it should not be called before the entire message body has
        been received. ::

            # Get content of uploaded file
            print(msg.upload('foo').asset.slurp())
        """
        return self._cache('upload', False, name)

    @property
    def uploads(self):
        """::

            uploads = msg.uploads

        All ``multipart/form-data`` file uploads, usually :mod:`Pyjo.Upload` objects. ::

            # Names of all uploads
            for upload in msg.uploads:
                print(upload.name)
        """
        uploads = []
        for data in self._parse_formdata(True):
            upload = Pyjo.Upload.new(name=data[0], filename=data[2], asset=data[1].asset, headers=data[1].headers)
            uploads.append(upload)
        return uploads

    def _build(self, method):
        buf = b''
        offset = 0

        while True:
            # No chunk yet, try again
            chunk = getattr(self, method)(offset)
            if chunk is None:
                continue

            # End of part
            l = len(chunk)
            if not l:
                break

            offset += l
            buf += chunk

        return buf

    def _cache(self, method, ret_all, name):
        # Cache objects by name
        method += 's'
        attr = '_' + method

        if not getattr(self, attr):
            setattr(self, attr, {})
            c = getattr(self, method)
            if c:
                for a in c:
                    if a.name not in getattr(self, attr):
                        getattr(self, attr)[a.name] = []
                    getattr(self, attr)[a.name].append(a)

        if name in getattr(self, attr):
            objects = getattr(self, attr)[name]
        else:
            objects = []

        if ret_all:
            return objects
        else:
            if objects:
                return objects[-1]
            else:
                return

    def _downgrade_content(self):
        # Downgrade multipart content
        if self.content.is_multipart:
            self.content = Pyjo.Content.Single.new()
        return self.content

    def _limit(self, message):
        self._limited = True
        return self.set_error(message=message)

    def _parse_formdata(self, upload=False):
        content = self.content

        if not content.is_multipart:
            return

        charset = content.charset or self.default_charset

        # Check all parts recursively
        parts = [content]
        while parts:
            part = parts.pop(0)
            if part.is_multipart:
                parts = part.parts + parts
                continue

            try:
                disposition = part.headers.content_disposition
            except:
                disposition = None

            if not disposition:
                continue

            m = re_filename.search(disposition)
            filename = m.group(1) if m else None

            if upload and filename is None or not upload and filename is not None:
                continue

            m = re_name.search(disposition)
            name = m.group(1) if m else None
            if not upload:
                part = part.asset.slurp()

            if charset:
                if name and (decoded := decode(charset, name)) is not None:
                    name = decoded
                if filename and (decoded := decode(charset, filename)) is not None:
                    filename = decoded
                if not upload and (decoded := decode(charset, part)) is not None:
                    part = decoded

            yield name, part, filename


new = Pyjo_Message.new
object = Pyjo_Message
