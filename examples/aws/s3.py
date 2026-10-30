"""
__DATA__

@@ folder.html.ep
<!DOCTYPE html>
<html>
  <head><title>/<%= prefix %></title></head>
  <body>
    <h1>/<%= prefix %></h1>
    <ul>
      % if prefix:
      <li><a href="../">../</a></li>
      % end
      % for name in names:
      <li><a href="<%= url_for('object', key=prefix + name) %>"><%= name %></a></li>
      % end
    </ul>
  </body>
</html>
"""

import Pyjo.Date
import Pyjo.GetOpt
import Pyjo.Promise

from Pyjo.Util import die, getopt
from Pyjoyment.Lite import *

import contextlib
import os
import threading

# The asynchronous AWS SDK, on the event loop of asyncio, which the default reactor runs
import aiobotocore.session
import botocore.exceptions


# The options before the command, with the names of the AWS CLI, which set the environment variables that the
# application and the AWS SDK read: python s3.py --profile myprofile --bucket mybucket daemon
getopt(
    {
        'bucket=s': Pyjo.GetOpt.env('S3_BUCKET'),
        'endpoint-url=s': Pyjo.GetOpt.env('AWS_ENDPOINT_URL'),
        'profile=s': Pyjo.GetOpt.env('AWS_PROFILE'),
        'region=s': Pyjo.GetOpt.env('AWS_REGION'),
    },
    pass_through=True,
    require_order=True,
)

# The bucket, whose objects the application serves, with the credentials and the region of the AWS SDK
bucket = os.environ.get('S3_BUCKET') or die(
    'Usage: s3.py --bucket BUCKET [--profile PROFILE] [--region REGION] [--endpoint-url URL] COMMAND [OPTIONS]'
)

session = aiobotocore.session.get_session()

# A client of S3 for each event loop, as its connections belong to one, which the first request that needs it makes
local = threading.local()


def s3_p():
    if not hasattr(local, 'client_p'):
        local.clients = contextlib.AsyncExitStack()
        local.client_p = Pyjo.Promise.new(local.clients.enter_async_context(session.create_client('s3')))
    return local.client_p


# The client closes its connections once the server stops
@hook('after_server_stop')
def after_server_stop(server, app):
    if hasattr(local, 'clients'):
        del local.client_p
        return Pyjo.Promise.new(local.clients.aclose())


def not_found(error):
    return error.response['Error']['Code'] in ('NoSuchKey', '404')


# A promise of a write, which the client has read once it is fulfilled
def write_p(c, chunk):
    drained = Pyjo.Promise.new()
    c.write(chunk, lambda c: drained.resolve(True))
    return drained


# The content of an object, as it comes, each chunk once the client has read the one before
async def send_object(c, key):
    s3 = await s3_p()
    response = await s3.get_object(Bucket=bucket, Key=key)
    headers = c.res.headers
    headers.content_type = response['ContentType']
    headers.content_length = response['ContentLength']
    headers.etag = response['ETag']
    headers.last_modified = Pyjo.Date.new(response['LastModified']).to_str()

    # The response ends with its last byte, as it has the length of the object, and a client that goes away finishes the
    # transaction, which drains no more
    finished = Pyjo.Promise.new()
    c.on('finish', lambda c: finished.resolve(False))
    async with response['Body'] as body:
        if not response['ContentLength']:
            return c.rendered()
        async for chunk in body.iter_chunks(64 * 1024):
            if not await Pyjo.Promise.race(write_p(c, chunk), finished):
                return


# The folders and the objects under a prefix, as S3 has no folders, only keys with slashes, and a folder that the console
# of S3 makes, an empty object of the prefix, which the list leaves out
async def send_folder(c, prefix):
    s3 = await s3_p()
    names, count = [], 0
    async for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket, Prefix=prefix, Delimiter='/'):
        count += page['KeyCount']
        names += [p['Prefix'].removeprefix(prefix) for p in page.get('CommonPrefixes', [])]
        names += [o['Key'].removeprefix(prefix) for o in page.get('Contents', []) if o['Key'] != prefix]
    if prefix and not count:
        return c.reply.not_found()
    c.render('folder', prefix=prefix, names=names)


# An object, "index.html" or the list of a folder, for a key that ends with a slash
@get('/*key', {'key': ''}, 'object')
async def serve(c):
    key = c.param('key')
    if key and not key.endswith('/'):
        try:
            return await send_object(c, key)
        except botocore.exceptions.ClientError as e:
            if not not_found(e):
                raise

        # A folder without its slash
        s3 = await s3_p()
        if (await s3.list_objects_v2(Bucket=bucket, Prefix=f'{key}/', MaxKeys=1))['KeyCount']:
            return c.redirect_to('object', key=f'{key}/')
        return c.reply.not_found()

    try:
        await send_object(c, f'{key}index.html')
    except botocore.exceptions.ClientError as e:
        if not not_found(e):
            raise
        await send_folder(c, key)


app.start()
