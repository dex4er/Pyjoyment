use v5.14;

use Mojo::IOLoop;

# Listen on port 3000
my $id = Mojo::IOLoop->server({port => 3000} => sub {
    my ($loop, $stream, $id) = @_;

    $stream->on(read => sub {
        my ($stream, $chunk) = @_;

        # Process input chunk
        say "Server: $chunk";

        # Write response
        $stream->write("HTTP/1.1 200 OK\x0d\x0a\x0d\x0a");

        # Disconnect client
        $stream->close_gracefully();
    });
});

# Connect to port 3000
Mojo::IOLoop->client({port => 3000} => sub {
    my ($loop, $err, $stream) = @_;

    $stream->on(read => sub {
        my ($stream, $chunk) = @_;

        # Process input
        say "Client: $chunk";
    });

    # Write request
    $stream->write("GET / HTTP/1.1\x0d\x0a\x0d\x0a");
});

# Add a timer
Mojo::IOLoop->timer(3 => sub {
    my $loop = shift;

    say "Timeout";

    # Shutdown server
    $loop->remove($id);
});

# Start event loop
Mojo::IOLoop->start;
