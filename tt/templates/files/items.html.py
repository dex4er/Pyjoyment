from Pyjo.String.Template import t


def render(c, items):
    return t('<ul>{list}</ul>', list=[c.include('files/item', item=item) for item in items])
