"""HTTP helper: session, timeout, polite delay, retries with exponential backoff."""
import logging
import time

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)


class HttpClient:
    def __init__(self, delay=0.2, timeout=15, retries=3):
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        retry = Retry(
            total=retries,
            backoff_factor=1,  # 1s, 2s, 4s ...
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers["User-Agent"] = "scraping-assignment/1.0 (educational use)"

    def get_soup(self, url):
        """Return BeautifulSoup for url, or None if the request failed."""
        time.sleep(self.delay)  # rate limiting
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as exc:
            log.error("Request failed for %s: %s", url, exc)
            return None
