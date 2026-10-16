#!/usr/bin/env python3
"""Bounded, anonymous HTTPS GET diagnosis for identity and gzip content coding."""

import argparse
import datetime as dt
import gzip
import hashlib
import http.client
import ipaddress
import json
import math
from pathlib import Path
import re
import ssl
import subprocess
import sys
import time
import urllib.parse
import zlib

SCHEMA = 'coding-lens/v1'
USER_AGENT = 'Pepeolithic-Coding-Lens/1.0 (public read-only diagnostics)'
MAX_BYTES = 16777216
MAX_MEMBERS = 16


class CodingError(ValueError):
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def validate_url(value):
    if (not isinstance(value, str) or not value or len(value) > 4096
            or any(ord(c) <= 32 or ord(c) == 127 for c in value)):
        raise ValueError('use an ASCII HTTPS URL of at most 4096 characters without controls')
    value.encode('ascii')
    parsed = urllib.parse.urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.fragment):
        raise ValueError('use an absolute HTTPS URL without credentials or fragment')
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise ValueError('port must be in 1..65535')
    host = parsed.hostname.rstrip('.').lower()
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if host == 'localhost' or host.endswith(('.localhost', '.local')):
            raise ValueError('use a public host')
    else:
        if not address.is_global:
            raise ValueError('use a public host')
    return parsed


def validate_limits(deadline, max_encoded, max_decoded):
    if not math.isfinite(deadline) or not 0 < deadline <= 30:
        raise ValueError('deadline must be finite, positive and at most 30 seconds')
    for label, number in (('max-encoded', max_encoded), ('max-decoded', max_decoded)):
        if type(number) is not int or not 1 <= number <= MAX_BYTES:
            raise ValueError(label + ' must be in 1..16777216')


class Decoder:
    """Incremental decoder: no retained body, at most budget+1 decoded bytes."""
    def __init__(self, coding, max_decoded):
        if coding not in ('identity', 'gzip'):
            raise CodingError('unsupported_coding', 'Only identity and a single gzip content coding are supported.')
        self.coding = coding
        self.limit = max_decoded
        self.size = 0
        self.members = 0
        self.digest = hashlib.sha256()
        self.decoder = None

    def _admit(self, chunk):
        self.size += len(chunk)
        if self.size > self.limit:
            raise CodingError('decoded_limit', 'Decoded body exceeds its byte budget.')
        self.digest.update(chunk)

    def feed(self, data):
        if self.coding == 'identity':
            # Count no more than the single sentinel byte beyond the budget.
            self._admit(data[:self.limit + 1 - self.size])
            return
        while data:
            if self.decoder is None or self.decoder.eof:
                if self.members >= MAX_MEMBERS:
                    raise CodingError('member_limit', 'More than 16 concatenated gzip members are refused.')
                self.decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
            try:
                output = self.decoder.decompress(data, self.limit + 1 - self.size)
            except zlib.error:
                raise CodingError('gzip_integrity', 'Invalid gzip header, compressed stream, CRC or size trailer.') from None
            self._admit(output)
            if self.decoder.eof:
                self.members += 1
                data = self.decoder.unused_data
            else:
                data = self.decoder.unconsumed_tail

    def finish(self):
        if self.coding == 'gzip' and (self.decoder is None or not self.decoder.eof):
            raise CodingError('gzip_incomplete', 'Gzip body ended before a complete member and trailer.')
        return {'decoded_bytes': self.size, 'decoded_sha256': self.digest.hexdigest(),
                'gzip_members': self.members}


