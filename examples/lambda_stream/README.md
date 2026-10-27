# A streaming event function of AWS Lambda

`function/app.py` is an application of `Pyjoyment.Lite` whose responses AWS
Lambda streams through a Function URL, as they are written, which the OpenTofu
of this directory deploys, with the ZIP files of `generate lambda-zip
--runtime`: the function with `app.py` and `wrapper.py`, and Pyjoyment in a
layer of its own, with a Function URL of the invoke mode `RESPONSE_STREAM`.
`/count` writes a line every half a second, which comes to the client as it is
written.

The runtime of Python of Lambda does not stream, so `wrapper.py`, which
`AWS_LAMBDA_EXEC_WRAPPER` names, runs the runtime client of
`Pyjo.Server.Lambda` in its place, and `PYJO_LAMBDA_INVOKE_MODE` tells the
application the invoke mode of the Function URL, which the function does not
learn from its invocations. Both have to agree with `invoke_mode` of the
Function URL. The runtime puts the layer in the path of Python only for its
own runtime client, so `PYTHONPATH` names the site-packages of the layer for
the one of the wrapper.

The application is the directory `function`, as the generator puts every file
of the current directory into `function.zip`, which would take the state of
OpenTofu too. The inline metadata of the script takes Pyjoyment of the
checkout.

## Running locally

The same script runs as an application of its own:

```sh
uv run python examples/lambda_stream/function/app.py daemon
curl -N http://127.0.0.1:3000/count
```

and as a streaming event function under `Pyjo.App.Lambda`, as its test does:

```sh
uv run python -m Pyjo.Prove -l t/examples/lambda_stream/app.py
```

## Deploying to AWS

The ZIP files go to `function/dist`, for the runtime of the variable
`runtime`, `python3.15` by default, and the architecture of the function,
`arm64`:

```sh
uv run --directory examples/lambda_stream/function python app.py generate lambda-zip --arch arm64 --runtime python3.15
```

OpenTofu 1.13 deploys them with the credentials and the region of the default
chain of AWS, as `AWS_PROFILE` and `AWS_REGION`, and a new build of the same
files changes nothing:

```sh
tofu -chdir=examples/lambda_stream init
tofu -chdir=examples/lambda_stream apply
```

`-var pyjoyment_layer=ARN` takes a layer of Pyjoyment that is published
already, for the same Python, in the place of `function/dist/pyjoyment.zip`.

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
