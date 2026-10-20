use Mojo::Server::CGI;

my $cgi = Mojo::Server::CGI->new;
$cgi->unsubscribe('request');
$cgi->on(request => sub {
    my ($cgi, $tx) = @_;

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
$cgi->run;
