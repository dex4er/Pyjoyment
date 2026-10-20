use Mojo::Server::Daemon;

my $daemon = Mojo::Server::Daemon->new(listen => ['http://*:3000']);
$daemon->unsubscribe('request');
$daemon->on(request => sub {
    my ($daemon, $tx) = @_;

    # Request
    my $method = $tx->req->method;
    my $path   = $tx->req->url->path;

    # Response
    $tx->res->code(200);
    $tx->res->headers->content_type('text/plain');
    $tx->res->body("$method request for $path\n");

    # Resume transaction
    $tx->resume;
});
$daemon->run;
