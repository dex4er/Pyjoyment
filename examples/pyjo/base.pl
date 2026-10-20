use v5.14;


package Point {
    use Mojo::Base -base;
    has ['x', 'y'] => 0;
}

package Line {
    use Mojo::Base -base;
    has ['p1', 'p2'] => sub { Point->new };
}


my $p = Point->new(x => 1, y => 2);

my $line = Line->new(p1 => $p);

say sprintf "[%s,%s]", $line->p1->x, $line->p1->y;
say sprintf "[%s,%s]", $line->p2->x, $line->p2->y;
