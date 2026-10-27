# An event function of AWS Lambda from ZIP files

`function/app.py` is an application of `Pyjoyment.Lite` that runs as an event
function of AWS Lambda on the custom runtime `provided.al2023`, with the ZIP
files of `generate lambda-zip`, which the OpenTofu of this directory deploys:
the layer with Python, of any version, also the free-threaded build, the
function with the application, its dependencies and the `bootstrap` that runs
the script, which is the runtime of the function itself, and a Function URL.
`/python` tells the Python that runs it and the certificates that it reads.

The application is the directory `function`, as the generator puts every file
of the current directory into `function.zip`, which would take the state of
OpenTofu too. The inline metadata of the script takes Pyjoyment of the
checkout.

## Running locally

The same script runs as an application of its own:

```sh
uv run python examples/lambda_zip/function/app.py daemon
curl http://127.0.0.1:3000/python
```

and as the runtime of an event function under `Pyjo.App.Lambda`, as its test
does:

```sh
uv run python -m Pyjo.Prove -l t/examples/lambda_zip/app.py
```

## Deploying to AWS

The ZIP files go to `function/dist`, for the architecture of the function,
`arm64` by default, and the Python that runs the generator, or the one of
`--python`, as `3.15t` for the free-threaded build:

```sh
uv run --directory examples/lambda_zip/function python app.py generate lambda-zip --arch arm64
```

OpenTofu 1.13 deploys them with the credentials and the region of the default
chain of AWS, as `AWS_PROFILE` and `AWS_REGION`, and a new build of the same
files changes nothing:

```sh
tofu -chdir=examples/lambda_zip init
tofu -chdir=examples/lambda_zip apply
```

`-var arch=x86_64` is the architecture of a build with `--arch x86_64`, and
`-var invoke_mode=RESPONSE_STREAM` makes a Function URL that streams the
responses, which the function learns from `PYJO_LAMBDA_INVOKE_MODE`.

The output `url` is the Function URL, which the test takes in
`TEST_LAMBDA_ZIP_URL`, and `python_url` its page `/python`:

```sh
curl "$(tofu -chdir=examples/lambda_zip output -raw python_url)"
TEST_LAMBDA_ZIP_URL=$(tofu -chdir=examples/lambda_zip output -raw url) \
  uv run python -m Pyjo.Prove -l t/examples/lambda_zip/app.py
```

The resources go away with:

```sh
tofu -chdir=examples/lambda_zip destroy
```
