import re
import requests
from django.http import HttpResponse
from django.http import QueryDict
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


host = 'http://'
words = re.compile(r'(?P<prefix>^|\W)(?P<word>\w{6})(?P<suffix>$|\W)',re.UNICODE)
replace = r'\g<prefix>\g<word>™\g<suffix>'


def proxy_view(request, urlt, requests_args=None):


    url = host + urlt
    requests_args = (requests_args or {}).copy()
    headers = get_headers(request.META)
    params = request.GET.copy()

    if 'headers' not in requests_args:
        requests_args['headers'] = {}
    if 'data' not in requests_args:
        requests_args['data'] = request.body
    if 'params' not in requests_args:
        requests_args['params'] = QueryDict('', mutable=True)

    headers.update(requests_args['headers'])
    params.update(requests_args['params'])

    for key in list(headers.keys()):
        if key.lower() == 'content-length':
            del headers[key]

    requests_args['headers'] = headers
    requests_args['params'] = params

    response = requests.request(request.method, url, **requests_args)
    
    foo = response.content.decode('utf-8')

    html = BeautifulSoup(foo, 'html5lib')
    for text in html.find_all(text=True):
        text.replace_with(words.sub(replace, text))
    for link in html.find_all('a',href=True):
        link.attrs['href'] = urljoin(
            '/', link.attrs['href'][len(host):])
    content = html.prettify(formatter='html')
    proxy_response = HttpResponse(
        content,
        status=response.status_code)
    return proxy_response

def get_headers(environ):
    headers = {}
    for key, value in environ.items():
        # Sometimes, things don't like when you send the requesting host through.
        if key.startswith('HTTP_') and key != 'HTTP_HOST':
            headers[key[5:].replace('_', '-')] = value
        elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            headers[key.replace('_', '-')] = value

    return headers
