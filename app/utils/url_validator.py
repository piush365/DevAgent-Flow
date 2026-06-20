"""
DevFlow Agent — URL Validator
Prevents Server-Side Request Forgery (SSRF) by validating that
user-supplied URLs resolve to public internet addresses only.
"""

import ipaddress
import logging
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# RFC 1918 private ranges + reserved ranges that must be blocked
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),        # "This" network
    ipaddress.ip_network("10.0.0.0/8"),        # RFC 1918 private
    ipaddress.ip_network("100.64.0.0/10"),     # Shared address space
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local (AWS metadata, etc.)
    ipaddress.ip_network("172.16.0.0/12"),     # RFC 1918 private
    ipaddress.ip_network("192.0.0.0/24"),      # IETF protocol assignments
    ipaddress.ip_network("192.168.0.0/16"),    # RFC 1918 private
    ipaddress.ip_network("198.18.0.0/15"),     # Benchmarking
    ipaddress.ip_network("198.51.100.0/24"),   # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),    # TEST-NET-3
    ipaddress.ip_network("240.0.0.0/4"),       # Reserved
    ipaddress.ip_network("255.255.255.255/32"),# Broadcast
    # IPv6
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
]

_ALLOWED_SCHEMES = {"http", "https"}


def validate_fetch_url(url: str) -> str:
    """
    Validate that a URL is safe to fetch (SSRF prevention).

    Checks:
    - Scheme is http or https
    - Hostname is present and resolvable
    - Resolved IP is not in any private/reserved range

    Args:
        url: The URL string to validate.

    Returns:
        The original URL string if valid.

    Raises:
        ValueError: With a descriptive message if the URL fails any check.
    """
    if not url or not url.strip():
        raise ValueError("URL must not be empty.")

    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise ValueError(f"Malformed URL: {exc}") from exc

    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(
            f"URL scheme {parsed.scheme!r} is not allowed. "
            "Only 'http' and 'https' are permitted."
        )

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must contain a valid hostname.")

    # Resolve hostname to IP addresses
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError(
            f"Could not resolve hostname {hostname!r}: {exc}"
        ) from exc

    if not addr_infos:
        raise ValueError(f"Hostname {hostname!r} resolved to no addresses.")

    for _family, _type, _proto, _canonname, sockaddr in addr_infos:
        raw_ip = sockaddr[0]
        try:
            ip = ipaddress.ip_address(raw_ip)
        except ValueError:
            continue

        for network in _BLOCKED_NETWORKS:
            if ip in network:
                logger.warning(
                    "Blocked SSRF attempt: %s resolved to %s (matches %s)",
                    url,
                    ip,
                    network,
                )
                raise ValueError(
                    f"URL resolves to a private or reserved address ({ip}). "
                    "Only publicly routable URLs are permitted."
                )

    return url
