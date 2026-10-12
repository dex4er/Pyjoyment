"""
Pyjo.Date - HTTP date
=====================
::

    import Pyjo.Date

    # Parse
    date = Pyjo.Date.new('Sun, 06 Nov 1994 08:49:37 GMT')
    print(date.epoch)

    # Build
    date = Pyjo.Date.new(steady_time() + 60)
    print(date)

:mod:`Pyjo.Date` implements HTTP date and time functions based on
:rfc:`7230`,
:rfc:`7231` and
:rfc:`3339`.

Classes
-------
"""

import Pyjo.Base
import Pyjo.String.Mixin

from Pyjo.Regexp import r
from Pyjo.Util import notnone

import calendar
import time


DAYS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
MONTHS = (None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
MONTHNAMES = {}
for _ in range(len(MONTHS)):
    MONTHNAMES[MONTHS[_]] = _


re_epoch = r(r'^\d+$|^\d+\.\d+$')
re_rfc_822_850 = r(r'^\w+\W+(\d+)\W+(\w+)\W+(\d+)\W+(\d+):(\d+):(\d+)\W*\w+$')
re_rfc3339 = r(
    r"""
  ^(\d+)-(\d+)-(\d+)\D+(\d+):(\d+):(\d+(?:\.\d+)?)   # Date and time
  (?:Z|([+-])(\d+):(\d+))?$                          # Offset
""",
    'xi',
)
re_asctime = r(r'^\w+\s+(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+)\s+(\d+)$')


class Pyjo_Date(Pyjo.Base.object, Pyjo.String.Mixin.object):
    """
    :mod:`Pyjo.Date` inherits all attributes and methods from
    :mod:`Pyjo.Base` and :mod:`Pyjo.String.Mixin` and implements the following new ones.
    """

    def __init__(self, date=None, **kwargs):
        """::

            date = Pyjo.Date.new()
            date = Pyjo.Date.new('Sun Nov  6 08:49:37 1994')

        Construct a new :mod:`Pyjo.Date` object and :meth:`parse` date if necessary.
        """

        self.epoch = None
        """::

            epoch = date.epoch
            date.epoch = 784111777

        Epoch seconds, defaults to the current time.
        """

        if date is not None:
            self.parse(date)
        else:
            self.epoch = notnone(kwargs.get('epoch'), lambda: time.time())

    def __bool__(self):
        """::

            boolean = bool(date)

        Always true.
        """
        return True

    def parse(self, date):
        """::

            date = date.parse('Sun Nov  6 08:49:37 1994')

        Parse date. ::

            # Epoch
            print(Pyjo.Date.new('784111777').epoch)
            print(Pyjo.Date.new('784111777.21').epoch)

            # RFC 822/1123
            print(Pyjo.Date.new('Sun, 06 Nov 1994 08:49:37 GMT').epoch)

            # RFC 850/1036
            print(Pyjo.Date.new('Sunday, 06-Nov-94 08:49:37 GMT').epoch)

            # Ansi C asctime()
            print(Pyjo.Date.new('Sun Nov  6 08:49:37 1994').epoch)

            # RFC 3339
            print(Pyjo.Date.new('1994-11-06T08:49:37Z').epoch)
            print(Pyjo.Date.new('1994-11-06T08:49:37').epoch)
            print(Pyjo.Date.new('1994-11-06T08:49:37.21Z').epoch)
            print(Pyjo.Date.new('1994-11-06T08:49:37+01:00').epoch)
            print(Pyjo.Date.new('1994-11-06T08:49:37-01:00').epoch)
        """
        # epoch (784111777)
        if isinstance(date, (int, float)) or re_epoch.search(date):
            if isinstance(date, float) or not str(date).isdigit():
                self.epoch = float(date)
            else:
                self.epoch = int(date)
            return self

        # RFC 822/1123 (Sun, 06 Nov 1994 08:49:37 GMT)
        # RFC 850/1036 (Sunday, 06-Nov-94 08:49:37 GMT)
        offset = 0
        while True:
            m = re_rfc_822_850.search(date)
            if m:
                day, month, year, hh, mm, ss = (
                    int(m.group(1)),
                    MONTHNAMES.get(m.group(2)),
                    int(m.group(3)),
                    int(m.group(4)),
                    int(m.group(5)),
                    float(m.group(6)),
                )
                break

            # RFC 3339 (1994-11-06T08:49:37Z)
            m = re_rfc3339.search(date)
            if m:
                year, month, day, hh, mm, ss = (
                    int(m.group(1)),
                    int(m.group(2)),
                    int(m.group(3)),
                    int(m.group(4)),
                    int(m.group(5)),
                    float(m.group(6)),
                )
                if m.group(7):
                    offset = ((int(m.group(8)) * 3600) + (int(m.group(9)) * 60)) * (-1 if m.group(7) == '+' else 1)
                break

            # ANSI C asctime() (Sun Nov  6 08:49:37 1994)
            m = re_asctime.search(date)
            if m:
                month, day, hh, mm, ss, year = (
                    MONTHNAMES.get(m.group(1)),
                    int(m.group(2)),
                    int(m.group(3)),
                    int(m.group(4)),
                    float(m.group(5)),
                    int(m.group(6)),
                )
                break

            self.epoch = None
            return self

        try:
            if (
                year < 0
                or month < 0
                or month > 12
                or day < 0
                or day > 31
                or hh < 0
                or hh > 24
                or mm < 0
                or mm > 60
                or ss < 0
                or ss > 60
            ):
                self.epoch = None
                return self

            if year < 100:
                if year < 70:
                    year += 2000
                else:
                    year += 1900

            # Prevent crash
            epoch = calendar.timegm(
                (year, month, day, hh, mm, ss, 0, 0, -1),
            )
        except:
            epoch = None

        if epoch is not None:
            epoch += offset
            if epoch < 0:
                epoch = None

        self.epoch = epoch
        return self

    def isoformat(self, sep='T'):
        """::

            string = date.iso_format()

        Render :rfc:`3339` date and time. ::

            # "1994-11-06T08:49:37Z"
            Pyjo.Date.new(784111777).isoformat()

            # "1994-11-06T08:49:37.21Z"
            Pyjo.Date.new(784111777.21).isoformat(sep='T')
        """
        # RFC 3339 (1994-11-06T08:49:37Z)
        epoch = self.epoch
        year, month, day, h, m, s, _, _, _ = tuple(time.gmtime(epoch))
        string = f'{year:04d}-{month:02d}-{day:02d}{sep}{h:02d}:{m:02d}:{s:02d}'
        if isinstance(epoch, float):
            epoch = str(epoch)
            if not epoch.endswith('.0'):
                string += epoch[epoch.index('.') :]
        string += 'Z'
        return string

    def to_str(self):
        """::

            string = date.to_str()

        Render date suitable for HTTP messages. ::

            # "Sun, 06 Nov 1994 08:49:37 GMT"
            Pyjo.Date.new(784111777).to_str()
        """
        # RFC 7231 (Sun, 06 Nov 1994 08:49:37 GMT)
        year, month, mday, h, m, s, wday, _, _ = tuple(time.gmtime(self.epoch))
        return f'{DAYS[wday]}, {mday:02d} {MONTHS[month]} {year:04d} {h:02d}:{m:02d}:{s:02d} GMT'


new = Pyjo_Date.new
object = Pyjo_Date
