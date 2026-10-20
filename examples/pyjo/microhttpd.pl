use v5.14;

use Mojo::IOLoop;

my %opts = (address => '0.0.0.0', port => 8080, map { split /=/, $_, 2 } @ARGV);

Mojo::IOLoop->server(%opts, sub {
    my ($loop, $stream, $id) = @_;

    $stream->on(read => sub {
        my ($stream, $chunk) = @_;

        # Check if we got start line and headers (no body support)
        if (index($chunk, "\x0d\x0a\x0d\x0a") >= 0) {

            my $keepalive = (index($chunk, "\x0d\x0aConnection: Keep-Alive\x0d\x0a") >= 0);

            # Write a minimal HTTP response
            # (the "Hello World!" message has been optimized away!)
            $stream->write("HTTP/1.1 200 OK\x0d\x0aContent-Length: 0\x0d\x0a"
            . ($keepalive ? "Connection: keep-alive\x0d\x0a" : "")
            . "\x0d\x0a");

            if (not $keepalive) {
                $stream->close_gracefully();
            }
        }
    });
});

# Start event loop
Mojo::IOLoop->start;
