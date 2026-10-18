from Pyjoyment.Lite import *


def looks_like_number(value):
    try:
        float(value)
    except ValueError:
        return False
    return True


@get('/divide/:dividend/by/:divisor')
def divide(c):

    dividend = c.param('dividend')
    divisor = c.param('divisor')

    # 404
    if not looks_like_number(dividend) or not looks_like_number(divisor):
        return c.reply.not_found()

    # 500
    if float(divisor) == 0:
        return c.reply.exception('Division by zero!')

    # 200
    c.render(text=f'{float(dividend) / float(divisor):g}')


app.start()
