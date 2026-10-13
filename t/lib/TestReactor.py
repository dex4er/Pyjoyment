import Pyjo.Reactor.Asyncio


# Dummy reactor
class TestReactor(Pyjo.Reactor.Asyncio.object):
    pass


def new():
    return TestReactor()


if __name__ == '__main__':
    from Pyjo.Test import plan

    plan(skip_all='helper module, not a test')
