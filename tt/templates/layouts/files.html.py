from Pyjo.String.Template import t


def render(c, **stash):
    return t('<title>{title}</title><body>{content}</body>', title=c.title(), content=c.content())
