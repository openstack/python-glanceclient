

fixtures = {
    '/v1/images': {
        'POST': (
            {
                'location': '/v1/images/1',
                'x-image-meta-id': '1',
                'x-image-meta-name': 'image-1',
                'x-image-meta-property-arch': 'x86_64',
            },
            None),
    },
    '/v1/images/detail': {
        'GET': (
            {},
            {'images': [
                {
                    'id': '1',
                    'name': 'image-1',
                    'properties': {'arch': 'x86_64'},
                },
            ]},
        ),
    },
    '/v1/images/1': {
        'HEAD': (
            {
                'x-image-meta-id': '1',
                'x-image-meta-name': 'image-1',
                'x-image-meta-property-arch': 'x86_64',
            },
            None),
        'PUT': (
            {
                'x-image-meta-id': '1',
                'x-image-meta-name': 'image-2',
                'x-image-meta-property-arch': 'x86_64',
            },
            None),
        'DELETE': ({}, None),
    }
}

class FakeAPI(object):

    def __init__(self):
        self.calls = []

    def _request(self, method, url, headers=None, body=None):
        call = (method, url, headers or {}, body)
        self.calls.append(call)
        # drop any query params
        url = url.split('?', 1)[0]
        return fixtures[url][method]

    def get(self, url):
        return self._request('GET', url)

    def head(self, url):
        return self._request('HEAD', url)

    def post(self, url, headers=None, body=None):
        return self._request('POST', url, headers, body)

    def put(self, url, headers=None, body=None):
        return self._request('PUT', url, headers, body)

    def delete(self, url):
        return self._request('DELETE', url)
