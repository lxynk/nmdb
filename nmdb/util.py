"""
This is a modification of the rendered_sentence function from helpers.py.
Available within mako templates as 'u' instead of 'h'.
"""
import os
import re
from itertools import zip_longest, groupby  # we just import this to have it available in templates!
import datetime  # we just import this to have it available in templates!
from base64 import b64encode
from urllib.parse import quote, urlencode, urlparse, urlsplit, urlunsplit, SplitResult

from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from markupsafe import Markup
from pyramid.renderers import render as pyramid_render
from pyramid.threadlocal import get_current_request
from pyramid.interfaces import IRoutesMapper
from zope.interface import providedBy
from clldutils.misc import xmlchars
from clldutils.coordinates import degminsec

import clld
from clld import interfaces
from clld import RESOURCES
from clld.web.util.htmllib import HTML, literal
from clld.web.util.downloadwidget import DownloadWidget
from clld.db.meta import DBSession
from clld.db.models import common as models
from clld.web.adapters import get_adapter, get_adapters
from clld.lib.coins import ContextObject
from clld.lib import bibtex
from clld.lib import rdf



# regex to match standard abbreviations in gloss units:
# We look for sequences of uppercase letters which are not followed by a lowercase letter.

GLOSS_ABBR_PATTERN = re.compile(
    '(?P<personprefix>1|2|3)?(?P<abbr>[A-Z]+)(?P<personsuffix>1|2|3)?(?=([^a-z]|$))')
ALT_TRANSLATION_LANGUAGE_PATTERN = re.compile(r'((?P<language>[a-zA-Z\s]+):)')



# TODO: enumerate exceptions: 1SG, 2SG, 3SG, ?PL, ?DU

def rendered_sentence(sentence, abbrs=None, fmt='long'):
    """Format a sentence as HTML."""
    if sentence.xhtml:
        return HTML.div(
            HTML.div(Markup(sentence.xhtml), class_='body'), class_="sentence")

    if abbrs is None:
        q = DBSession.query(models.GlossAbbreviation).filter(
            or_(models.GlossAbbreviation.language_pk == sentence.language_pk,
                models.GlossAbbreviation.language_pk == None)
        )
        abbrs = dict((g.id, g.name) for g in q)

    def gloss_with_tooltip(gloss):
        person_map = {
            '1': 'first person',
            '2': 'second person',
            '3': 'third person',
        }

        res, end = [], 0
        for match in GLOSS_ABBR_PATTERN.finditer(gloss):
            if match.start() > end:
                res.append(gloss[end:match.start()])

            abbr = match.group('abbr')
            if abbr in abbrs:
                explanation = abbrs[abbr]
                if match.group('personprefix'):
                    explanation = '%s %s' % (
                        person_map[match.group('personprefix')], explanation)

                if match.group('personsuffix'):
                    explanation = '%s %s' % (
                        explanation, person_map[match.group('personsuffix')])

                res.append(HTML.span(
                    HTML.span(gloss[match.start():match.end()].lower(), class_='sc'),
                    **{'data-hint': explanation, 'class': 'hint--bottom'}))
            else:
                res.append(
                    (match.group('personprefix') or '') +  # noqa: W504
                    abbr +  # noqa: W504
                    (match.group('personsuffix') or ''))

            end = match.end()

        res.append(gloss[end:])
        return filter(None, res)

    def alt_translation(sentence):
        res = ''
        if sentence.jsondata.get('alt_translation'):
            text = sentence.jsondata['alt_translation']
            name = ''
            if ALT_TRANSLATION_LANGUAGE_PATTERN.match(text):
                name, text = [t.strip() for t in text.split(':', 1)]
                name = HTML.span(name + ': ')
            res = HTML.div(name, HTML.span(text, class_='translation'))
        return res

    units = []
    if sentence.analyzed and sentence.gloss:
        analyzed = sentence.analyzed
        glossed = sentence.gloss
        for morpheme, gloss in zip_longest(
            analyzed.split('\t'), glossed.split('\t'), fillvalue=''
        ):
            if gloss:
                html_gloss = gloss_with_tooltip(gloss)
            else:
                # When there are less glosses than morphemes, the trailing
                # morphemes 'fall down' into the gloss line.  To prevent that we
                # pad the gloss line with some white space.
                html_gloss = [literal('&#160;')]
            units.append(HTML.div(
                HTML.div(morpheme, class_='morpheme'),
                HTML.div(*html_gloss, **{'class': 'gloss'}),
                class_='gloss-unit'))

    return HTML.div(
        HTML.div(
            HTML.div(
                HTML.div(sentence.original_script, class_='original-script')
                if sentence.original_script else '',
                HTML.div(literal(sentence.markup_text or sentence.name),
                         class_='object-language'),
                HTML.div(*units, **{'class': 'gloss-box'}) if units else '',
                HTML.div(sentence.description, class_='translation')
                if sentence.description else '',
                alt_translation(sentence),
                class_='body',
            ),
            class_="sentence",
        ),
        class_="sentence-wrapper",
    )
