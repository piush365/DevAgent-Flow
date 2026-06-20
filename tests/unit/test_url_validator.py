"""
Unit tests for URLValidator — the SSRF prevention layer.
Uses monkeypatching on socket.getaddrinfo to avoid real DNS lookups.
"""

import socket
import pytest

from app.utils.url_validator import validate_fetch_url


def _make_addr_info(ip: str):
    """Helper to build a minimal getaddrinfo return value for a given IP."""
    return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", (ip, 0))]


class TestSchemeValidation:
    def test_https_allowed(self, mocker):
        mocker.patch(
            "socket.getaddrinfo", return_value=_make_addr_info("93.184.216.34")
        )
        assert validate_fetch_url("https://example.com/page") == "https://example.com/page"

    def test_http_allowed(self, mocker):
        mocker.patch(
            "socket.getaddrinfo", return_value=_make_addr_info("93.184.216.34")
        )
        result = validate_fetch_url("http://example.com/")
        assert result == "http://example.com/"

    def test_ftp_blocked(self):
        with pytest.raises(ValueError, match="scheme"):
            validate_fetch_url("ftp://example.com/file")

    def test_file_scheme_blocked(self):
        with pytest.raises(ValueError, match="scheme"):
            validate_fetch_url("file:///etc/passwd")

    def test_empty_string_blocked(self):
        with pytest.raises(ValueError, match="empty"):
            validate_fetch_url("")

    def test_no_scheme_blocked(self):
        with pytest.raises(ValueError):
            validate_fetch_url("example.com/page")


class TestPrivateAddressBlocking:
    """All RFC 1918 and reserved ranges must be blocked."""

    def _assert_blocked(self, mocker, ip: str, url: str = "https://evil.internal/") -> None:
        mocker.patch("socket.getaddrinfo", return_value=_make_addr_info(ip))
        with pytest.raises(ValueError, match="private or reserved"):
            validate_fetch_url(url)

    def test_localhost_127_blocked(self, mocker):
        self._assert_blocked(mocker, "127.0.0.1")

    def test_localhost_127_other_blocked(self, mocker):
        self._assert_blocked(mocker, "127.0.0.2")

    def test_rfc1918_10_blocked(self, mocker):
        self._assert_blocked(mocker, "10.0.0.1")

    def test_rfc1918_10_large_blocked(self, mocker):
        self._assert_blocked(mocker, "10.255.255.255")

    def test_rfc1918_172_16_blocked(self, mocker):
        self._assert_blocked(mocker, "172.16.0.1")

    def test_rfc1918_172_31_blocked(self, mocker):
        self._assert_blocked(mocker, "172.31.255.255")

    def test_rfc1918_192_168_blocked(self, mocker):
        self._assert_blocked(mocker, "192.168.1.1")

    def test_link_local_169_254_blocked(self, mocker):
        """169.254.x.x is the AWS/GCP instance metadata endpoint range."""
        self._assert_blocked(mocker, "169.254.169.254")

    def test_aws_metadata_endpoint_blocked(self, mocker):
        self._assert_blocked(mocker, "169.254.169.254", "http://169.254.169.254/latest/meta-data/")

    def test_zero_network_blocked(self, mocker):
        self._assert_blocked(mocker, "0.0.0.0")


class TestPublicAddressAllowed:
    def _assert_allowed(self, mocker, ip: str, url: str = "https://public.example.com/") -> None:
        mocker.patch("socket.getaddrinfo", return_value=_make_addr_info(ip))
        result = validate_fetch_url(url)
        assert result == url

    def test_public_ip_allowed(self, mocker):
        self._assert_allowed(mocker, "93.184.216.34")

    def test_cloudflare_dns_allowed(self, mocker):
        self._assert_allowed(mocker, "1.1.1.1")

    def test_google_dns_allowed(self, mocker):
        self._assert_allowed(mocker, "8.8.8.8")


class TestDnsErrors:
    def test_unresolvable_host_blocked(self, mocker):
        mocker.patch(
            "socket.getaddrinfo",
            side_effect=socket.gaierror("Name or service not known"),
        )
        with pytest.raises(ValueError, match="Could not resolve"):
            validate_fetch_url("https://this-domain-does-not-exist.invalid/")

    def test_no_addresses_returned_blocked(self, mocker):
        mocker.patch("socket.getaddrinfo", return_value=[])
        with pytest.raises(ValueError, match="no addresses"):
            validate_fetch_url("https://empty.example.com/")
