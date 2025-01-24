import json
from typing import Literal

import requests


class RequestResult:

    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        if json_data is None:
            json_data = {}
        self.json = json_data


def make_request(endpoint, method: Literal['GET', 'POST', 'DELETE', 'PATCH', 'PUT'] = 'GET', token=None, data=None, port=4443, token_type='Bearer '):
    if data is not None:
        data = json.dumps(data)

    headers = {
        'Content-Type': 'application/json',
    }
    if token is not None:
        headers['Authorization'] = token_type + token

    r = requests.request(
        method=method,
        url=f'http{"s" if port == 4443 else ""}://localhost:{port}/api/{endpoint}',
        headers=headers,
        data=data,
        verify=False,
    )

    print(f'{method} {endpoint} => {r.status_code} - {data}', flush=True)

    if r.status_code == 204:
        print()
        return RequestResult(r.status_code)

    try:
        result = r.json()
        print('JSON =>', result, end='\n\n', flush=True)
        return RequestResult(r.status_code, result)
    except json.decoder.JSONDecodeError:
        pass
