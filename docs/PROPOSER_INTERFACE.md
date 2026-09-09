# File-only external-model proposal interface

```sh
ascent proposer-request --task periodic --seed 17 --output request.json
```

The request contains training/development examples, grammar and task. It excludes
the audit set. Human-reviewed manual sharing may still disclose private training
information. No external API is invoked, no provider is required, and no actual
GPT or other model performance is claimed.

An external model may return ONLY an array of at most 32 typed programs:

```json
[
  {"kind":"basis","features":["sin","x","x2"],"ridge":0.001},
  {"kind":"basis","features":["x","x2"],"ridge":0.01}
]
```

Use:

```sh
ascent run workspace --task periodic --seed 17 --candidate-file candidates.json --output run.json
```

Rejected content includes source code, commands, paths, tools, evaluator changes,
self-scores, identity assertions and unknown fields. Coefficients are fitted by the
trusted engine; a proposer does not control the verifier or the approval process.

CSV data must explicitly use `split,world,x,y,proxy`. Valid split names are `train`,
`development`, `audit`; train world is `in_distribution`. Evaluation worlds must
match between development and audit, with at least two and at most six worlds.
Each split/world needs 8 to 4096 rows. Identical record overlap is rejected; this
cannot establish causal independence or eliminate semantically similar leakage.

```sh
ascent csv-import examples/custom-dataset.csv --output custom-data.json
ascent proposer-request --task custom_regression --data custom-data.json --output request.json
ascent run workspace --task custom_regression --data custom-data.json --candidate-file candidates.json --output run.json
```

A custom task rejected by the fixed-reference gate is a result, not a bug. Keep the
failed record and use an independently justified new evaluation design; do not keep
trying on disclosed audit data until a desired result appears.
