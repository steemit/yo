# -*- coding: utf-8 -*-
"""Renders HTML and plaintext emails for notifications."""
import os

import jinja2
from jinja2 import Environment
from jinja2 import FileSystemLoader
from premailer import transform


class TemplatesMissing(Exception):
    pass


class MalformedTemplate(Exception):
    pass


class EmailRenderer:
    def __init__(self, templates_dir):
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        # fail early if template directory is missing
        if not os.path.isdir(templates_dir):
            raise TemplatesMissing('Invalid directory: %s' % templates_dir)

    def render(self, _type, data):
        """Return a dict containing `text` and optional `html` formatted
           message for notification *_type*. """

        text_template = self.env.get_template('%s.txt' % _type)
        html_template = None
        try:
            html_template = self.env.get_template('%s.html' % _type)
        except jinja2.exceptions.TemplateNotFound:
            pass

        # the subject is defined by the first line of the text
        # template with the format: subject=<subject>
        text = text_template.render(_type=_type, **data)
        line_break = text.index('\n')
        first_line = text[0:line_break]
        text = text[line_break + 1:]
        if first_line[0:8] != 'subject=':
            raise MalformedTemplate('Missing subject= line')
        subject = first_line[8:]
        if subject == '':
            raise MalformedTemplate('Subject missing')

        retval = {'subject': subject, 'text': text, 'html': None}
        if html_template is not None:
            html = html_template.render(type=_type, subject=subject, **data)
            # inline css with premailer
            html = transform(html)
            retval['html'] = html

        return retval
