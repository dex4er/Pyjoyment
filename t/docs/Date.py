if __name__ == '__main__':
    from Pyjo.Test import *  # noqa

    import time

    import Pyjo.Date

    # Parse
    date = Pyjo.Date.new('Sun, 06 Nov 1994 08:49:37 GMT')
    is_ok(date.epoch, 784111777, 'date')

    # Build
    before = time.time()
    date = Pyjo.Date.new(before + 60)
    ok(date.epoch > before, 'date.epoch > before')

    # new
    date = Pyjo.Date.new()
    ok(date.epoch >= before, 'date.epoch >= before')
    date = Pyjo.Date.new('Sun Nov  6 08:49:37 1994')
    is_ok(date.epoch, 784111777, 'date')

    # __bool__
    date = Pyjo.Date.new('Wrong')
    boolean = bool(date)
    ok(boolean, 'boolean')

    # parse
    date = date.parse('Sun Nov  6 08:49:37 1994')
    is_ok(date.epoch, 784111777, 'date')

    # Epoch
    is_ok(Pyjo.Date.new('784111777').epoch, 784111777, 'date')
    is_ok(Pyjo.Date.new('784111777.21').epoch, 784111777.21, 'date')

    # RFC 822/1123
    is_ok(Pyjo.Date.new('Sun, 06 Nov 1994 08:49:37 GMT').epoch, 784111777, 'date')

    # RFC 850/1036
    is_ok(Pyjo.Date.new('Sunday, 06-Nov-94 08:49:37 GMT').epoch, 784111777, 'date')

    # Ansi C asctime()
    is_ok(Pyjo.Date.new('Sun Nov  6 08:49:37 1994').epoch, 784111777, 'date')

    # RFC 3339
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37Z').epoch, 784111777, 'date')
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37').epoch, 784111777, 'date')
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37.21Z').epoch, 784111777.21, 'date')
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37+01:00').epoch, 784108177, 'date')
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37-01:00').epoch, 784115377, 'date')

    # isoformat
    string = Pyjo.Date.new(784111777).isoformat()
    is_ok(string, '1994-11-06T08:49:37Z', 'date')

    string = Pyjo.Date.new(784111777.21).isoformat(sep='T')
    is_ok(string, '1994-11-06T08:49:37.21Z', 'date')

    string = Pyjo.Date.new(784111777).to_str()
    is_ok(string, 'Sun, 06 Nov 1994 08:49:37 GMT', 'date')

    done_testing()
