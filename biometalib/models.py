from collections import OrderedDict
from pkg_resources import resource_filename
from ruamel import yaml

from mongoengine import Document, EmbeddedDocument
from mongoengine import StringField, IntField, FloatField, BooleanField, \
    ListField, DictField, MapField, DateTimeField, EmbeddedDocumentField
from mongoengine.errors import ValidationError, FieldDoesNotExist

from sramongo.mongo_schema import Pubmed

# Import Cleaned Attributes and make model
with open(resource_filename('biometalib', 'data/cleaned_fields.yaml'), 'r') as fh:
    CLEANED_ATTRIBUTES = yaml.load(fh, Loader=yaml.RoundTripLoader)

_cleanedAttributesDocument = OrderedDict()
for k, v in CLEANED_ATTRIBUTES.items():
    if v['type'] == 'string':
        _cleanedAttributesDocument[k] = StringField(help_text=v['description'])
    elif v['type'] == 'int':
        _cleanedAttributesDocument[k] = IntField(help_text=v['description'])
    elif v['type'] == 'float':
        _cleanedAttributesDocument[k] = FloatField(help_text=v['description'])
    elif v['type'] == 'bool':
        _cleanedAttributesDocument[k] = BooleanField(help_text=v['description'])

CleanedAttributes = type('CleanedAttributes', (EmbeddedDocument, ), _cleanedAttributesDocument)


class Contacts(EmbeddedDocument):
    first_name = StringField()
    last_name = StringField()
    email = StringField()


class Experiment(EmbeddedDocument):
    srx = StringField()
    runs = ListField(StringField(), default=list)


class Annotation(EmbeddedDocument):
    name = StringField()
    value = StringField()


class BiometaFields(Document):
    biosample = StringField(primary_key=True, required=True)
    srs = StringField()
    gsm = StringField()
    srp = StringField()
    bioproject = StringField()
    study_title = StringField()
    study_abstract = StringField()
    description = StringField()

    contacts = ListField(EmbeddedDocumentField(Contacts), default=list)
    papers = ListField(EmbeddedDocumentField(Pubmed), default=list)
    experiments = ListField(EmbeddedDocumentField(Experiment), default=list)

    taxon_id = StringField()
    sample_title = StringField()
    sample_attributes = ListField(EmbeddedDocumentField(Annotation), default=list)

    magic = ListField(EmbeddedDocumentField(Annotation))
    mieg = ListField(EmbeddedDocumentField(Annotation))
    chen = ListField(EmbeddedDocumentField(Annotation))
    oliver = ListField(EmbeddedDocumentField(Annotation))
    nlm = ListField(EmbeddedDocumentField(Annotation))
    fear = ListField(EmbeddedDocumentField(Annotation))
    user_annotation = MapField(EmbeddedDocumentField(CleanedAttributes))

    meta = {'abstract': True}


class Biometa(BiometaFields):
    pass

