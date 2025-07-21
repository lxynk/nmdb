from sqlalchemy.orm import joinedload
from clld.web import datatables
from clld.web.datatables.base import LinkCol, Col, LinkToMapCol, DetailsRowLinkCol

from clld_glottologfamily_plugin.models import Family
from clld_glottologfamily_plugin.datatables import FamilyCol


from nmdb import models




class Languages(datatables.Languages):
    def base_query(self, query):
        return query.outerjoin(Family).options(joinedload(models.Variety.family)).distinct()

    def col_defs(self):
        return [
            LinkCol(self, 'name'),
            FamilyCol(self, 'Family', models.Variety),
            Col(self,
                'latitude',
                sDescription='<small>The geographic latitude</small>'),
            Col(self,
                'longitude',
                sDescription='<small>The geographic longitude</small>'),
            LinkToMapCol(self, 'm'),
        ]


class ExampleCol(Col):
    __kw__ = dict(bSearchable=False, bSortable=False)

    def format(self, item):
        if item.sentence_assocs:
            return DetailsRowLinkCol(self.dt, '', button_text='Example').format(item)
        #return HTML.ul(*util.glossed_examples(item), class_='unstyled')
        return ''


class Datapoints(datatables.Values):
    def col_defs(self):
        return [ExampleCol(self, 'examples')] + datatables.Values.col_defs(self)[1:3] + [Col(self, 'description', sTitle='Comment', bSearchable=False)]


def includeme(config):
    """register custom datatables"""

    config.register_datatable('languages', Languages)
    config.register_datatable('values', Datapoints)

