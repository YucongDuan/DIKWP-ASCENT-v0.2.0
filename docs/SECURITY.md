# ASCENT 0.2.0 threat model

## In scope

Untrusted data-only candidates, unknown/oversized/malformed JSON, nonfinite numbers,
invalid feature names, wrong family, deceptive self-scores, reused audit content,
expired/replayed approval, parent/source mismatch, stop/resume races, and accidental
local cross-origin API use. Full source/control authority remains with the operator.

The live server binds exactly 127.0.0.1. It validates Host, rejects other Origins,
requires the server-session token on API calls, accepts bounded JSON, and permits
one research worker at a time. There is no arbitrary file path, shell, proxy,
provider credential, tool, payment or remote-publish endpoint. The root page is
available to the local user. Tokens are anti-CSRF controls, NOT identity certificates.

The registry serializes authority transitions with SQLite transactions. Audits use
a consistent read transaction. Run approval checks the source fingerprint; activation
checks record, incumbent, epoch, expiry and unused ticket in one transaction. Stop
advances the epoch. Resume never revalidates an earlier epoch's approval.

## Outside scope

A malicious same-OS-user process, host administrator, compromised interpreter or
source, stolen controller key, replacement of the entire database plus trusted
history, filesystem rollback, hardware failure, network-deployed multi-user access,
and civil identity or legal authorization. An HMAC cannot solve those problems.

Module separation is not process/container isolation. Candidates cannot supply
native code; expanding the grammar to native code is a new security design requiring
separate review. Resource checks are cooperative and bounded-built-in accounting,
not a scheduler for hostile machine code or proof of measured energy consumption.

`http.server` is not a production server. Do not forward this service through a
public tunnel, shared host, reverse proxy or a non-loopback address. Use an isolated
research OS account; protect and back up key/state together. A forced process kill
cannot guarantee a final stop event was written. After abnormal termination inspect
the audit and stopped state before reuse.

## Evidence limits

Public generators do not constitute secret holdouts. One-use audit registration
limits local repeated tuning; it does not defeat reconstructed synthetic data,
semantically duplicated observations or resetting the whole trusted controller.
The strong reference is fixed, not the best known scientific solution. Bootstrap
intervals are descriptive and do not correct unrestricted adaptive multiple testing.

## Model APIs

No network model provider is implemented or called. The proposer-request export
contains training and development data only. Before manually sending it to any
external provider, establish authorization and privacy terms. Never send controller
keys, approval tickets, private audit data or raw internal chains of thought.

## Sources

Python server warning: https://docs.python.org/3/library/http.server.html
SQLite isolation: https://www.sqlite.org/isolation.html
