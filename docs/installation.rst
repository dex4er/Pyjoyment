Installation
============

Pyjoyment is installed from its Git repository, as the release on PyPI
predates the revival: ::

    pip install git+https://github.com/dex4er/Pyjoyment

or, in a project managed with `uv <https://docs.astral.sh/uv/>`_: ::

    uv add git+https://github.com/dex4er/Pyjoyment

The skills for coding agents that write applications with Pyjoyment are a
plugin of `Claude Code <https://code.claude.com/docs/en/plugins>`_, whose
``SKILL.md`` files other agents read too: ::

    /plugin install pyjoyment --marketplace dex4er/Pyjoyment
