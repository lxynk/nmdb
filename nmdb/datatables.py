from sqlalchemy.orm import joinedload
from clld.web import datatables
from clld.web.datatables.base import LinkCol, Col, LinkToMapCol

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
        if util.glossed_examples(item):
            return DetailsRowLinkCol(self.dt, '', button_text='Example').format(item)
        #return HTML.ul(*util.glossed_examples(item), class_='unstyled')
        return ''


def includeme(config):
    """register custom datatables"""

    config.register_datatable('languages', Languages)
