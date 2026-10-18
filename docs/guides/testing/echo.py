import Pyjo.Test.Pyjo

from Pyjo.Test import *


# Test echo web service
t = Pyjo.Test.Pyjo.new('EchoService')
t.websocket_ok('/echo').send_ok('Hello Pyjo!').message_ok().message_is('echo: Hello Pyjo!').finish_ok()

# Test JSON web service
(
    t.websocket_ok('/echo.json')
    .send_ok({'json': {'test': [1, 2, 3]}})
    .message_ok()
    .json_message_is('/test', [1, 2, 3])
    .finish_ok()
)

done_testing()
