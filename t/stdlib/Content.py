import Pyjo.Content.Single

from Pyjo.Test import *

import email.mime.application
import email.mime.multipart
import email.mime.text
import email.policy
import gzip


with subtest('gzip of the standard library'):
    body = gzip.compress(b'Hello World!' * 100)
    content = Pyjo.Content.Single.new(auto_decompress=True)
    content.parse(b'Content-Encoding: gzip\x0d\x0aContent-Length: %d\x0d\x0a\x0d\x0a' % len(body))
    for i in range(0, len(body), 7):
        content.parse(body[i : i + 7])
    ok(content.is_finished, 'finished')
    is_ok(content.asset.slurp(), b'Hello World!' * 100, 'decompressed')
    is_ok(content.headers.content_length, '1200', 'length of the decompressed content')
    is_ok(content.headers.content_encoding, None, 'no "Content-Encoding" header')

with subtest('Multipart content of the email package'):
    message = email.mime.multipart.MIMEMultipart('form-data', boundary='pyjo-boundary')
    message.attach(email.mime.text.MIMEText('Hello World!', 'plain', 'utf-8'))
    message.attach(email.mime.application.MIMEApplication(b'\x00\x01\x02', 'octet-stream'))
    data = message.as_bytes(policy=email.policy.HTTP)
    headers, body = data.split(b'\x0d\x0a\x0d\x0a', 1)
    content = Pyjo.Content.Single.new()
    content = content.parse(headers + b'\x0d\x0aContent-Length: %d\x0d\x0a\x0d\x0a' % len(body) + body)
    ok(content.is_multipart, 'upgraded to multipart')
    ok(content.is_finished, 'finished')
    is_ok(len(content.parts), 2, 'two parts')
    is_ok(content.parts[0].headers.content_type, 'text/plain; charset="utf-8"', 'type of the first part')
    is_ok(content.parts[1].headers.header('Content-Transfer-Encoding'), 'base64', 'encoding of the second part')

    # And the other way round
    rendered, offset = b'', 0
    while chunk := content.get_body_chunk(offset):
        rendered += chunk
        offset += len(chunk)
    parsed = email.message_from_bytes(
        b'Content-Type: ' + content.headers.content_type.encode() + b'\x0d\x0a\x0d\x0a' + rendered,
        policy=email.policy.HTTP,
    )
    is_ok(
        [part.get_content_type() for part in parsed.iter_parts()], ['text/plain', 'application/octet-stream'], 'parsed'
    )
    is_ok(parsed.get_payload()[1].get_payload(decode=True), b'\x00\x01\x02', 'binary part')

done_testing()
