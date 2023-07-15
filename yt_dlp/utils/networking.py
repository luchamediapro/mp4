import collections
import random
import urllib.parse
import urllib.request

from ._utils import remove_start


def random_user_agent():
    _USER_AGENT_TPL = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/%s Safari/537.36'
    _CHROME_VERSIONS = (
        '103.0.5060.139',
        '103.0.5060.14',
        '103.0.5060.140',
        '103.0.5060.141',
        '103.0.5060.142',
        '104.0.5112.127',
        '104.0.5112.128',
        '104.0.5112.129',
        '104.0.5112.93',
        '104.0.5112.94',
        '104.0.5112.95',
        '104.0.5112.96',
        '104.0.5112.97',
        '104.0.5112.98',
        '104.0.5112.99',
        '105.0.5195.145',
        '105.0.5195.146',
        '105.0.5195.147',
        '105.0.5195.94',
        '105.0.5195.95',
        '105.0.5195.96',
        '105.0.5195.97',
        '105.0.5195.98',
        '105.0.5195.99',
        '105.0.5195.127',
        '106.0.5196.0',
        '106.0.5196.1',
        '106.0.5197.0',
        '107.0.5304.107',
        '107.0.5304.123',
        '108.0.5359.125',
        '111.0.5563.64',
        '111.0.5563.111',
        '112.0.5615.138',
        '113.0.5672.93',
        '113.0.5672.127',
        '114.0.5735.110',
        '114.0.5735.134',
        '114.0.5735.199',  # Current chrome version on Win10x64
    )
    return _USER_AGENT_TPL % random.choice(_CHROME_VERSIONS)


class HTTPHeaderDict(collections.UserDict, dict):
    """
    Store and access keys case-insensitively.
    The constructor can take multiple dicts, in which keys in the latter are prioritised.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        for dct in args:
            if dct is not None:
                self.update(dct)
        self.update(kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key.title(), str(value))

    def __getitem__(self, key):
        return super().__getitem__(key.title())

    def __delitem__(self, key):
        super().__delitem__(key.title())

    def __contains__(self, key):
        return super().__contains__(key.title() if isinstance(key, str) else key)


std_headers = HTTPHeaderDict({
    'User-Agent': random_user_agent(),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-us,en;q=0.5',
    'Sec-Fetch-Mode': 'navigate',
})


def clean_proxies(proxies: dict, headers: HTTPHeaderDict):
    req_proxy = headers.pop('Ytdl-Request-Proxy', None)
    if req_proxy:
        proxies.clear()  # XXX: compat: Ytdl-Request-Proxy takes preference over everything, including NO_PROXY
        proxies['all'] = req_proxy
    for proxy_key, proxy_url in proxies.items():
        if proxy_url == '__noproxy__':
            proxies[proxy_key] = None
            continue
        if proxy_key == 'no':  # special case
            continue
        if proxy_url is not None:
            # Ensure proxies without a scheme are http.
            proxy_scheme = urllib.request._parse_proxy(proxy_url)[0]
            if proxy_scheme is None:
                proxies[proxy_key] = 'http://' + remove_start(proxy_url, '//')

            replace_scheme = {
                'socks5': 'socks5h',  # compat: socks5 was treated as socks5h
                'socks': 'socks4'  # compat: non-standard
            }
            if proxy_scheme in replace_scheme:
                proxies[proxy_key] = urllib.parse.urlunparse(
                    urllib.parse.urlparse(proxy_url)._replace(scheme=replace_scheme[proxy_scheme]))


def clean_headers(headers: HTTPHeaderDict):
    if 'Youtubedl-No-Compression' in headers:  # compat
        del headers['Youtubedl-No-Compression']
        headers['Accept-Encoding'] = 'identity'
