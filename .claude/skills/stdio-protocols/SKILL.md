---
name: stdio-protocols
description: Change the protocols of Pyjoyment on the standard input and output and on streams of messages, with Pyjo.IOLoop.Stdio, the framings of Pyjo.IOLoop.Messages, the promises and iterators of streams, Pyjo.Server.Stdio and serve of Pyjo.JSON.RPC. Use when changing them, or a protocol on them, as the one of MCP.
---

# Standard Input and Output

`Pyjo.IOLoop.Stdio` serves a protocol on the standard input and output, as the
transport stdio of MCP or LSP, where a single stray byte on the standard
output breaks the protocol, so it takes them for itself: it reads and writes
duplicates of the file descriptors `0` and `1`, the descriptor `0` reads
`/dev/null`, and the descriptor `1` and `sys.stdout` write to the standard
error, so that a `print`, a library or a process that inherits them writes
there; `close` gives them back. A test runs it in a process of its own, as
`t/Pyjo/IOLoop_Stdio.py` does, as it changes the descriptors of its process.

- `O_NONBLOCK` belongs to the open file description, which the process shares
  with its parent and the other processes of a pipeline, so the stream sets
  it only on pipes and sockets and gives back the mode that it had, and a
  terminal, whose description the shell shares, stays blocking.
- A reactor watches pipes, sockets and terminals, but epoll watches no file
  and no `/dev/null` (`EPERM`) and kqueue no `/dev/null` (`EINVAL`), so a file
  is read with a timer of no time and written at once, as its reads and writes
  do not block.
- A peer that writes requests without reading the responses fills the pipe of
  the output, and then the buffer of the stream grows without a limit; a
  server that has much to write waits for `drain`, with the callback of
  `write` or `send`, or stops reading while `can_write` is false. A blocking
  write in its place would deadlock both sides once both pipes are full.
- The end of the input is the event `end`, not `close`, as the responses of
  the requests in progress are still to be written: without a subscriber, the
  stream closes gracefully, as a connection of TCP that the peer closes.
- Windows has no pipes that the event loop watches, so the constructor
  raises there, as `Pyjo.IOLoop.ChildProcess` emits `error`.

A framing of `Pyjo.IOLoop.Messages` decodes one message at a time, so that a
message over the maximum size, which closes the stream, does not lose the
messages before it in the same read, and `Lines` remembers how far it has
searched, so that a long line that comes in many reads is not searched from
its beginning each time. With the input and the output of a child process,
`close_gracefully` closes the output only, the standard input of the child,
which is how a server of the standard input and output learns that no request
comes anymore, and the input is read until the child ends it, so that the
responses of the requests in progress still come in.

The promises of a stream and of its messages, `read_p` and `message_p`, and
their iterators, pull them as the streams of Node.js in their paused mode: the
stream reads only while a promise waits, so that a peer that sends more than
is asked for waits in the pipe, and what came before the first promise went to
the subscribers of the event `read` alone, as a stream of Mojo emits what it
reads at once. The reactor of asyncio runs a coroutine as a task, in the next
cycle of its loop, where the base reactor runs it at once until it waits, so
a promise or an iterator is made before the coroutine that awaits it, as
`read_all_p` asks for its first chunk at once, and `once_p` before the event
that it waits for. A stream that is closed already gives `None` and rejects a
write at once, and fulfills `once_p('close')` and `close_gracefully_p`, as its
event `close` comes no more; `close_gracefully_p` subscribes the event before
the close, which comes at once when nothing waits to be written. The
inactivity timeout of a stream rejects its promises with `TimeoutError`, so
that it is not taken for the end of the stream. `client_p` of `Pyjo.IOLoop`
and `connect_p` of `Pyjo.IOLoop.Datagram` make the pull before they fulfill
their promise, so that what a peer sends at once, as a greeting or the
refusal of a datagram, waits for the coroutine. An error of a datagram socket
leaves it open, so it rejects only the promises that wait, or the next one, and
the error of a datagram that `send_p` sends rejects its promise in the place of
the event `error`. The methods of
`Pyjo.EventEmitter` are `once_p` and `events`, as `iterate` of a stream takes a
size.

A reactor refers to its sockets weakly, so a coroutine that waits for the
promise of a socket that only it refers to, or that nothing refers to, as in
`await Pyjo.IOLoop.Datagram.new().connect_p(...)`, is in a cycle of the socket,
its subscribers and the promise, which the garbage collector frees, where Perl
keeps it. So `run_coroutine` of the base reactor keeps its coroutines until
they end, as the reactor of asyncio keeps its tasks, and an event emitter is
kept while a promise of it waits, by `_hold` of `Pyjo.EventEmitter`, which
`once_p`, the pulls and `write_p` and `send_p` call. A promise that never
settles keeps its emitter, as a task of asyncio that never ends. A test of it
calls `gc.collect()` while the coroutine waits, which frees the cycle at once.

`Pyjo.Server.Stdio` serves no HTTP, so the application gives its protocol with
a subscriber of the event `stream` of the server, in the hook
`before_server_start`, where a plugin configures the servers, and the framing
stays with the protocol, not with the command line; the command `stdio` is not
detected, as a pipe on the standard input is too common to mean it. The server
takes the standard input and output before it emits the hook, so that what
the application prints while it starts goes to the standard error, and INT and
TERM end the standard input with `end` of the stream, as its end does, so
that a graceful stop is the end of the input of the protocol, which waits for
the responses in progress.

`serve` of `Pyjo.JSON.RPC` makes both peers of a stream servers and clients,
so it drops a response to no call of its client, as answering it with an
error, as a server answers what is not a request, would send the error back
and forth between two peers that serve each other. Its `context` is one object
for all the requests, so a protocol on JSON-RPC that keeps the state of a
request in its context, as the server of MCP does, or has rules of its own, as
no batches, gives `serve` a function `dispatch_p` in its place, which gets each
message with the client and calls a dispatcher of its own: a protocol holds a
dispatcher rather than subclassing it, and `serve` keeps what the stream needs,
the responses to the client, the requests in progress and the end of the
input, so a function that fails answers its requests with `-32603` instead of
leaving the count of them, and the end of the stream, waiting.
