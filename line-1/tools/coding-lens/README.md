# Content Coding Lens

Diagnose an endpoint whose response uses gzip, including damaged compressed
streams and excessive expansion. Endpoint Sentry deliberately refuses compressed
responses; this separate Python 3.10+ standard-library tool requests gzip and
checks it with independent encoded and decoded byte budgets. It makes one
anonymous HTTPS GET, follows no redirect, and retains no response body.

From the repository root, this command works entirely offline:

```sh
python3 -B line-1/tools/coding-lens/coding_lens.py --demo
```

The explicitly synthetic demonstration prints three cases: a valid gzip stream
is complete, a shortened trailer is `gzip_incomplete`, and a decoded byte budget
one byte below the payload is `decoded_limit`. It sends no request and returns
0 when the demonstration finishes. Synthetic examples are not live evidence.

## Tried on the real swarm

A fresh read of `https://api.imd.fun/launches` at **2026-10-16 09:07:23 UTC**
returned HTTP 200 with gzip and chunked transfer coding. Coding Lens admitted
**23,964 encoded bytes and 125,111 decoded bytes**, checked one complete gzip
member, and finished in 377.668 ms under its eight-second process budget.
The expansion ratio was 5.22079. The body-free result is retained in
[observed-live41.json](observed-live41.json); it is a historical observation,
not a claim of current availability or payload correctness.

This was the command, which can also make a new observation:

```sh
python3 -B line-1/tools/coding-lens/coding_lens.py --url https://api.imd.fun/launches --deadline 8 --max-encoded 262144 --max-decoded 1048576
```

The request carries its own `Pepeolithic-Coding-Lens/1.0` User-Agent and
`Accept-Encoding: gzip, identity;q=0.5`. No coin or payment is required.

## Reading the result

`capture_complete` means that the supported coding and observed transfer passed
the checks below. `http_success` separately means HTTP 200–299. `ok` requires
both, so a completely decoded 404 still exits 1. Exit 0 means `ok`; exit 1 means
a failed HTTP status, refused coding, incomplete capture, budget failure or
watchdog failure; exit 2 means invalid arguments. No redirects are followed.

`encoded_bytes` counts the received body after HTTP chunk framing is removed;
`decoded_bytes` counts the expanded payload. Both are independent of TLS bytes
and HTTP header size. The hashes appear only after a complete admitted capture.
On byte-budget failure a count may include one sentinel byte beyond its limit.
A whole-process timeout discards partial evidence and kills and reaps its worker.

Supported content codings are absent/identity and a single `gzip` coding. Up to
16 concatenated gzip members are supported, including empty members. Gzip
headers, stream termination, CRC and size trailers are checked by the standard
library's zlib decoder. A truncated member, corrupt trailer, trailing garbage,
extra zero padding, or a seventeenth member is refused. Stacked codings,
`deflate`, `br`, `zstd` and duplicate Content-Encoding fields are unsupported;
the tool never guesses or tries another encoding.

The default encoded and decoded budgets are each 1 MiB; each can be set from
1 byte through 16 MiB. Streaming decoding stops after at most one decoded
sentinel byte beyond its budget and never retains the decoded body. The CLI's
process watchdog covers DNS, TLS, response headers, body reads and decoding;
its deadline must be positive and at most 30 seconds. Direct calls to `observe`
have cooperative/socket bounds only; `run` and the CLI supply the watchdog.
Process startup and kill/reap scheduling add small overhead around the budget.

## Framing and limits of the evidence

Content-Length values must be bounded ASCII decimals and agree. Their value is
compared with the observed encoded length, including short reads that the HTTP
library otherwise accepts quietly. Transfer-Encoding plus Content-Length,
unsupported transfer coding, and disagreement with the library's recognition
of `chunked` are refused. Only Content-Encoding, Content-Length and
Transfer-Encoding are retained, capped at 20 fields and 4096 characters each.
Other headers, cookies and payload bytes are omitted. Metadata on a 304 refers
to a representation; no gzip member is expected for its absent message body.

`framing_assurance` distinguishes an explicit matching length, status-defined
absence of a body, library-parsed chunking, and connection closure alone.
Chunk framing is handled by `http.client`, not audited as raw wire bytes.
Missing data chunks or a missing zero chunk are rejected, but the library
accepts EOF after a zero chunk without the final empty trailer line. This lens
also accepts that case and reports `http_library_parsed_chunked`; it does not
claim strict HTTP conformance. Close-delimited responses have no independent
promised length, even when all observed gzip members validate. A valid gzip
checksum establishes consistency of the received stream, not the application's
intended content, authenticity, complete intended member count, or future health.

Use only public, non-secret URLs whose GET semantics you trust. Known nonpublic
IP literals and localhost names are rejected, but hostnames are not filtered
against their DNS results: this is not an SSRF boundary for untrusted input.
URLs, including query strings, appear in reports. Connections are direct,
without proxy/environment discovery, credentials or cookies. There are no
retries, writes to the service, authentication, signing, wallet operations,
transactions, payments, background monitoring or body downloads to disk.

## Offline checks

```sh
python3 -B -m unittest discover -s line-1/tools/coding-lens -v
```

All **24 delivered tests** pass. They exercise bytewise gzip input, exact and
exceeded budgets, CRC/size corruption, concatenated/empty members, truncated
members, unsupported codings, real HTTPResponse parsing of short lengths and
interrupted chunks, parser tolerance and disagreement, no-body metadata, header
allowlisting/bounds, status separation, response cleanup on early failure,
CLI behavior, and a real local worker timeout without network. An independent
review also passed 11 adversarial tests in disposable scratch space; that review
is local evidence, not independent certification. No installed dependency or
network is needed for the demonstration or delivered tests.

The bounded GET/report and process-watchdog designs reuse ideas from the
existing Endpoint Sentry, Accept Lens and Deadline Sentry; this folder imports
none of those tools. The gzip decoder and coding-specific tests are new.
