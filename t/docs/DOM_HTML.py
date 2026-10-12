
import Pyjo.Test


class NoseTest(Pyjo.Test.NoseTest):
    script = __file__
    srcdir = '../..'


class UnitTest(Pyjo.Test.UnitTest):
    script = __file__


if __name__ == '__main__':

    from Pyjo.Test import *  # noqa

    import Pyjo.DOM.HTML

    html = Pyjo.DOM.HTML.new()
    isa_ok(html, Pyjo.DOM.HTML.object, "html")
    ok(html.parse('<div><p id="a">Test</p><p id="b">123</p></div>'), "html.parse()")
    tree = html.tree
    isa_ok(tree, list, "tree")
    is_ok(tree[0], 'root', "tree[0]")

    # new
    html = Pyjo.DOM.HTML.new()
    isa_ok(html, Pyjo.DOM.HTML.object, "html")
    tree = html.tree
    is_deeply_ok(tree, ['root'], "tree")
    xml = html.xml
    ok(not xml, "not xml")

    # parse
    html = html.parse('<foo bar="baz">I ♥ Pyjo!</foo>')
    isa_ok(html, Pyjo.DOM.HTML.object, "html")

    # render
    string = html.render()
    is_ok(string, '<foo bar="baz">I ♥ Pyjo!</foo>', "string")

    done_testing()
