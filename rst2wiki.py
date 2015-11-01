#!/usr/bin/env python
# coding=utf-8
import json
import os
from pprint import pformat
import re

import click
# dirty hack for locale bug (for docutils)
os.environ['LC_CTYPE'] = 'en_US.UTF8'
from docutils.core import publish_doctree, publish_from_doctree
from docutils.nodes import comment, Text
from rst2confluence import confluence
import requests
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()


autogen_warning = {
    'off': '',
    'en': (
        '{note:title=Autogenerated documentation}\n'
        'This page is autogenerated from RST source.\n'
        'All manual changes will be lost after next update.\n'
        '{note}\n'
    ),
    'ru': (
        '{note:title=Автогенерируемая документация}\n'
        'Эта страница обновляется из файлов документации '
        'в пакете программного продукта.\n'
        'Учтите, что изменения, внесённые в страницу, могут быть '
        'перезаписаны при следующем обновлении документации.\n'
        'Автор страницы получит письмо об изменении страницы и, возможно, '
        'внесёт изменения в файлы документации.\n'
        '{note}\n'
    )

}


def config_data(config):
    if not os.path.exists(config):
        return make_config(config)

    with open(config) as f:
        data = json.load(f)
    return data['url'], (data['user'], data['password'])


def make_config(default_path):
    path = click.prompt(
        'Configuration file location',
        type=click.Path(dir_okay=False, writable=True, resolve_path=True),
        default=default_path)
    url = click.prompt('Confluence URL', type=click.STRING)
    user = click.prompt('Confluence login', type=click.STRING)
    password = click.prompt(
        'Confluence password',
        type=click.STRING,
        hide_input=True)

    with open(path, 'w') as f:
        json.dump(
            {'url': url,
             'user': user,
             'password': password}, f)
    click.echo('Wrote configuration to {}'.format(path))

    return url, (user, password)


def generate_content(filename, tip_lang):
    click.echo('Preparing content...')
    with open(filename) as f:
        rst = f.read()
    doctree = publish_doctree(rst)
    metadata = extract_metadata(doctree)
    content = publish_from_doctree(doctree, writer=confluence.Writer())
    tip_lang = tip_lang or metadata.get('warning')
    warning = autogen_warning.get(tip_lang, '')

    return warning + content, metadata


def extract_metadata(doctree):
    comments = find_comments(doctree)
    metadata = None
    for c in comments:
        metadata = parse_metadata(c) or metadata

    return metadata


def find_comments(doctree):
    acc = []
    for comment_node in doctree.traverse(condition=comment):
        text_child = list(comment_node.traverse(condition=Text,
                                                include_self=False))
        if text_child:
            text = text_child[0].astext()
            acc.append(text)

    return acc


def parse_metadata(text):
    if text.startswith('rst2wiki'):
        pattern = '''
            # argument name enclosed in ':'
            :(?P<arg>page|ancestor|title|warning):
            # whitespace
            \s
            # argument value (one word)
            (?P<val>.*)
        '''
        result = re.findall(pattern, text, flags=re.VERBOSE)
        return dict(result)
    else:
        return None


def page_url(hostname, page_id):
    return hostname.rstrip('/') + '/rest/api/content/{}'.format(page_id)


def fetch_page(page_id, hostname, auth):
    click.echo('Fetching page {}...'.format(page_id))
    url = page_url(hostname, page_id)
    response = requests.get(url, auth=auth)
    response.raise_for_status()
    return response.json()


def push_page(meta, hostname, auth):
    page_id = meta['id']
    click.echo('Writing to Confluence...')
    response = requests.put(
        page_url(hostname, page_id),
        auth=auth,
        headers={'Content-Type': 'application/json'},
        data=json.dumps(meta))
    response.raise_for_status()
    click.echo('Page {} successfully updated'.format(page_id))


def prepare_for_sending(content, page, ancestor_page=None, title=None):
    meta = {
        'id': page['id'],
        'type': 'page',
        'title': title or page['title'],
        'space': {'key': page['space']['key']},
        'version': {'number': page['version']['number'] + 1},
        'body': {'wiki': {'value': content,
                          'representation': 'wiki'}}
    }

    if ancestor_page:
        meta['ancestors'] = [{'type': 'page', 'id': ancestor_page['id']}]

        if meta['space']['key'] != ancestor_page['space']['key']:
            raise click.ClickException(
                "Your ancestor page belongs to another space ({} <> {}).\n"
                "Because it is currently not possible to change "
                "page's space\nthrough Confluence REST API, "
                "you'll need to do it manually."
                .format(meta['space']['key'],
                        ancestor_page['space']['key']))

    return meta


def publish_content(content, page_id, ancestor_id=None,
                    title=None, config=None):
    hostname, auth = config_data(config)

    try:
        page = fetch_page(page_id, hostname, auth)
        if ancestor_id:
            ancestor_page = fetch_page(ancestor_id, hostname, auth)
        else:
            ancestor_page = None

        meta = prepare_for_sending(content, page, ancestor_page, title)

        push_page(meta, hostname, auth)
    except requests.ConnectionError:
        raise click.ClickException(
            'Could not connect to hostname {}'.format(hostname))
    except requests.RequestException as e:
        click.echo('Something went wrong, analyze response from server:')
        if e.response.headers.get('Content-Type') == 'application/json':
            click.echo(pformat(e.response.json()))
        else:
            click.echo(pformat(e.response.text))
        raise click.Abort()


@click.command()
@click.argument('source', type=click.Path(exists=True, dir_okay=False))
@click.option('-p', '--page', type=click.INT,
              help='Page id in Confluence')
@click.option('-a', '--ancestor', type=click.INT,
              help='Ancestor page id in Confluence')
@click.option('-t', '--title', type=click.STRING,
              help='Page title in confluence')
@click.option('-w', '--warning', type=click.Choice(autogen_warning.keys()),
              help='Language of autogenerated warning')
@click.option('-c', '--config',
              type=click.Path(resolve_path=True),
              default=click.get_app_dir('rst2wiki', force_posix=True),
              help='Configuration file')
@click.version_option()
def main(source, page, ancestor, title, warning, config):
    """
    Tool converts SOURCE file in reStructuredText format to confluence
    wiki format and pushes it in Confluence instance.
    """
    content, metadata = generate_content(source, warning)
    # arguments from command line have priority
    page = page or metadata.get('page')
    ancestor = ancestor or metadata.get('ancestor')
    title = title or metadata.get('title')
    # we absolutely need page id
    if page is None:
        raise click.BadParameter(
            'Please provide page id using CLI or document metadata',
            param_hint='-p/--page')
    publish_content(content, page, ancestor, title, config)


if __name__ == '__main__':
    main()
