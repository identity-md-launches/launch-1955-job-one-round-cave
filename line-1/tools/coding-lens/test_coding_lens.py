"""Offline adversarial decoder, HTTP parser and watchdog checks."""
import gzip
import hashlib
import http.client
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('coding_lens', HERE / 'coding_lens.py')
lens = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lens)
URL = 'https://api.imd.fun/launches'


class Socket:
    def __init__(self, wire):
        self.stream = io.BytesIO(wire)
    def makefile(self, _):
        return self.stream


class Connection:
    def __init__(self, wire):
        self.response = http.client.HTTPResponse(Socket(wire))
        self.sock = None
        self.requested = None
        self.closed = False
    def request(self, method, target, headers):
        self.requested = (method, target, headers)
    def getresponse(self):
        self.response.begin()
        return self.response
    def close(self):
        # A real Connection: close response may detach from its connection.
        self.closed = True


def wire(body, headers=None, status='200 OK'):
    if headers is None:
        headers = [('Content-Length', str(len(body)))]
    return ('HTTP/1.1 ' + status + '\r\n' + ''.join(k + ': ' + v + '\r\n' for k, v in headers)
            + '\r\n').encode('ascii') + body


class CodingTests(unittest.TestCase):
    def decode(self, body, limit=100000, chunk=1, coding='gzip'):
        decoder = lens.Decoder(coding, limit)
        for start in range(0, len(body), chunk):
            decoder.feed(body[start:start + chunk])
        return decoder.finish()

    def observe(self, body, headers=None, status='200 OK', **kwargs):
        conn = Connection(wire(body, headers, status))
        result = lens.observe(URL, factory=lambda *a, **kw: conn, **kwargs)
        self.assertTrue(conn.closed)
        self.assertTrue(conn.response.isclosed())
        self.assertEqual(conn.requested[0], 'GET')
        self.assertEqual(conn.requested[2]['User-Agent'], lens.USER_AGENT)
        self.assertEqual(conn.requested[2]['Accept-Encoding'], 'gzip, identity;q=0.5')
        return result

    def test_incremental_gzip_and_exact_decoded_limit(self):
        raw = b'payload' * 50
        result = self.decode(gzip.compress(raw), len(raw))
        self.assertEqual(result['decoded_bytes'], len(raw))
        self.assertEqual(result['decoded_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['gzip_members'], 1)

    def test_expansion_budget_uses_one_sentinel_byte(self):
        decoder = lens.Decoder('gzip', 10)
        with self.assertRaises(lens.CodingError) as caught:
            decoder.feed(gzip.compress(b'x' * 1000000))
        self.assertEqual(caught.exception.kind, 'decoded_limit')
        self.assertEqual(decoder.size, 11)

    def test_identity_budget_and_empty_body(self):
        self.assertEqual(self.decode(b'', coding='identity')['decoded_bytes'], 0)
        self.assertEqual(self.decode(b'abc', 3, coding='identity')['decoded_bytes'], 3)
        decoder = lens.Decoder('identity', 3)
        with self.assertRaises(lens.CodingError):
            decoder.feed(b'123456789')
        self.assertEqual(decoder.size, 4)

    def test_truncated_header_stream_and_trailer(self):
        body = gzip.compress(b'abcdefg' * 100)
        for cut in (0, 1, 8, 15, len(body) - 1, len(body) - 7):
            with self.subTest(cut=cut), self.assertRaises(lens.CodingError) as caught:
                self.decode(body[:cut])
            self.assertEqual(caught.exception.kind, 'gzip_incomplete')

    def test_crc_and_size_trailer_corruption(self):
        body = gzip.compress(b'payload')
        for offset in (-8, -4):
            bad = bytearray(body)
            bad[offset] ^= 1
            with self.assertRaises(lens.CodingError) as caught:
                self.decode(bytes(bad))
            self.assertEqual(caught.exception.kind, 'gzip_integrity')

    def test_concatenated_members_include_empty_members(self):
        body = b''.join(gzip.compress(raw) for raw in (b'abc', b'', b'def'))
        for chunk in (1, len(body)):
            result = self.decode(body, 6, chunk)
            self.assertEqual(result['gzip_members'], 3)
            self.assertEqual(result['decoded_sha256'], hashlib.sha256(b'abcdef').hexdigest())

    def test_member_budget_and_trailing_garbage(self):
        self.assertEqual(self.decode(gzip.compress(b'') * 16)['gzip_members'], 16)
        with self.assertRaises(lens.CodingError) as caught:
            self.decode(gzip.compress(b'') * 17)
        self.assertEqual(caught.exception.kind, 'member_limit')
        for tail in (b'garbage', b'\x00', b'\x1f\x8b'):
            with self.subTest(tail=tail), self.assertRaises(lens.CodingError):
                self.decode(gzip.compress(b'ok') + tail)

    def test_identity_http_and_no_body_output(self):
        result = self.observe(b'sensitive-looking-body')
        self.assertTrue(result['ok'])
        self.assertTrue(result['capture_complete'])
        self.assertNotIn('sensitive-looking-body', json.dumps(result))
        self.assertEqual(result['encoded_sha256'], result['decoded_sha256'])

    def test_gzip_http_with_exact_encoded_budget(self):
        body = gzip.compress(b'hello')
        result = self.observe(body, [('Content-Encoding', 'GZip'), ('Content-Length', str(len(body)))],
                              max_encoded=len(body), max_decoded=5)
        self.assertTrue(result['ok'])
        self.assertEqual(result['encoded_bytes'], len(body))
        self.assertEqual(result['decoded_bytes'], 5)
        self.assertEqual(result['gzip_members'], 1)

    def test_encoded_over_budget(self):
        body = gzip.compress(b'hello')
        result = self.observe(body, [('Content-Encoding', 'gzip'), ('Content-Length', str(len(body)))],
                              max_encoded=len(body)-1)
        self.assertEqual(result['error']['kind'], 'encoded_limit')
        self.assertEqual(result['encoded_bytes'], len(body))
        self.assertFalse(result['capture_complete'])
        self.assertNotIn('encoded_sha256', result)

    def test_parser_silent_short_content_length(self):
        body = gzip.compress(b'hello')
        result = self.observe(body, [('Content-Encoding', 'gzip'), ('Content-Length', str(len(body)+1))])
        self.assertEqual(result['error']['kind'], 'framing')
        self.assertFalse(result['capture_complete'])
        self.assertNotIn('decoded_sha256', result)

    def test_complete_and_interrupted_chunked_bodies(self):
        body = gzip.compress(b'hello')
        chunk = ('%x\r\n' % len(body)).encode() + body + b'\r\n'
        headers = [('Content-Encoding', 'gzip'), ('Transfer-Encoding', 'chunked')]
        result = self.observe(chunk + b'0\r\n\r\n', headers)
        self.assertTrue(result['capture_complete'])
        self.assertEqual(result['encoded_bytes'], len(body))
        for truncated in (chunk, chunk[:-2], chunk[:7]):
            result = self.observe(truncated, headers)
            self.assertFalse(result['capture_complete'])
            self.assertIn('error', result)

    def test_library_chunk_trailer_tolerance_is_explicit(self):
        # HTTPResponse accepts EOF after zero chunk without final empty line.
        # This is library acceptance, not proof of strict wire framing.
        result = self.observe(b'3\r\nabc\r\n0\r\n', [('Transfer-Encoding', 'chunked')])
        self.assertTrue(result['capture_complete'])
        self.assertEqual(result['framing_assurance'], 'http_library_parsed_chunked')

    def test_unsupported_and_duplicate_content_coding(self):
        for fields in ([('Content-Encoding', 'br')], [('Content-Encoding', 'gzip, gzip')],
                       [('Content-Encoding', 'gzip'), ('Content-Encoding', 'gzip')],
                       [('Content-Encoding', '')]):
            result = self.observe(b'', fields)
            self.assertEqual(result['error']['kind'], 'unsupported_coding')

    def test_ambiguous_or_malformed_framing(self):
        cases = [[('Content-Length', '3'), ('Content-Length', '4')],
                 [('Content-Length', '+3')], [('Content-Length', '3,')],
                 [('Content-Length', '3'), ('Transfer-Encoding', 'chunked')],
                 [('Transfer-Encoding', 'gzip, chunked')]]
        for fields in cases:
            with self.subTest(fields=fields):
                result = self.observe(b'abc', fields)
                self.assertEqual(result['error']['kind'], 'framing')
                self.assertFalse(result['capture_complete'])
        self.assertTrue(self.observe(b'abc', [('Content-Length', '3, 3')])['ok'])

    def test_parser_disagreement_on_chunked_whitespace(self):
        # HTTPResponse does not strip trailing whitespace from this field.
        # Refuse raw chunk frames instead of counting them as identity bytes.
        result = self.observe(b'3\r\nabc\r\n0\r\n\r\n', [('Transfer-Encoding', 'chunked ')])
        self.assertEqual(result['error']['kind'], 'framing')
        self.assertFalse(result['capture_complete'])

    def test_close_delimited_coding_retains_weaker_framing(self):
        result = self.observe(gzip.compress(b'hello'), [('Content-Encoding', 'gzip')])
        self.assertTrue(result['capture_complete'])
        self.assertEqual(result['framing_assurance'], 'closure_only')

    def test_no_body_response_metadata(self):
        result = self.observe(b'', [('Content-Encoding', 'gzip'), ('Content-Length', '999')], '304 Not Modified')
        self.assertTrue(result['capture_complete'])
        self.assertFalse(result['ok'])
        self.assertFalse(result['coding_applies_to_body'])
        self.assertEqual(result['decoded_bytes'], 0)
        self.assertTrue(self.observe(b'', [('Content-Encoding', 'gzip')], '204 No Content')['ok'])
        result = self.observe(b'', [('Content-Encoding', 'gzip'), ('Transfer-Encoding', 'chunked')], '304 Not Modified')
        self.assertTrue(result['capture_complete'])
        self.assertFalse(result['coding_applies_to_body'])
        self.assertEqual(self.observe(b'', [('Content-Length', '0')], '204 No Content')['error']['kind'], 'framing')

    def test_http_failure_separate_from_successful_decoding(self):
        result = self.observe(b'not found', status='404 Not Found')
        self.assertFalse(result['ok'])
        self.assertFalse(result['http_success'])
        self.assertTrue(result['capture_complete'])

    def test_selected_headers_allowlist_and_bounds(self):
        result = self.observe(b'', [('Set-Cookie', 'unretained'), ('Content-Length', '0')])
        self.assertNotIn('unretained', json.dumps(result))
        for fields in ([('Content-Encoding', 'x' * 4097)], [('Content-Encoding', 'gzip')] * 21):
            result = self.observe(b'', fields)
            self.assertEqual(result['error']['kind'], 'header_limit')

    def test_watchdog_discards_partial_report(self):
        def stalled(command, **kwargs):
            self.assertEqual(kwargs['env'], {})
            self.assertEqual(kwargs['timeout'], 0.01)
            raise subprocess.TimeoutExpired(command, kwargs['timeout'], output='partial')
        result = lens.run(URL, deadline=0.01, runner=stalled)
        self.assertEqual(result['error']['kind'], 'deadline')
        self.assertNotIn('partial', result)
        self.assertFalse(result['capture_complete'])

    def test_real_watchdog_kills_local_slow_worker(self):
        # No network: substitute an inert Python sleeper for the locally constructed worker.
        def local_sleeper(command, **kwargs):
            return subprocess.run([sys.executable, '-I', '-B', '-c', 'import time; time.sleep(2)'], **kwargs)
        result = lens.run(URL, deadline=0.05, runner=local_sleeper)
        self.assertEqual(result['error']['kind'], 'deadline')
        self.assertLess(result['watchdog_elapsed_ms'], 1500)

    def test_worker_protocol_and_url_refusals(self):
        for stdout in ('{}', 'null', '{broken'):
            result = lens.run(URL, runner=lambda *a, **kw: subprocess.CompletedProcess(a[0], 0, stdout))
            self.assertEqual(result['error']['kind'], 'worker')
        for url in ('http://api.imd.fun', 'https://user@api.imd.fun', 'https://api.imd.fun:0/',
                    'https://127.0.0.1/', 'https://localhost./', 'https://api.imd.fun/#part',
                    'https://api.imd.fun/\nheader'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                lens.validate_url(url)
        self.assertEqual(lens.validate_url('https://api.imd.fun:8443/').port, 8443)

    def test_demo_cli_and_invalid_argument_cli(self):
        process = subprocess.run([sys.executable, '-I', '-B', str(HERE / 'coding_lens.py'), '--demo'],
                                 capture_output=True, text=True, timeout=5, env={})
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertTrue(result['synthetic_demo'])
        self.assertEqual([row['outcome'] for row in result['cases']],
                         ['complete', 'gzip_incomplete', 'decoded_limit'])
        process = subprocess.run([sys.executable, '-I', '-B', str(HERE / 'coding_lens.py'), '--url',
                                  URL, '--deadline', 'nan'], capture_output=True, text=True, timeout=5, env={})
        self.assertEqual(process.returncode, 2)


if __name__ == '__main__':
    unittest.main()
