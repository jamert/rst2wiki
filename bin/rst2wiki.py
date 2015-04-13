import os
import json
from pprint import pprint
import argparse

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


def push_content(content, page_id, config):
    hostname, auth = config_data(config)
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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--config',
        help='configuration file location (default: ~/.wiki.json)')
    parser.add_argument('source', help='reST source file')
    parser.add_argument('page_id', help='page id in confluence', type=int)
    args = parser.parse_args()
    return args.config, args.source, args.page_id


def main(config, filename, page_id):
    content = generate_content(filename)
    push_content(content, page_id, config)


if __name__ == '__main__':
    config, source, page_id = parse_args()
    main(config, source, page_id)
