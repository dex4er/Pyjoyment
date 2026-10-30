import Pyjo.YAML

import os
import re


# The skills of the plugin of Claude Code, whose files are tested as the examples of the guides are, as an example that
# went stale teaches a coding agent the wrong thing without anyone noticing, and the skills of the project, of whoever
# changes Pyjoyment itself
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
PLUGIN = os.path.join(ROOT, 'plugins', 'pyjoyment')
SKILLS = os.path.join(PLUGIN, 'skills')
PROJECT = os.path.join(ROOT, '.claude', 'skills')


def path(skill, skills=SKILLS):
    return os.path.join(skills, skill, 'SKILL.md')


def read(skill, skills=SKILLS):
    with open(path(skill, skills), encoding='utf-8') as f:
        return f.read()


# The front matter of the skill, between the lines "---" that start the file, and the body after it
def parse(skill, skills=SKILLS):
    if not (m := re.match(r'---\n(.*?)\n---\n(.*)', read(skill, skills), re.S)):
        return None, None
    return Pyjo.YAML.load(m[1]), m[2]


# The blocks of code of a language, in their order
def blocks(skill, language='python'):
    return re.findall(rf'^```{re.escape(language)}\n(.*?)^```$', read(skill), re.M | re.S)


if __name__ == '__main__':
    from Pyjo.Test import plan

    plan(skip_all='helper module, not a test')
