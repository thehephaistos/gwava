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
    "GWTC-4.1",
    "GWTC-5.0"
)


def fetch_all(
    path: str,
    params: Mapping[str, Any] | None = None,
    *,
    base_url: str = BASE_URL,
    session: requests.Session | None = None,
    timeout: float = 30,
) -> list[dict[str, Any]]:
    """Fetch and combine every page from a paginated GWOSC endpoint.

    Parameters
    ----------
    path:
        Absolute or relative API endpoint path. Relative paths are resolved
        against ``base_url``.
    params:
        Optional query parameters sent with the first request. Subsequent
        pages use the query string supplied by the API's ``next`` URL.
    base_url:
        Root URL of the GWOSC service. Defaults to :data:`BASE_URL`.
    session:
        Optional :class:`requests.Session` used to make requests. Supplying a
        session allows connection reuse and makes the function easier to test.
    timeout:
        Maximum number of seconds to wait for each HTTP request.

    Returns
    -------
    list of dict
        Combined objects from the ``results`` list on every response page.

    Raises
    ------
    requests.HTTPError
        If GWOSC returns an unsuccessful HTTP status code.
    requests.RequestException
        If a network, connection, or timeout error occurs.
    requests.JSONDecodeError
        If a response body cannot be decoded as JSON.
    ValueError
        If a decoded response does not contain a ``results`` list.

    Notes
    -----
    The first request receives ``params`` explicitly. Each following request
    uses the API-provided ``next`` URL, which already includes its pagination
    query parameters.
    """
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
    """Fetch event versions from selected GWOSC catalog releases.

    Parameters
    ----------
    releases:
        Catalog release names to include. Values are joined into the
        comma-separated ``release`` query parameter.
    include_default_parameters:
        If ``True``, request the preferred default parameter values for each
        event, including masses, distance, redshift, spin, and SNR when
        available.
    last_version_only:
        If ``True``, request only the latest version of each event.
    page_size:
        Maximum number of event versions requested per API page.
    session:
        Optional :class:`requests.Session` passed to :func:`fetch_all`.
    timeout:
        Maximum number of seconds to wait for each HTTP request.

    Returns
    -------
    list of dict
        Event-version records returned by all pages of the GWOSC endpoint.

    Raises
    ------
    requests.HTTPError
        If GWOSC returns an unsuccessful HTTP status code.
    requests.RequestException
        If a network, connection, or timeout error occurs.
    requests.JSONDecodeError
        If a response body cannot be decoded as JSON.
    ValueError
        If a decoded response does not contain the expected paginated
        ``results`` list.

    Notes
    -----
    Boolean values are converted to lowercase strings because the GWOSC API
    expects query values such as ``"true"`` and ``"false"``.
    """
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
