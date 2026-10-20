use v5.14;

use Mojo::IOLoop;

Mojo::IOLoop->recurring(0, sub {
    say "A";
});

Mojo::IOLoop->timer(1, sub {
    my ($loop) = @_;
    $loop->stop();
});

Mojo::IOLoop->start();
