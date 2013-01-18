# -*- coding: utf-8 -*-
from collections import defaultdict

import polib
from carcade.environments import create_jinja2_env


def get_template_source(jinja2_env, template):
    template_source, _, _ = \
        jinja2_env.loader.get_source(jinja2_env, template)
    return template_source


def main():
    jinja2_env = create_jinja2_env()

    po = polib.POFile()
    po.metadata = {
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
    }

    messages = defaultdict(list)
    for template in jinja2_env.list_templates():
        template_source = get_template_source(jinja2_env, template)
        for (lineno, _, message) in jinja2_env.extract_translations(template_source):
            message = unicode(message)
            occurence = (template, lineno)
            messages[message].append(occurence)

    for message, occurrences in messages.iteritems():
        entry = polib.POEntry(msgid=message, msgstr=message, occurrences=occurrences)
        po.append(entry)

    po.save('./translations/initial.po')
