# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for tink.python.tink.jwt._jwt_format."""

from absl.testing import absltest
from absl.testing import parameterized
from tink.jwt import _jwt_error
from tink.jwt import _jwt_format


class JwtFormatTest(parameterized.TestCase):

  def test_base64_encode_decode_header_fixed_data(self):
    # Example from https://tools.ietf.org/html/rfc7519#section-3.1
    header = bytes([
        123, 34, 116, 121, 112, 34, 58, 34, 74, 87, 84, 34, 44, 13, 10, 32, 34,
        97, 108, 103, 34, 58, 34, 72, 83, 50, 53, 54, 34, 125
    ])
    encoded_header = b'eyJ0eXAiOiJKV1QiLA0KICJhbGciOiJIUzI1NiJ9'
    self.assertEqual(_jwt_format._base64_encode(header), encoded_header)
    self.assertEqual(_jwt_format._base64_decode(encoded_header), header)

  def test_base64_encode_decode_payload_fixed_data(self):
    # Example from https://tools.ietf.org/html/rfc7519#section-3.1
    payload = bytes([
        123, 34, 105, 115, 115, 34, 58, 34, 106, 111, 101, 34, 44, 13, 10, 32,
        34, 101, 120, 112, 34, 58, 49, 51, 48, 48, 56, 49, 57, 51, 56, 48, 44,
        13, 10, 32, 34, 104, 116, 116, 112, 58, 47, 47, 101, 120, 97, 109, 112,
        108, 101, 46, 99, 111, 109, 47, 105, 115, 95, 114, 111, 111, 116, 34,
        58, 116, 114, 117, 101, 125
    ])
    encoded_payload = (b'eyJpc3MiOiJqb2UiLA0KICJleHAiOjEzMDA4MTkzODAsDQogImh0'
                       b'dHA6Ly9leGFtcGxlLmNvbS9pc19yb290Ijp0cnVlfQ')
    self.assertEqual(_jwt_format._base64_encode(payload), encoded_payload)
    self.assertEqual(_jwt_format._base64_decode(encoded_payload), payload)

  def test_base64_decode_fails_with_unknown_chars(self):
    self.assertNotEmpty(
        _jwt_format._base64_decode(
            b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
    )
    self.assertEqual(_jwt_format._base64_decode(b''), b'')
    with self.assertRaises(_jwt_error.JwtInvalidError):
      _jwt_format._base64_decode(b'[')
    with self.assertRaises(_jwt_error.JwtInvalidError):
      _jwt_format._base64_decode(b'@')
    with self.assertRaises(_jwt_error.JwtInvalidError):
      _jwt_format._base64_decode(b'/')
    with self.assertRaises(_jwt_error.JwtInvalidError):
      _jwt_format._base64_decode(b':')
    with self.assertRaises(_jwt_error.JwtInvalidError):
      _jwt_format._base64_decode(b'{')

  def test_decodeencode_header_hs256(self):
    # Example from https://tools.ietf.org/html/rfc7515#appendix-A.1
    encoded_header = b'eyJ0eXAiOiJKV1QiLA0KICJhbGciOiJIUzI1NiJ9'
    json_header = _jwt_format.decode_header(encoded_header)
    self.assertEqual(json_header['alg'], 'HS256')
    self.assertEqual(json_header['typ'], 'JWT')
    self.assertEqual(
        _jwt_format.decode_header(_jwt_format.encode_header(json_header)),
        json_header)

  def test_decodeencode_header_rs256(self):
    # Example from https://tools.ietf.org/html/rfc7515#appendix-A.2
    encoded_header = b'eyJhbGciOiJSUzI1NiJ9'
    json_header = _jwt_format.decode_header(encoded_header)
    self.assertEqual(json_header['alg'], 'RS256')
    self.assertEqual(
        _jwt_format.decode_header(_jwt_format.encode_header(json_header)),
        json_header)

  def testdecode_header(self):
    encoded_header = _jwt_format._base64_encode(b'{"alg":"RS256"}')
    json_header = _jwt_format.decode_header(encoded_header)
    self.assertEqual(json_header['alg'], 'RS256')

  def testdecode_header_without_quotes(self):
    encoded_header = _jwt_format._base64_encode(b'{alg:"RS256"}')
    with self.assertRaises(_jwt_error.JwtInvalidError):
      _jwt_format.decode_header(encoded_header)

  @parameterized.parameters([
      'HS256', 'HS384', 'HS512', 'ES256', 'ES384', 'ES512', 'RS256', 'RS384',
      'RS384', 'RS512', 'PS256', 'PS384', 'PS512'
  ])
  def test_create_validate_header(self, algorithm):
    header = _jwt_format.create_header(algorithm)
    _jwt_format.validate_header(header, algorithm)

  def test_create_unknown_header_fails(self):
    with self.assertRaises(_jwt_error.JwtInvalidError):
      _jwt_format.create_header('unknown')

  def test_verify_wrong_header_fails(self):
    header = _jwt_format.create_header('HS256')
    with self.assertRaises(_jwt_error.JwtInvalidError):
      _jwt_format.validate_header(header, 'ES256')

  def test_verify_empty_header_fails(self):
    header = _jwt_format.encode_header({})
    with self.assertRaises(_jwt_error.JwtInvalidError):
      _jwt_format.validate_header(header, 'ES256')

  def test_validate_header_with_unknown_algorithm_fails(self):
    header = _jwt_format.encode_header({})
    with self.assertRaises(_jwt_error.JwtInvalidError):
      _jwt_format.validate_header(header, 'HS123')

  def test_validate_header_with_uppercase_typ_success(self):
    header = _jwt_format.encode_header({'alg': 'HS256', 'typ': 'JWT'})
    _jwt_format.validate_header(header, 'HS256')

  def test_validate_header_with_lowercase_typ_success(self):
    header = _jwt_format.encode_header({'alg': 'HS256', 'typ': 'jwt'})
    _jwt_format.validate_header(header, 'HS256')

  def test_validate_header_with_bad_typ_fails(self):
    header = _jwt_format.encode_header({'alg': 'HS256', 'typ': 'IWT'})
    with self.assertRaises(_jwt_error.JwtInvalidError):
      _jwt_format.validate_header(header, 'HS256')

  def test_json_decode_encode_payload_fixed_data(self):
    # Example from https://tools.ietf.org/html/rfc7519#section-3.1
    encoded_payload = (b'eyJpc3MiOiJqb2UiLA0KICJleHAiOjEzMDA4MTkzODAsDQogImh0'
                       b'dHA6Ly9leGFtcGxlLmNvbS9pc19yb290Ijp0cnVlfQ')
    json_payload = _jwt_format.decode_payload(encoded_payload)
    payload = _jwt_format.json_loads(json_payload)
    self.assertEqual(payload['iss'], 'joe')
    self.assertEqual(payload['exp'], 1300819380)
    self.assertEqual(payload['http://example.com/is_root'], True)
    self.assertEqual(
        _jwt_format.decode_payload(_jwt_format.encode_payload(json_payload)),
        json_payload)

  def test_decode_encode_payload(self):
    # Example from https://tools.ietf.org/html/rfc7519#section-3.1
    encoded_payload = (b'eyJpc3MiOiJqb2UiLA0KICJleHAiOjEzMDA4MTkzODAsDQogImh0'
                       b'dHA6Ly9leGFtcGxlLmNvbS9pc19yb290Ijp0cnVlfQ')
    json_payload = _jwt_format.decode_payload(encoded_payload)
    payload = _jwt_format.json_loads(json_payload)
    self.assertEqual(payload['iss'], 'joe')
    self.assertEqual(payload['exp'], 1300819380)
    self.assertEqual(payload['http://example.com/is_root'], True)
    self.assertEqual(
        _jwt_format.decode_payload(_jwt_format.encode_payload(json_payload)),
        json_payload)

  def test_create_unsigned_compact_success(self):
    self.assertEqual(
        _jwt_format.create_unsigned_compact('RS256', '{"iss":"joe"}'),
        b'eyJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJqb2UifQ')

  def test_encode_decode_signature_success(self):
    signature = bytes([
        116, 24, 223, 180, 151, 153, 224, 37, 79, 250, 96, 125, 216, 173, 187,
        186, 22, 212, 37, 77, 105, 214, 191, 240, 91, 88, 5, 88, 83, 132, 141,
        121
    ])
    encoded = _jwt_format.encode_signature(signature)
    self.assertEqual(encoded, b'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk')
    self.assertEqual(_jwt_format.decode_signature(encoded), signature)

  def test_create_signed_compact(self):
    unsigned_compact = b'eyJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJqb2UifQ'
    signature = _jwt_format.decode_signature(
        b'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk')
    self.assertEqual(
        _jwt_format.create_signed_compact(
            unsigned_compact, signature),
        'eyJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJqb2UifQ.'
        'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk')

if __name__ == '__main__':
  absltest.main()
