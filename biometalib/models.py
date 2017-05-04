from mongoengine import Document, EmbeddedDocument
from mongoengine import StringField, IntField, FloatField, \
    ListField, DictField, MapField, DateTimeField, EmbeddedDocumentField
from mongoengine.errors import ValidationError, FieldDoesNotExist

from sramongo.mongo_schema import Pubmed

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
    user_annotation = MapField(EmbeddedDocumentField(Annotation))

    meta = {'abstract': True}

class Biometa(BiometaFields):
    pass
