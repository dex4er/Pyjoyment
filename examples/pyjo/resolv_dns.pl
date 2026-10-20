#!/usr/bin/env perl

use v5.14;

use Mojo::IOLoop;
use Net::DNS::Packet;
use Socket qw(SOCK_DGRAM);

my ($name, $type, $ns) = @ARGV;
die "Usage: resolv_dns.pl name [type] [nameserver]\n" unless $name;
$type //= 'A';
$ns   //= '8.8.8.8';

my $timeout = Mojo::IOLoop->timer(5 => sub {
    my $loop = shift;
    warn "Timeout\n";
    $loop->stop;
});

# UDP, as the socket options go to IO::Socket::IP as they are
Mojo::IOLoop->client({address => $ns, port => 53, socket_options => {Type => SOCK_DGRAM}} => sub {
    my ($loop, $err, $stream) = @_;
    return warn "Connection error: $err\n" if $err;

    $stream->on(read => sub {
        my ($stream, $bytes) = @_;
        say $_->string for Net::DNS::Packet->new(\$bytes)->answer;
        $loop->remove($timeout);
        $stream->close;
    });

    my $packet = Net::DNS::Packet->new($name, $type, 'IN');
    $packet->header->rd(1);
    $stream->write($packet->data);
});

Mojo::IOLoop->start;
