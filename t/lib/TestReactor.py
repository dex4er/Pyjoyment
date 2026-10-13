import Pyjo.Reactor.Select


# Dummy reactor
class TestReactor(Pyjo.Reactor.Select.object):
    pass


def new():
    return TestReactor()


if __name__ == '__main__':
    from Pyjo.Test import plan

    plan(skip_all='helper module, not a test')
