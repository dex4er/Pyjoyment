# A streaming event function of AWS Lambda

`app.py` is an application of `Pyjoyment.Lite` whose responses AWS Lambda
streams through a Function URL, as they are written, which the OpenTofu of
this directory deploys: the function with `app.py` and `wrapper.py`, and the
framework, `Pyjo` and `Pyjoyment` of the checkout, in a layer of its own, with
a Function URL of the invoke mode `RESPONSE_STREAM`. `/count` writes a line
every half a second, which comes to the client as it is written.

The runtime of Python of Lambda does not stream, so `wrapper.py`, which
`AWS_LAMBDA_EXEC_WRAPPER` names, runs the runtime client of
`Pyjo.Server.Lambda` in its place, and `PYJO_LAMBDA_INVOKE_MODE` tells the
application the invoke mode of the Function URL, which the function does not
learn from its invocations. Both have to agree with `invoke_mode` of the
Function URL.

## Running locally

The same script runs as an application of its own:

```sh
uv run python examples/lambda_stream/app.py daemon
curl -N http://127.0.0.1:3000/count
```

and as a streaming event function under `Pyjo.App.Lambda`, as its test does:

```sh
uv run python -m Pyjo.Prove -l t/examples/lambda_stream/app.py
```

## Deploying to AWS

OpenTofu 1.13 deploys it with the credentials and the region of the default
chain of AWS, as `AWS_PROFILE` and `AWS_REGION`:

```sh
tofu -chdir=examples/lambda_stream init
tofu -chdir=examples/lambda_stream apply
```

The output `url` is the Function URL, which the test takes in
`TEST_LAMBDA_STREAM_URL`:

```sh
curl -N "$(tofu -chdir=examples/lambda_stream output -raw url)/count"
TEST_LAMBDA_STREAM_URL=$(tofu -chdir=examples/lambda_stream output -raw url) \
  uv run python -m Pyjo.Prove -l t/examples/lambda_stream/app.py
```

The resources go away with:

```sh
tofu -chdir=examples/lambda_stream destroy
```
