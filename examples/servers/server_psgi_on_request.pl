use Mojo::Server::PSGI;

use HTTP::Server::PSGI;

my $psgi = Mojo::Server::PSGI->new;
$psgi->unsubscribe('request');
$psgi->on(request => sub {
    my ($psgi, $tx) = @_;

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
my $app = $psgi->to_psgi_app;

my $server = HTTP::Server::PSGI->new(
    host => "127.0.0.1",
    port => 5000,
);

$server->run($app);
