# JSON-Schema-Test-Suite

The files of the official test suite of JSON Schema,
[JSON-Schema-Test-Suite](https://github.com/json-schema-org/JSON-Schema-Test-Suite),
for draft 2020-12, as they are at the commit
[89e83a7401](https://github.com/json-schema-org/JSON-Schema-Test-Suite/tree/89e83a74014617ffbe79a56d83d14d054cd11417),
under the license in [`LICENSE`](LICENSE). `t/Pyjo/JSON_Schema_suite.py`
runs them on the validation of `Pyjo.JSON.Schema`:

```sh
mise exec -- python -m Pyjo.Prove -l t/Pyjo/JSON_Schema_suite.py
```

`tests/draft2020-12` holds the files of the keywords and the formats that the
validation supports, and `remotes` the schemas that their `$ref` refer to,
which the test adds to the registry under `http://localhost:1234/` and their
path, as the suite says. These are left out:

| Files                                                                                                        | Reason                                                          |
| ------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| `dynamicRef.json`, `optional/dynamicRef.json`                                                                | `$dynamicRef`                                                   |
| `unevaluatedItems.json`, `unevaluatedProperties.json`                                                        | `unevaluatedItems` and `unevaluatedProperties`                  |
| `vocabulary.json`, `optional/format-assertion.json`                                                          | the vocabularies of a metaschema of its own                     |
| `optional/cross-draft.json`                                                                                  | the dialects of the older drafts                                |
| `optional/dependencies-compatibility.json`                                                                   | `dependencies` of the older drafts, which 2020-12 does not have |
| `optional/format/idn-email.json`, `idn-hostname.json`, `iri.json`, `iri-reference.json`, `uri-template.json` | formats that stay annotations                                   |
| `remotes/draft2019-09`, `draft3`, `draft4`, `draft6`, `draft7`, `v1`                                         | the older drafts                                                |
| `remotes/draft2020-12/detached-dynamicref.json`, `extendible-dynamic-ref.json`, `tree.json`                  | `$dynamicRef`                                                   |
| `remotes/draft2020-12/format-assertion-*.json`, `metaschema-*.json`                                          | the vocabularies of a metaschema of its own                     |

A newer version of the suite replaces the files of these directories as they
are, without the ones that are left out.
