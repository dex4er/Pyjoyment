# Examples of JSON Schema

The [examples of json-schema.org](https://json-schema.org/learn/json-schema-examples),
of the page `pages/learn/json-schema-examples.md` of
[json-schema-org/website](https://github.com/json-schema-org/website) at the
commit
[441d2a0927](https://github.com/json-schema-org/website/tree/441d2a09271f3d0b76e01065ceb323c3b1ad7010),
under the BSD 3-clause license or the Academic Free License v3.0 of
[`LICENSE`](LICENSE). Each example is a document, as `address.json`, and its
schema, as `address.schema.json`, and `smartphone.schema.json` and
`laptop.schema.json` are the schemas that `device.schema.json` refers to by
their `$id`, as `calendar.schema.json` refers to
`geographical-location.schema.json`. The files have the JSON of the page as it
is, but the schema of the calendar, which requires `startDate` where the page
requires `dtstart`, a property that it does not have.
