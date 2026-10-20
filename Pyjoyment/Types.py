"""
Pyjoyment.Types - MIME types
============================
::

    from Pyjoyment.Types import Types

    types = Types()
    types.type('foo', 'text/foo')
    print(types.type('foo'))

    # Or import the module, as in Google Python Style Guide

    import Pyjoyment.Types

    types = Pyjoyment.Types.new()
    types.type('foo', 'text/foo')
    print(types.type('foo'))

:mod:`Pyjoyment.Types` manages MIME types for :mod:`Pyjoyment`. ::

    appcache -> text/cache-manifest
    atom     -> application/atom+xml
    bin      -> application/octet-stream
    css      -> text/css
    gif      -> image/gif
    gz       -> application/x-gzip
    htm      -> text/html
    html     -> text/html;charset=UTF-8
    ico      -> image/x-icon
    jpeg     -> image/jpeg
    jpg      -> image/jpeg
    js       -> application/javascript
    json     -> application/json;charset=UTF-8
    mp3      -> audio/mpeg
    mp4      -> video/mp4
    ogg      -> audio/ogg
    ogv      -> video/ogg
    pdf      -> application/pdf
    png      -> image/png
    rss      -> application/rss+xml
    sse      -> text/event-stream
    svg      -> image/svg+xml
    toml     -> application/toml;charset=UTF-8
    ttf      -> font/ttf
    txt      -> text/plain;charset=UTF-8
    webm     -> video/webm
    woff     -> font/woff
    woff2    -> font/woff2
    xml      -> application/xml,text/xml
    yaml     -> application/yaml;charset=UTF-8,text/yaml,application/x-yaml,text/x-yaml
    zip      -> application/zip

The most common ones are already defined.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Types <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Types.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Base
import Pyjo.File

import os
import re

from typing import TYPE_CHECKING, Self, overload


if TYPE_CHECKING:
    import Pyjo.Headers
    import Pyjoyment.Controller


_ACCEPT_RE = re.compile(r'^\s*([^,; ]+)(?:\s*\;\s*q\s*=\s*(\d+(?:\.\d+)?))?\s*$', re.IGNORECASE)


class Pyjoyment_Types(Pyjo.Base.object):
    """
    :mod:`Pyjoyment.Types` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def __init__(self, mapping: dict[str, list[str]] | None = None) -> None:
        """::

            types = Pyjoyment.Types.new()
            types = Pyjoyment.Types.new(mapping={'png': ['image/png']})

        Construct a new :mod:`Pyjoyment.Types` object.
        """
        self.mapping: dict[str, list[str]] = (
            mapping
            if mapping is not None
            else {
                'appcache': ['text/cache-manifest'],
                'atom': ['application/atom+xml'],
                'bin': ['application/octet-stream'],
                'css': ['text/css'],
                'gif': ['image/gif'],
                'gz': ['application/x-gzip'],
                'htm': ['text/html'],
                'html': ['text/html;charset=UTF-8'],
                'ico': ['image/x-icon'],
                'jpeg': ['image/jpeg'],
                'jpg': ['image/jpeg'],
                'js': ['application/javascript'],
                'json': ['application/json;charset=UTF-8'],
                'mp3': ['audio/mpeg'],
                'mp4': ['video/mp4'],
                'ogg': ['audio/ogg'],
                'ogv': ['video/ogg'],
                'pdf': ['application/pdf'],
                'png': ['image/png'],
                'rss': ['application/rss+xml'],
                'sse': ['text/event-stream'],
                'svg': ['image/svg+xml'],
                # Not in Mojolicious: TOML
                'toml': ['application/toml;charset=UTF-8'],
                'ttf': ['font/ttf'],
                'txt': ['text/plain;charset=UTF-8'],
                'webm': ['video/webm'],
                'woff': ['font/woff'],
                'woff2': ['font/woff2'],
                'xml': ['application/xml', 'text/xml'],
                # Not in Mojolicious: YAML, of RFC 9512, and the types that it had before
                'yaml': ['application/yaml;charset=UTF-8', 'text/yaml', 'application/x-yaml', 'text/x-yaml'],
                'zip': ['application/zip'],
            }
        )
        """::

            mapping = types.mapping
            types.mapping = {'png': ['image/png']}

        MIME type mapping.
        """

    def content_type(
        self, c: 'Pyjoyment.Controller.object', *, ext: str | None = None, file: str | os.PathLike[str] | None = None
    ) -> 'Pyjo.Headers.object | None':
        """::

            types.content_type(Pyjoyment.Controller.new(), ext='json')

        Detect MIME type for :mod:`Pyjoyment.Controller` object unless a
        ``Content-Type`` response header has already been set, defaults to using
        ``application/octet-stream`` if no better alternative could be found.
        These options are currently available:

        ext
            ::

                ext='json'

            File extension to get MIME type for.

        file
            ::

                file='foo/bar.png'

            File path to get MIME type for.
        """
        headers = c.res.headers
        if headers.content_type:
            return None

        type = self.file_type(file) if file else self.type(ext or '')
        headers.content_type = type if type is not None else 'application/octet-stream'
        return headers

    def detect(self, accept: str | None) -> list[str]:
        """::

            exts = types.detect('text/html, application/json;q=9')

        Detect file extensions from ``Accept`` header value. ::

            # List detected extensions prioritized
            for ext in types.detect('application/json, text/xml;q=0.1'):
                print(ext)
        """
        # Extract and prioritize MIME types
        types: dict[str, float] = {}
        for part in (accept or '').split(','):
            if m := _ACCEPT_RE.match(part):
                types[m[1].lower()] = float(m[2]) if m[2] is not None else 1
        detected = sorted(sorted(types), key=lambda type: types[type], reverse=True)

        # Detect extensions from MIME types
        reverse: dict[str, list[str]] = {}
        mapping = self.mapping
        for ext in sorted(mapping):
            for type in mapping[ext]:
                reverse.setdefault(type.partition(';')[0].lower(), []).append(ext)

        return [ext for type in detected for ext in reverse.get(type, [])]

    def file_type(self, file: str | os.PathLike[str]) -> str | None:
        """::

            type = types.file_type('foo/bar.png')

        Get MIME type for file path.
        """
        return self.type(Pyjo.File.path(file).extname)

    @overload
    def type(self, ext: str) -> str | None: ...

    @overload
    def type(self, ext: str, type: str | list[str]) -> Self: ...

    def type(self, ext: str, type: str | list[str] | None = None) -> str | Self | None:
        """::

            type = types.type('png')
            types = types.type('png', 'image/png')
            types = types.type('json', ['application/json', 'text/x-json'])

        Get or set MIME types for file extension, alternatives are only used for
        detection.
        """
        if type is None:
            types = self.mapping.get(ext.lower())
            return types[0] if types else None
        self.mapping[ext.lower()] = type if isinstance(type, list) else [type]
        return self


new = Pyjoyment_Types.new
object = Pyjoyment_Types
Types = Pyjoyment_Types
