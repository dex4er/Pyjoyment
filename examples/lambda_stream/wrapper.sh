#!/bin/sh
# The wrapper of AWS_LAMBDA_EXEC_WRAPPER, which runs the runtime client of
# Pyjo.Server.Lambda in the place of the one of the managed runtime of Python,
# which does not stream: Lambda passes it the command of that runtime client,
# which it leaves out, and the runtime client takes the handler of _HANDLER.
exec python3 -m Pyjo.Server.Lambda
