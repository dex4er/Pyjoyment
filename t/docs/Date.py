from Pyjo.Test import *


with subtest('Synopsis'):
    import Pyjo.Date

    import time

    # Parse
    date = Pyjo.Date.new('Sun, 06 Nov 1994 08:49:37 GMT')
    is_ok(date.epoch, 784111777, 'date.epoch')

    # Build
    date = Pyjo.Date.new(time.time() + 60)
    like_ok(str(date), r'^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT$', 'date')

with subtest('new'):
    date = Pyjo.Date.new()
    isa_ok(date, Pyjo.Date.object, 'date')
    date = Pyjo.Date.new('Sun Nov  6 08:49:37 1994')
    is_ok(date.epoch, 784111777, 'date.epoch')

with subtest('epoch'):
    epoch = date.epoch
    is_ok(epoch, 784111777, 'epoch')
    date.epoch = 784111777
    is_ok(date.epoch, 784111777, 'date.epoch')

with subtest('__bool__'):
    boolean = bool(date)
    is_ok(boolean, True, 'boolean')

with subtest('__str__'):
    string = str(date)
    is_ok(string, 'Sun, 06 Nov 1994 08:49:37 GMT', 'string')

with subtest('parse'):
    date = date.parse('Sun Nov  6 08:49:37 1994')
    is_ok(date.epoch, 784111777, 'date.epoch')

    # Epoch
    is_ok(Pyjo.Date.new('784111777').epoch, 784111777, "Pyjo.Date.new('784111777').epoch")
    is_ok(Pyjo.Date.new('784111777.21').epoch, 784111777.21, "Pyjo.Date.new('784111777.21').epoch")

    # RFC 822/1123
    is_ok(
        Pyjo.Date.new('Sun, 06 Nov 1994 08:49:37 GMT').epoch,
        784111777,
        "Pyjo.Date.new('Sun, 06 Nov 1994 08:49:37 GMT').epoch",
    )

    # RFC 850/1036
    is_ok(
        Pyjo.Date.new('Sunday, 06-Nov-94 08:49:37 GMT').epoch,
        784111777,
        "Pyjo.Date.new('Sunday, 06-Nov-94 08:49:37 GMT').epoch",
    )

    # Ansi C asctime()
    is_ok(Pyjo.Date.new('Sun Nov  6 08:49:37 1994').epoch, 784111777, "Pyjo.Date.new('Sun Nov  6 08:49:37 1994').epoch")

    # RFC 3339
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37Z').epoch, 784111777, "Pyjo.Date.new('1994-11-06T08:49:37Z').epoch")
    is_ok(Pyjo.Date.new('1994-11-06T08:49:37').epoch, 784111777, "Pyjo.Date.new('1994-11-06T08:49:37').epoch")
    is_ok(
        Pyjo.Date.new('1994-11-06T08:49:37.21Z').epoch,
        784111777.21,
        "Pyjo.Date.new('1994-11-06T08:49:37.21Z').epoch",
    )
    is_ok(
        Pyjo.Date.new('1994-11-06T08:49:37+01:00').epoch,
        784108177,
        "Pyjo.Date.new('1994-11-06T08:49:37+01:00').epoch",
    )
    is_ok(
        Pyjo.Date.new('1994-11-06T08:49:37-01:00').epoch,
        784115377,
        "Pyjo.Date.new('1994-11-06T08:49:37-01:00').epoch",
    )

with subtest('to_datetime'):
    string = date.to_datetime()
    is_ok(string, '1994-11-06T08:49:37Z', 'string')

    # "1994-11-06T08:49:37Z"
    is_ok(Pyjo.Date.new(784111777).to_datetime(), '1994-11-06T08:49:37Z', 'Pyjo.Date.new(784111777).to_datetime()')

    # "1994-11-06T08:49:37.21Z"
    is_ok(
        Pyjo.Date.new(784111777.21).to_datetime(),
        '1994-11-06T08:49:37.21Z',
        'Pyjo.Date.new(784111777.21).to_datetime()',
    )

with subtest('to_str'):
    string = date.to_str()
    is_ok(string, 'Sun, 06 Nov 1994 08:49:37 GMT', 'string')

    # "Sun, 06 Nov 1994 08:49:37 GMT"
    is_ok(Pyjo.Date.new(784111777).to_str(), 'Sun, 06 Nov 1994 08:49:37 GMT', 'Pyjo.Date.new(784111777).to_str()')

done_testing()
