from Pyjoyment.Lite import *

import asyncio


# Wait 3 seconds before rendering a response
@get('/')
async def index(c):
    await asyncio.sleep(3)
    c.render(text='Delayed by 3 seconds!')


app.start()
