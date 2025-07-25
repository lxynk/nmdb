import itertools
import collections

from pycldf import Sources
from clldutils.misc import nfilter
from clldutils.color import qualitative_colors
from clld.cliutil import Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib import bibtex

from clld_glottologfamily_plugin.util import load_families


import nmdb
from nmdb import models


def main(args):

    assert args.glottolog, 'The --glottolog option is required!'

    data = Data()
    data.add(
        common.Dataset,
        nmdb.__name__,
        id=nmdb.__name__,
        domain='',

        publisher_name="University of Göttingen",
        publisher_place="Göttingen",
        publisher_url="",
        license="http://creativecommons.org/licenses/by/4.0/",
        jsondata={
            'license_icon': 'cc-by.png',
            'license_name': 'Creative Commons Attribution 4.0 International License'},

    )


    contrib = data.add(
        common.Contribution,
        None,
        id='cldf',
        name=args.cldf.properties.get('dc:title'),
        description=args.cldf.properties.get('dc:bibliographicCitation'),
    )

    for lang in args.cldf.iter_rows('LanguageTable', 'id', 'glottocode', 'name', 'latitude', 'longitude'):
        data.add(
            models.Variety,
            lang['id'],
            id=lang['id'],
            name=lang['name'],
            latitude=lang['latitude'],
            longitude=lang['longitude'],
            glottocode=lang['glottocode'],
        )

    for rec in bibtex.Database.from_file(args.cldf.bibpath, lowercase=True):
        data.add(common.Source, rec.id, _obj=bibtex2source(rec))

    refs = collections.defaultdict(list)

    for row in args.cldf['abbreviations.csv']:
        DBSession.add(common.GlossAbbreviation(
            id=row['ID'],
            name=row['Name']
        ))

    for param in args.cldf.iter_rows('ParameterTable', 'id', 'name', 'description'):
        data.add(
            models.Feature,
            param['id'],
            id=param['id'],
            name=param['description'] or param['id'],
        )
    for pid, codes in itertools.groupby(
        sorted(
            args.cldf.iter_rows('CodeTable', 'id', 'name', 'description', 'parameterReference'),
            key=lambda v: (v['parameterReference'], v['id'])),
        lambda v: v['parameterReference'],
    ):
        codes = list(codes)
        colors = qualitative_colors(len(codes))
        for code, color in zip(codes, colors):
            data.add(
                common.DomainElement,
                code['id'],
                id=code['id'],
                name=code['name'],
                description=code['description'],
                parameter=data['Feature'][code['parameterReference']],
                jsondata=dict(color=color),
            )

    for ex in args.cldf.iter_rows('ExampleTable', 'id', 'languageReference'):
        p = data.add(
            common.Sentence,
            ex['id'],
            id=ex['id'],
            name=ex['Primary_Text'],
            analyzed='\t'.join(ex['Analyzed_Word']),
            gloss='\t'.join(ex['Gloss']),
            description=ex['Translated_Text'],
            language=data['Variety'][ex['languageReference']],
            comment=ex['Comment'],
            source=ex['Source_Comment'],
            type=ex['Grammaticality_Judgement']
        )

        ref = ex['Source'][0] if ex['Source'] else None
        if ref is None:
            continue
        else:
            sid, desc = Sources.parse(ref)
            DBSession.add(common.SentenceReference(
                sentence=p,
                source=data['Source'][sid],
                key=sid,
                description=desc
            ))

    for val in args.cldf.iter_rows(
            'ValueTable',
            'id', 'value', 'languageReference', 'parameterReference', 'codeReference', 'exampleReference', 'source'):
        if val['value'] is None:  # Missing values are ignored.
            continue
        vsid = (val['languageReference'], val['parameterReference'])
        vs = data['ValueSet'].get(vsid)
        if not vs:
            vs = data.add(
                common.ValueSet,
                vsid,
                id='-'.join(vsid),
                language=data['Variety'][val['languageReference']],
                parameter=data['Feature'][val['parameterReference']],
                contribution=contrib,
            )
        for ref in val.get('source', []):
            sid, pages = Sources.parse(ref)
            refs[(vsid, sid)].append(pages)
        v = data.add(
            common.Value,
            val['id'],
            id=val['id'],
            name=val['value'],
            description=val['Comment'],
            valueset=vs,
            domainelement=data['DomainElement'][val['codeReference']],
        )
        for exid in val['exampleReference']:
            DBSession.add(common.ValueSentence(value=v, sentence=data['Sentence'][exid]))

    for (vsid, sid), pages in refs.items():
        DBSession.add(common.ValueSetReference(
            valueset=data['ValueSet'][vsid],
            source=data['Source'][sid],
            description='; '.join(nfilter(pages))
        ))

    load_families(
        Data(),
        [(l.glottocode, l) for l in data['Variety'].values()],
        glottolog_repos=args.glottolog,
        isolates_icon='tcccccc',
        strict=False,
    )



def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
