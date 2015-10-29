#!/usr/bin/env python
# coding=utf-8
import os
import json
from pprint import pprint

import click
# dirty hack for locale bug (for docutils)
os.environ['LC_CTYPE'] = 'en_US.UTF8'
from docutils.core import publish_string
from rst2confluence import confluence
import requests
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()


def config_data(config):
    with open(config) as f:
        data = json.load(f)
    return data['url'], (data['user'], data['password'])


def generate_content(filename):
    with open(filename) as f:
        rst = f.read()
    content = publish_string(rst, writer=confluence.Writer())

    autogenerated_docs_tip = "{note:title=Автогенерируемая документация}\n" \
                             "Эта страница обновляется из файлов документации " \
                             "в пакете программного продукта.\n" \
                             "Учтите, что изменения, внесённые в страницу, могут быть " \
                             "перезаписаны при следующем обновлении документации.\n" \
                             "Автор страницы получит письмо об изменении страницы и, возможно, " \
                             "внесёт изменения в файлы документации.\n" \
                             "{note}\n"

    return autogenerated_docs_tip + content


def push_content(content, page_id, ancestor_page_id=None, config=None):
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
    if ancestor_page_id:
        wrap['ancestors'] = [{'type': 'page', 'id': ancestor_page_id}]

    req = requests.put(url, auth=auth,
                       headers={'Content-Type': 'application/json'},
                       data=json.dumps(wrap))
    if req.status_code != 200:
        click.echo('Something went wrong, analyze response:')
        pprint(req.json())


def required(ctx, param, value):
    if value is None:
        raise click.BadParameter('option is required')
    else:
        return value


@click.command()
@click.argument('source', type=click.Path(exists=True, dir_okay=False))
@click.option('-p', '--page', type=click.INT,
              callback=required,
              help='page id in Confluence')
@click.option('-a', '--ancestor', type=click.INT,
              help='ancestor page id in Confluence')
@click.option('-c', '--config',
              type=click.Path(resolve_path=True),
              default=os.path.join(os.getenv('HOME'), '.wiki.json'),
              help='configuration file (default: ~/.wiki.json)')
@click.version_option()
def main(source, page, ancestor, config):
    """
    Tool converts SOURCE file in reStructuredText format to confluence
    wiki format and pushes it in Confluence instance
    """
    content = generate_content(source)
    push_content(content, page, ancestor, config)


if __name__ == '__main__':
    main()
