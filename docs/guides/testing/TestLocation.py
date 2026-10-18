import Pyjo.Test.Pyjo


class TestLocation(Pyjo.Test.Pyjo.object):
    def location_is(self, value, desc=None):
        return self.test('is', self.tx.res.headers.location, value, desc or f'Location: {value}')


new = TestLocation.new
object = TestLocation
