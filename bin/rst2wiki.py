import sys
import os
import json
from pprint import pprint

# dirty hack for locale bug (for docutils)
os.environ['LC_CTYPE'] = 'en_US.UTF8'
from docutils.core import publish_string
from rst2confluence import confluence
import requests
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()


def config_data(config=None):
    if not config:
        config = os.path.join(os.getenv('HOME'), '.wiki.json')
    with open(config) as f:
        data = json.load(f)
    return data['url'], (data['user'], data['password'])


def generate_content(filename):
    with open(filename) as f:
        rst = f.read()
    content = publish_string(rst, writer=confluence.Writer())
    return content


def push_content(content, page_id):
    hostname, auth = config_data()
    url = hostname.rstrip('/') + '/rest/api/content/{}'.format(page_id)
    page = requests.get(url, auth=auth).json()
    wrap = {"id": page['id'],
            "type": "page",
            "title": page['title'],
            "space": {"key": page['space']['key']},
            "version": {"number": page['version']['number'] + 1},
            "body": {"wiki": {"value": content,
                              "representation": "wiki"}}}
    req = requests.put(url, auth=auth,
                       headers={'Content-Type': 'application/json'},
                       data=json.dumps(wrap))
    if req.status_code != 200:
        print 'Something went wrong, analyze response:'
        pprint(req.json())


def main(filename, page_id):
    content = generate_content(filename)
    push_content(content, page_id)


if __name__ == '__main__':
    main(*sys.argv[1:])
