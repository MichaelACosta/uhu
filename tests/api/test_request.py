# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from efu.http.auth import EFOTAV1Signature
from efu.http.request import Request

from ..utils import HTTPTestCaseMixin, EFUTestCase


class RequestTestCase(HTTPTestCaseMixin, EFUTestCase):

    def test_request_date_is_in_utc(self):
        expected = datetime.now(timezone.utc).timestamp()
        observed = Request('', 'POST').date.timestamp()
        # 60 seconds of tolerance between expected and observed
        self.assertAlmostEqual(observed, expected, delta=60)

    @patch('efu.http.request.datetime')
    def test_request_has_minimal_headers(self, mock):
        mock_date = datetime(1970, 1, 1, tzinfo=timezone.utc)
        mock.now.return_value = mock_date

        request = Request('https://localhost/', 'POST', b'\0')

        host = request.headers.get('Host')
        timestamp = request.headers.get('Timestamp')
        sha256 = request.headers.get('Content-sha256')
        api = request.headers.get('Api-Content-Type')

        self.assertEqual(len(request.headers), 5)
        self.assertEqual(host, 'localhost')
        self.assertEqual(timestamp, 0)
        self.assertEqual(api, 'application/vnd.fota-server-v1+json')
        self.assertEqual(
            sha256,
            '6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'
        )

    def test_request_does_not_send_json_content_type_by_default(self):
        request = Request('https://localhost/', 'POST')
        self.assertIsNone(request.headers.get('Content-Type'))

    def test_can_set_json_content_type(self):
        request = Request('https://localhost/', 'POST', b'{}', json=True)
        header = request.headers.get('Content-Type')
        self.assertIsNotNone(header)
        self.assertEqual(header, 'application/json')

    def test_header_content_sha256_when_bytes(self):
        payload = b'bytes'
        request = Request('localhost', 'POST', payload)
        expected = hashlib.sha256(payload).hexdigest()
        observed = request.headers.get('Content-sha256')
        self.assertEqual(observed, expected)

    def test_header_content_sha256_when_string(self):
        payload = 'string'
        request = Request('localhost', 'POST', payload)
        expected = hashlib.sha256(payload.encode()).hexdigest()
        observed = request.headers.get('Content-sha256')
        self.assertEqual(observed, expected)

    def test_prepared_headers_are_strings(self):
        request = Request('localhost', 'POST')
        headers = request.headers
        prepared_headers = request._prepare_headers()

        self.assertEqual(prepared_headers.keys(), headers.keys())

        for value in prepared_headers.values():
            self.assertIs(type(value), str)

        for header in headers:
            self.assertEqual(str(headers[header]), prepared_headers[header])

    def test_send_request(self):
        self.httpd.register_response('/', body='{"status": "ok"}')
        request = Request(self.httpd.url(), 'GET')
        response = request.send()
        self.assertEqual(response.json()['status'], 'ok')

    def test_request_is_signed(self):
        self.httpd.register_response('/signed', body='{"status": "ok"}')
        Request(self.httpd.url('/signed'), 'GET').send()
        response = self.httpd.requests[-1]
        auth_header = response.headers.get('Authorization')
        self.assertIsNotNone(auth_header)

    def test_host_header_includes_port_if_provided(self):
        req = Request('http://localhost:123', 'GET')
        expected = 'localhost:123'
        observed = req.headers.get('Host')
        self.assertEqual(observed, expected)

    def test_host_header_does_not_include_port_if_not_provided(self):
        req = Request('http://localhost', 'GET')
        expected = 'localhost'
        observed = req.headers.get('Host')
        self.assertEqual(observed, expected)

    @patch('efu.http.request.requests.request')
    def test_can_pass_extra_kwargs_to_requests(self, mock):
        Request('http://localhost', 'GET', stream=True).send()
        observed = list(mock.call_args)[1].get('stream')
        self.assertTrue(observed)


class CanonicalRequestTestCase(unittest.TestCase):

    @patch('efu.http.request.datetime')
    def test_canonical_request(self, mock):
        date = datetime(1970, 1, 1, tzinfo=timezone.utc)
        mock.now.return_value = date
        request = Request(
            'http://localhost/upload?c=3&b=2&a=1',
            'POST',
            b'\0',
        )
        expected = '''POST
/upload
a=1&b=2&c=3
accept:application/json
api-content-type:application/vnd.fota-server-v1+json
content-sha256:6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d
host:localhost
timestamp:0.0

6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'''
        self.assertEqual(request.canonical(), expected)

    def test_canonical_query(self):
        url = 'https://localhost/?c=000&bb=111&aaa=222'
        request = Request(url, 'POST')
        expected = 'aaa=222&bb=111&c=000'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_query_is_correctly_escaped(self):
        url = 'https://localhost/?to-be-scaped=scape me!&b=1&a=2'
        request = Request(url, 'POST')
        expected = 'a=2&b=1&to-be-scaped=scape%20me%21'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_query_handles_repeated_values(self):
        url = 'https://localhost/?b=3&a=3&b=2&a=2&b=1&a=1'
        request = Request(url, 'POST')
        expected = 'a=1&a=2&a=3&b=1&b=2&b=3'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_query_can_sort_escaped_repeated_values(self):
        url = 'https://localhost/?b=3&a=1&b=2&a=!&b=1&a= '
        request = Request(url, 'POST')
        expected = 'a=%20&a=%21&a=1&b=1&b=2&b=3'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_headers(self):
        request = Request('http://foo.bar.com.br', 'POST')
        request.headers = {
            'Host': 'foo.bar.com.br',
            'Content-sha256': '1234',
            'Timestamp': 123456.1234,
            'Accept': 'text/json',
        }
        expected = '''accept:text/json
content-sha256:1234
host:foo.bar.com.br
timestamp:123456.1234'''
        observed = request._canonical_headers()
        self.assertEqual(observed, expected)


class SignedRequestTestCase(HTTPTestCaseMixin, EFUTestCase):

    def test_signed_request_has_the_authorization_header(self):
        request = Request('https://127.0.0.1/upload', 'POST')
        header = request.headers.get('Authorization', None)
        self.assertIsNone(header)

        request._sign()
        header = request.headers.get('Authorization', None)
        self.assertIsNotNone(header)

    def test_signatured_is_calculated_with_right_headers(self):
        self.httpd.register_response('/')

        request = Request(self.httpd.url(), 'POST')
        self.assertIsNone(request.headers.get('Authorization', None))

        sig = EFOTAV1Signature(request, None, None).signature
        self.assertIsNone(request.headers.get('Authorization', None))

        # It is right when we sign the request
        request._sign()
        self.assertIsNotNone(request.headers.get('Authorization', None))
        self.assertEqual(sig, request.headers['Authorization'])

        del request.headers['Authorization']
        response = request.send()
        self.assertEqual(response.request.headers['Authorization'], sig)

        # It is right when we send the request
        request = Request(self.httpd.url(), 'POST')
        self.assertIsNone(request.headers.get('Authorization', None))

        sig = EFOTAV1Signature(request, None, None).signature
        self.assertIsNone(request.headers.get('Authorization', None))
        response = request.send()
        self.assertEqual(response.request.headers['Authorization'], sig)