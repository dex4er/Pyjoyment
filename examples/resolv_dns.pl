#!/usr/bin/env perl

use v5.14;

use Mojo::IOLoop;
use Net::DNS::Packet;

my ($name, $type, $ns) = @ARGV;
die "Usage: resolv_dns.pl name [type] [nameserver]\n" unless $name;
$type //= 'A';
$ns   //= '8.8.8.8';

# DNS over TCP, where a message has its length in front of it
Mojo::IOLoop->client({address => $ns, port => 53} => sub {
    my ($loop, $err, $stream) = @_;
    return warn "Connection error: $err\n" if $err;

    my $buffer = '';
    $stream->on(read => sub {
        my ($stream, $bytes) = @_;
        $buffer .= $bytes;
        return unless length $buffer >= 2 and length $buffer >= 2 + unpack 'n', $buffer;
        my $data = substr $buffer, 2;
        say $_->string for Net::DNS::Packet->new(\$data)->answer;
        $stream->close;
    });

    my $packet = Net::DNS::Packet->new($name, $type, 'IN');
    $packet->header->rd(1);
    my $query = $packet->data;
    $stream->write(pack('n', length $query) . $query);
});

Mojo::IOLoop->start;
