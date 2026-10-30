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
    with open(os.path.join(Skills.PLUGIN, '.claude-plugin', 'icon.png'), 'rb') as f:
        png = f.read(24)
    is_ok(png[:8], b'\x89PNG\r\n\x1a\n', 'icon is a PNG')
    is_ok(png[16:24], (512).to_bytes(4) * 2, 'icon of 512 x 512 pixels')

for title, directory in (('Skills of the plugin', Skills.SKILLS), ('Skills of the project', Skills.PROJECT)):
    with subtest(title):
        skills = sorted(os.listdir(directory))
        ok(skills, 'skills')
        for skill in skills:
            front, body = Skills.parse(skill, directory)
            ok(front is not None, f'{skill}: front matter on the first line')
            is_deeply_ok(sorted(set(front) - PORTABLE), [], f'{skill}: portable fields')
            is_ok(front.get('name'), skill, f'{skill}: name of the directory')
            like_ok(skill, r'^[a-z0-9]+(?:-[a-z0-9]+)*$', f'{skill}: name')
            ok(len(skill) <= 64, f'{skill}: short name')
            ok(0 < len(front.get('description') or '') <= 1024, f'{skill}: description')
            ok(len(body.splitlines()) < 500, f'{skill}: short body')
            for link in re.findall(r'\]\((?!https?:)([^)]+)\)', body):
                ok(os.path.exists(os.path.join(directory, skill, link)), f'{skill}: {link} exists')

# AGENTS.md names each skill of the project by its file, which other agents read as it is
with subtest('Skills of the project in AGENTS.md'):
    with open(os.path.join(Skills.ROOT, 'AGENTS.md'), encoding='utf-8') as f:
        agents = f.read()
    named = sorted(set(re.findall(r'`\.claude/skills/([a-z0-9-]+)/SKILL\.md`', agents)))
    is_deeply_ok(named, sorted(os.listdir(Skills.PROJECT)), 'every skill of the project, and no other')

done_testing()
