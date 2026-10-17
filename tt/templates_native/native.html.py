def render(c, items):
    return t'<ul>{[t"<li>{item}</li>" for item in items]}</ul>'
