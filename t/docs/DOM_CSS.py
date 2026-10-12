
import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':

    from Pyjo.Test import *  # noqa

    import Pyjo.DOM.CSS

    # new
    html = Pyjo.DOM.HTML.new().parse('<html><head><title>Test</title></head></html>')
    css = Pyjo.DOM.CSS.new(tree=html.tree)
    isa_ok(css, Pyjo.DOM.CSS.object, "css")
    tree = css.tree
    is_ok(tree[0], 'root', "tree")

    # matches
    ok(Pyjo.DOM.CSS.new(tree=html.tree[1]).matches('html'), "css.matches()")

    # select
    elements = css.select('head > title')
    isa_ok(elements, list, 'elements')
    is_ok(elements[0][0], 'tag', "elements[0][0]")
    is_ok(elements[0][1], 'title', "elements[0][1]")

    # select_one
    elements = css.select_one('head > title')
    isa_ok(elements, list, 'elements')
    is_ok(elements[0], 'tag', "elements[0]")
    is_ok(elements[1], 'title', "elements[1]")

    done_testing()
