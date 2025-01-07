def get_headers() -> dict:
    return {
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua-mobile': "?1",
        'origin': "https://game.zoo.team",
        'x-requested-with': "org.telegram.messenger",
        'sec-fetch-site': "same-site",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://game.zoo.team/",
        'accept-language': "en-US,en;q=0.9,bn-BD;q=0.8,bn;q=0.7",
        'priority': "u=1, i"
    }


def options_headers(
    method: str,
    kwarg: dict = None
) -> dict:
    if kwarg is None:
        kwarg = {}

    excluded_keys = {'sec-ch-ua', 'sec-ch-ua-mobile',
                     'sec-ch-ua-platform', 'content-type', 'accept', 'api-hash', 'api-key', 'api-time', 'is-beta-server'}
    kwarg = {k: v for k, v in kwarg.items() if k.lower() not in excluded_keys}

    return {
        'access-control-request-method': method.upper(),
        'access-control-request-headers': 'api-hash,api-key,api-time,content-type,is-beta-server',
        ** kwarg
    }
