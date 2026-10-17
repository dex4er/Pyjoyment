from Pyjo.String.Template import t


def render(c, name):
    c.layout('files')
    c.title('Hello')
    return t('<p>Hello {name}!</p>')