def headers_and_framing(response):
    allowed = {'content-encoding', 'content-length', 'transfer-encoding'}
    fields = [[name.lower(), value] for name, value in response.getheaders()
              if name.lower() in allowed]
    if len(fields) > 20 or any(len(value) > 4096 for _, value in fields):
        raise CodingError('header_limit', 'Coding/framing metadata exceeds its bounded allowance.')
    values = {name: [value for key, value in fields if key == name] for name in allowed}
    encodings = values['content-encoding']
    coding = encodings[0].strip(' \t').lower() if len(encodings) == 1 else 'identity' if not encodings else 'unsupported'
    lengths = [item.strip(' \t') for value in values['content-length'] for item in value.split(',')]
    length = None
    if lengths:
        if any(not re.fullmatch('[0-9]{1,20}', item) for item in lengths):
            raise CodingError('framing', 'Content-Length is not a bounded ASCII decimal list.')
        if len({int(item) for item in lengths}) != 1:
            raise CodingError('framing', 'Content-Length values disagree.')
        length = int(lengths[0])
    transfers = values['transfer-encoding']
    if transfers and lengths:
        raise CodingError('framing', 'Transfer-Encoding and Content-Length coexist.')
    if transfers and (len(transfers) != 1 or transfers[0].strip(' \t').lower() != 'chunked'):
        raise CodingError('framing', 'Only a single bare chunked transfer coding is supported.')
    no_body = response.status < 200 or response.status in (204, 304)
    if no_body:
        if response.status != 304 and (lengths or transfers):
            raise CodingError('framing', 'This no-body status forbids framing fields.')
        return fields, coding, 0, 'no_message_body'
    if transfers and not getattr(response, 'chunked', False):
        raise CodingError('framing', 'HTTP parser did not recognize the declared chunked coding.')
    return fields, coding, length, 'chunked' if transfers else 'content_length' if lengths else 'connection_close'


def observe(url, deadline=10, max_encoded=1048576, max_decoded=1048576, factory=None):
    """One GET; injected factory is only a test seam. CLI adds a process watchdog."""
    parsed = validate_url(url)
    validate_limits(deadline, max_encoded, max_decoded)
    started = time.monotonic()
    result = {'schema': SCHEMA, 'url': url, 'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'ok': False, 'capture_complete': False, 'encoded_bytes': 0, 'decoded_bytes': 0,
              'limits': {'deadline_seconds': deadline, 'max_encoded_bytes': max_encoded,
                         'max_decoded_bytes': max_decoded, 'max_gzip_members': MAX_MEMBERS}}
    connection = response = decoder = None
    stage = 'connection'
    try:
        connection = (factory or http.client.HTTPSConnection)(parsed.hostname,
            443 if parsed.port is None else parsed.port, timeout=deadline, context=ssl.create_default_context())
        target = urllib.parse.urlunsplit(('', '', parsed.path or '/', parsed.query, ''))
        stage = 'headers'
        connection.request('GET', target, headers={'User-Agent': USER_AGENT,
            'Accept': '*/*', 'Accept-Encoding': 'gzip, identity;q=0.5', 'Connection': 'close'})
        response = connection.getresponse()
        result.update(status=response.status, http_success=200 <= response.status < 300)
        fields, coding, length, framing = headers_and_framing(response)
        result.update(coding_headers=fields, content_coding=coding, framing=framing)
        if length is not None:
            result['expected_encoded_bytes'] = length
        if framing == 'no_message_body':
            # Content-Encoding on 304 describes a representation, not an empty gzip stream.
            decoder = Decoder('identity', max_decoded)
            result['coding_applies_to_body'] = False
        else:
            decoder = Decoder(coding, max_decoded)
            result['coding_applies_to_body'] = True
        encoded_digest = hashlib.sha256()
        stage = 'body'
        while framing != 'no_message_body':
            remaining = deadline - (time.monotonic() - started)
            if remaining <= 0:
                raise CodingError('deadline', 'GET deadline elapsed.')
            if connection.sock is not None:
                connection.sock.settimeout(remaining)
            chunk = response.read1(min(65536, max_encoded + 1 - result['encoded_bytes']))
            if not chunk:
                break
            result['encoded_bytes'] += len(chunk)
            if result['encoded_bytes'] > max_encoded:
                raise CodingError('encoded_limit', 'Encoded body exceeds its byte budget.')
            encoded_digest.update(chunk)
            decoder.feed(chunk)
        # read1() can quietly return EOF while Content-Length bytes remain.
        if length is not None and result['encoded_bytes'] != length:
            raise CodingError('framing', 'Body ended before the declared Content-Length.')
        if getattr(response, 'length', None) not in (None, 0):
            raise CodingError('framing', 'HTTP parser reports unread declared body bytes.')
        result.update(decoder.finish())
        result.update(capture_complete=True, encoded_sha256=encoded_digest.hexdigest(),
                      ok=result['http_success'],
                      framing_assurance={'connection_close': 'closure_only', 'chunked': 'http_library_parsed_chunked',
                                         'content_length': 'declared_length_matched',
                                         'no_message_body': 'status_has_no_body'}[framing])
        if result['encoded_bytes']:
            result['expansion_ratio'] = round(result['decoded_bytes'] / result['encoded_bytes'], 6)
    except (OSError, ValueError, UnicodeError, http.client.HTTPException) as error:
        kind = error.kind if isinstance(error, CodingError) else 'tls' if isinstance(error, ssl.SSLError) else stage
        result['error'] = {'kind': kind, 'message': str(error)[:512]}
    finally:
        if decoder is not None:
            result['decoded_bytes'] = decoder.size
        if response is not None:
            response.close()
        if connection is not None:
            connection.close()
    result['elapsed_ms'] = round((time.monotonic() - started) * 1000, 3)
    return result


