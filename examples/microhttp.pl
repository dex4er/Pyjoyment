use v5.14;

use Mojo::IOLoop;

my $port = $ARGV[0] || 8080;

Mojo::IOLoop->client(address => '127.0.0.1', port => $port, sub {
    my ($loop, $err, $stream) = @_;
    return warn "Connection error: $err\n" if $err;

    $stream->on(read => sub {
        my ($stream, $chunk) = @_;
        print $chunk;
        $stream->close();
    });
    $stream->write("GET / HTTP/1.0\x0d\x0a\x0d\x0a");
});

Mojo::IOLoop->start;
