use v5.14;

use Mojo::EventEmitter;


package Cat {
    use Mojo::Base 'Mojo::EventEmitter';
    sub poke {
        my ($self, $times) = @_;
        $self->emit(roar => $times);
    }
    sub kill {
        my ($self, $times) = @_;
        $self->emit('dead');
    }
}


my $tiger = Cat->new();

$tiger->on(roar => sub {
    my ($self, $times) = @_;
    for (1 .. $times) {
        say 'RAWR!';
    }
});

$tiger->once(dead => sub {
    say '(x.x)';
});

$tiger->poke(2);
$tiger->poke(2);
$tiger->kill();
$tiger->kill();
