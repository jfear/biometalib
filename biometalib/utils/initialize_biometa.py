#!/usr/bin/env python
"""Populate fields of the Remap collection from the Ncbi collection.

This program initializes the Remap mongoDB collection to include fields from
the Ncbi collection. At this time I am only copying over identifiers. Other
metadata will eventually be copied over.
"""
import sys
import logging
import json
import mongoengine as me
from mongoengine.context_managers import switch_db
from mongoengine.errors import ValidationError
from sramongo.mongo_schema import Ncbi

sys.path.insert(0, '../')
from biometalib.models import Biometa

logger = logging.getLogger()

#TODO Change to command line options
client = me.connect(db='sra', host='localhost', port=27022)

def dict_uniqify(d):
    return [dict(y) for y in set(tuple(x.items()) for x in d)]


def get_contacts(ncbi):
    contacts = []
    for s in  ncbi.biosample:
        for contact in s.contacts:
            contacts.append({
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'email': contact.email,
            })
    return dict_uniqify(contacts)


def get_sample_attributes(ncbi):
    attributes = []
    at1 = ncbi.sra.sample.attributes
    if (at1 is not None) and (len(at1) > 0):
        for a in at1:
            a = json.loads(a.to_json())
            if (a is not None) and (len(a) > 0):
                a['name'] = a['name'].lower().replace(' ', '_')
                attributes.append(a)
    try:
        for bio in ncbi.biosample:
            at2 = bio.attributes
            if (at2 is not None) and (len(at2) > 0):
                for a in at2:
                    a = json.loads(a.to_json())
                    if (a is not None) and (len(a) > 0):
                        a['name'] = a['name'].lower().replace(' ', '_')
                        attributes.append(a)
    except:
        pass

    return dict_uniqify(attributes)


def get_sample_title(ncbi):
    titles = []
    t1 = ncbi.sra.sample.title
    if (t1 is not None) and (len(t1) > 0):
        titles.append(t1)

    try:
        for bio in ncbi.biosample:
            t2 = bio.title
            if (t2 is not None) and (len(t2) > 0):
                titles.append(t2)
    except:
        pass

    titles = list(set(titles))
    if len(titles) > 1:
        logger.warn('{} had different titles from sra and biosample: {}'.format(
            ncbi.pk, titles)
        )
    return '|'.join(titles)


def get_papers(ncbi):
    ids = []
    papers = []
    if ncbi.pubmed:
        if (ncbi.pubmed is not None) and (len(ncbi.pubmed) > 0):
            for p in ncbi.pubmed:
                if (p is not None) and (p['pubmed_id'] not in ids):
                    papers.append(p)
                    ids.append(p['pubmed_id'])
    return papers


def get_descirption(ncbi):
    try:
        for s in  ncbi.biosample:
            return s.description
    except:
        pass


def main():
    for ncbi in Ncbi.objects():
        biosample = ncbi.sra.sample.BioSample

        # Skip if there is no sample information
        if (biosample is not None) and (biosample != ''):
            # General IDs
            strings = {
                'srs': ncbi.sra.sample.sample_id,
                'gsm': ncbi.sra.sample.GEO,

                'srp': ncbi.sra.study.study_id,
                'bioproject': ncbi.sra.study.BioProject,
                'study_title': ncbi.sra.study.title,
                'study_abstract': ncbi.sra.study.abstract,
                'description': get_descirption(ncbi),
                'sample_title': get_sample_title(ncbi),
                'taxon_id': ncbi.sra.sample.taxon_id
            }
            strings = {k: v for k, v in strings.items() if (v is not None) and (v != '')}

            contacts = get_contacts(ncbi)
            experiment = {
                    'srx': ncbi.srx,
                    'runs': [x for x in set([r.run_id for r in ncbi.sra.run]) if (x is not None) and (x != '')]
            }
            papers = get_papers(ncbi)
            sample_attributes = get_sample_attributes(ncbi)

            try:
                Biometa.objects(pk=biosample).update_one(
                    upsert=True,
                    biosample=biosample,
                    add_to_set__contacts=contacts,
                    add_to_set__papers=papers,
                    add_to_set__experiments=experiment,
                    add_to_set__sample_attributes=sample_attributes,
                    **strings
                )
            except ValidationError:
                print(ncbi.srx)


if __name__ == '__main__':
    main()