def run(url, deadline=10, max_encoded=1048576, max_decoded=1048576, runner=None):
    validate_url(url)
    validate_limits(deadline, max_encoded, max_decoded)
    started = time.monotonic()
    command = [sys.executable, '-I', '-B', str(Path(__file__).resolve()), '--worker', url,
               str(deadline), str(max_encoded), str(max_decoded)]
    base = {'schema': SCHEMA, 'url': url, 'ok': False, 'capture_complete': False,
            'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
            'limits': {'deadline_seconds': deadline, 'max_encoded_bytes': max_encoded,
                       'max_decoded_bytes': max_decoded, 'max_gzip_members': MAX_MEMBERS}}
    try:
        process = (runner or subprocess.run)(command, capture_output=True, text=True,
                                              timeout=deadline, stdin=subprocess.DEVNULL, env={})
        if process.returncode != 0 or len(process.stdout) > 100000:
            raise ValueError('worker failed')
        result = json.loads(process.stdout)
        if (not isinstance(result, dict) or result.get('schema') != SCHEMA or result.get('url') != url
                or type(result.get('ok')) is not bool or type(result.get('capture_complete')) is not bool):
            raise ValueError('invalid worker report')
    except subprocess.TimeoutExpired:
        result = dict(base, error={'kind': 'deadline',
            'message': 'Whole-process budget elapsed; worker killed and reaped, partial evidence discarded.'})
    except (OSError, ValueError, UnicodeError):
        result = dict(base, error={'kind': 'worker', 'message': 'Worker did not return a valid report.'})
    result['watchdog_elapsed_ms'] = round((time.monotonic() - started) * 1000, 3)
    return result


def demo():
    """Explicit synthetic decoder exercises, no DNS/socket/files or producer claims."""
    plain = b'Public endpoint diagnosis.\n' * 100
    compressed = gzip.compress(plain, mtime=0)
    cases = [('valid_gzip', compressed, len(plain)),
             ('truncated_trailer', compressed[:-3], len(plain)),
             ('decoded_budget', compressed, len(plain) - 1)]
    rows = []
    for name, body, limit in cases:
        decoder = Decoder('gzip', limit)
        row = {'case': name, 'encoded_bytes': len(body), 'decoded_budget': limit}
        try:
            for offset in range(0, len(body), 7):
                decoder.feed(body[offset:offset + 7])
            row.update(decoder.finish(), outcome='complete')
        except CodingError as error:
            row.update(outcome=error.kind, decoded_bytes=decoder.size)
        rows.append(row)
    return {'schema': SCHEMA, 'synthetic_demo': True, 'network_requests': 0, 'cases': rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--url', help='public, non-secret HTTPS GET endpoint')
    group.add_argument('--demo', action='store_true', help='run synthetic decoder cases offline')
    parser.add_argument('--deadline', type=float, default=10)
    parser.add_argument('--max-encoded', type=int, default=1048576)
    parser.add_argument('--max-decoded', type=int, default=1048576)
    args = parser.parse_args(argv)
    try:
        validate_limits(args.deadline, args.max_encoded, args.max_decoded)
        if args.demo:
            result = demo()
        else:
            result = run(args.url, args.deadline, args.max_encoded, args.max_decoded)
    except (ValueError, UnicodeError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if args.demo or result['ok'] else 1


if __name__ == '__main__':
    if len(sys.argv) == 6 and sys.argv[1] == '--worker':
        print(json.dumps(observe(sys.argv[2], float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))))
    else:
        sys.exit(main())
