import Pyjo.JSON

from Pyjo.Test import *

import importlib
import os
import re
import sys


# The marketplace and the plugin of Claude Code, and the front matter of each skill, with only the fields of the format
# of Agent Skills, which other agents read too
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Skills = importlib.import_module('Skills')

PORTABLE = {'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'}


def load_json(*parts):
    with open(os.path.join(*parts), 'rb') as f:
        return Pyjo.JSON.decode_json(f.read())


with subtest('Marketplace'):
    marketplace = load_json(Skills.ROOT, '.claude-plugin', 'marketplace.json')
    is_ok(marketplace['name'], 'pyjoyment', 'name')
    ok(marketplace['owner']['name'], 'owner')
    is_ok(len(marketplace['plugins']), 1, 'one plugin')
    entry = marketplace['plugins'][0]
    is_ok(entry['source'], './plugins/pyjoyment', 'source')
    ok(os.path.isdir(Skills.PLUGIN), 'plugin exists')

with subtest('Plugin'):
    plugin = load_json(Skills.PLUGIN, '.claude-plugin', 'plugin.json')
    is_ok(plugin['name'], entry['name'], 'name of the entry')
    ok(plugin['description'], 'description')

with subtest('Skills'):
    skills = sorted(os.listdir(Skills.SKILLS))
    ok(skills, 'skills')
    for skill in skills:
        front, body = Skills.parse(skill)
        ok(front is not None, f'{skill}: front matter on the first line')
        is_deeply_ok(sorted(set(front) - PORTABLE), [], f'{skill}: portable fields')
        is_ok(front.get('name'), skill, f'{skill}: name of the directory')
        like_ok(skill, r'^[a-z0-9]+(?:-[a-z0-9]+)*$', f'{skill}: name')
        ok(len(skill) <= 64, f'{skill}: short name')
        ok(0 < len(front.get('description') or '') <= 1024, f'{skill}: description')
        ok(len(body.splitlines()) < 500, f'{skill}: short body')
        for link in re.findall(r'\]\((?!https?:)([^)]+)\)', body):
            ok(os.path.exists(os.path.join(Skills.SKILLS, skill, link)), f'{skill}: {link} exists')

done_testing()
