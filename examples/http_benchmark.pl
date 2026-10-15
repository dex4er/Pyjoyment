#!/usr/bin/env perl

use v5.14;

use Mojo::IOLoop;

use Mojo::URL;

use Mojo::Util qw(steady_time);
use List::Util qw(sum);

my $verbose = $ARGV[0] =~ /^--?v(?:erbose)?/ ? shift @ARGV : '';
my $url = Mojo::URL->new($ARGV[0] || 'http://localhost/bigfile.bin');
my $n   = $ARGV[1] || 1;

my @speeds;

say $url;

for (1 .. $n) {

    my $t0 = steady_time;

    my $id = Mojo::IOLoop->client({address => $url->host, port => $url->port || 80} => sub {
        my ($loop, $err, $stream) = @_;
        return warn "Connection error: $err\n" if $err;

        my $size = 0;

        $stream->on(read => sub {
            my ($stream, $bytes) = @_;

            $size += length $bytes;
            print "$size\r" if $verbose;
        });

        $stream->on(close => sub {
            my ($stream) = @_;

            my $t1 = steady_time;
            my $delta = $t1 - $t0;
            push @speeds, int $size * 8 / 1024 / $delta / 1000;

            print "$size\n" if $verbose;
        });

        # Write request
        $stream->write("GET @{[ $url->path->to_string ]} HTTP/1.1\x0d\x0aHost: @{[ $url->host ]}:@{[ $url->port || 80 ]}\x0d\x0a\x0d\x0a");
    });

}

Mojo::IOLoop->start;


my $speed = sum @speeds;
while ($speed =~ s/(?<=\d)(\d{3})(,|$)/,$1/) { }
say $speed, ' Mb/s';
