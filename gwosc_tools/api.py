"""HTTP helpers for the GWOSC API."""

from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urljoin

import requests

BASE_URL = "https://gwosc.org"
EVENT_VERSIONS_PATH = "/api/v2/event-versions"
DEFAULT_RELEASES = (
    "GWTC-1-confident",
    "GWTC-2.1-confident",
    "GWTC-3-confident",
    "GWTC-4.1"
)


def fetch_all(
    path: str,
    params: Mapping[str, Any] | None = None,
    *,
    base_url: str = BASE_URL,
    session: requests.Session | None = None,
    timeout: float = 30,
) -> list[dict[str, Any]]:
    """Fetch every page from a paginated GWOSC endpoint."""
    url = urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))
    rows: list[dict[str, Any]] = []
    client = session or requests.Session()
    request_params = dict(params) if params is not None else None

    while url:
        response = client.get(url, params=request_params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        results = data.get("results")
        if not isinstance(results, list):
            raise ValueError("GWOSC response does not contain a 'results' list")

        rows.extend(results)
        next_url = data.get("next")
        url = urljoin(f"{base_url.rstrip('/')}/", next_url) if next_url else ""

        # The API's next-page URL already contains the query string.
        request_params = None

    return rows


def fetch_event_versions(
    releases: Sequence[str] = DEFAULT_RELEASES,
    *,
    include_default_parameters: bool = True,
    last_version_only: bool = True,
    page_size: int = 100,
    session: requests.Session | None = None,
    timeout: float = 30,
) -> list[dict[str, Any]]:
    """Fetch event versions from the selected GWOSC catalog releases."""
    params = {
        "format": "json",
        "release": ",".join(releases),
        "lastver": str(last_version_only).lower(),
        "include-default-parameters": str(include_default_parameters).lower(),
        "pagesize": page_size,
    }
    return fetch_all(
        EVENT_VERSIONS_PATH,
        params,
        session=session,
        timeout=timeout,
    )
