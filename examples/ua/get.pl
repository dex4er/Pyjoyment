use v5.14;

use open ();
use PerlIO::encoding;
use Encode qw(:fallback_all);
use if (-t STDOUT and $PerlIO::encoding::fallback = HTMLCREF), open => ':locale';
use if (not -t STDOUT), open => ':std', ':encoding(UTF-8)';

use Mojo::UserAgent;

my $url = shift @ARGV or die 'get.pl url opts';
my %opts = map { split /=/, $_, 2 } @ARGV;

my $tx = Mojo::UserAgent->new(%opts)->get($url);
if (my $err = $tx->error) {
    die "$err->{code} response: $err->{message}" if $err->{code};
    die "Connection error: $err->{message}";
}
say $tx->res->text;
