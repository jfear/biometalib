#!/usr/bin/env python
import os
import sys
import readline
from textwrap import dedent
import argparse
from argparse import RawDescriptionHelpFormatter as Raw
from logging import INFO, DEBUG
from collections import defaultdict

import yaml
from pymongo import MongoClient
from fuzzywuzzy import process

from biometalib.logger import logger

_DEBUG = False

def arguments():
    """Pulls in command line arguments."""

    DESCRIPTION = """\
    """

    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=Raw)

    db_args = parser.add_argument_group('Database Arguments')
    config = parser.add_argument_group('Inputs')

    db_args.add_argument("--host", dest="host", action='store', default='localhost', required=False,
                         help="Host running a mongo database. [default: localhost]")

    db_args.add_argument("--port", dest="port", action='store', type=int, required=False, default=27017,
                         help="Mongo database port. [default: 27017]")

    db_args.add_argument("--db", dest="db", action='store', required=True,
                        help="Name of the mongo database containing the biometa collection.")

    config.add_argument("--config", dest="config", action='store', required=True,
                        help="YAML file to store attribute decisions")

    parser.add_argument("--debug", dest="debug", action='store_true', required=False,
                        help="Turn on debug output.")

    args = parser.parse_args()

    # Set logging level
    if args.debug:
        logger.setLevel(DEBUG)
        global _DEBUG
        _DEBUG = True
    else:
        logger.setLevel(INFO)

    return args


class BioAttribute(object):
    def __init__(self, fn):
        """Column attributes.

        Uses YAMLs to store column attributes.

        Parameters:
        -----------
        fn: str
            A YAML file.

        Methods:
        --------
        write_attributes: method
            Writes out saved attributes to YAML

        """
        self.fn = fn
        self._storage = self._load_attributes()
        self._reverse = self._make_reverse()
        self.current_attrs = [x for x in self._storage.keys() if x != 'ignore']

    def _load_attributes(self):
        """Load YAML if it exists.

        Checks if the YAML config file exits, if it does returns a dictionary
        version of the YAML.
        """
        if os.path.exists(self.fn):
            with open(self.fn, 'r') as fh:
                return yaml.load(fh)
        else:
            return {}

    def write_attributes(self):
        """Writes current attribute.

        Writes the current attributes to YAML.
        """
        updated = defaultdict(list)
        for k, v in self._reverse.items():
            updated[v].append(k)

        with open(self.fn, 'w') as fh:
            yaml.dump(dict(updated), fh, default_flow_style=False)

    def _make_reverse(self):
        reverse = {}
        for k, v in self._storage.items():
            reverse[k] = k
            for i in v:
                reverse[i] = k
        return reverse

    def __getitem__(self, key):
        return self._reverse[key]

    def __setitem__(self, key, value):
        self._reverse[key] = value

    def __delitem__(self, key):
        del(self._reverse[key])

    def __iter__(self):
        return iter(self._reverse)

    def keys(self):
        return self._reverse.keys()

    def values(self):
        return self._reverse.values()

    def items(self):
        return self._reverse.items()


def connect_mongo(host, port, db):
    client = MongoClient(host=host, port=port)
    db = client[db]
    return db['biometa']


def get_list_sample_attrs(biometa):
    cursor = biometa.aggregate([
        {'$unwind': '$sample_attributes'},
        {
            '$project': {'_id': '$sample_attributes.name'}
        }
    ])
    return set([x['_id'] for x in cursor])


def autocomplete(text, state):
    for cmd in bioAttr.current_attrs:
        if cmd.startswith(text):
            if not state:
                return cmd
            else:
                state -= 1


class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def format_examples(examples):
    exp = ''
    for i, example in enumerate(examples):
        if i % 4 == 3:
            exp += '{0}{1:<60}{2}\n'.format(bcolors.GREEN, example, bcolors.ENDC)
        else:
            exp += '{0}{1:<60}{2}\t'.format(bcolors.GREEN, example, bcolors.ENDC)
    return exp


def get_examples(attr):
    num_samples = len(list(biometa.aggregate([
        {'$unwind': '$sample_attributes'},
        {'$match': {'sample_attributes.name': attr}},
    ])))

    num_projects = len(list(biometa.aggregate([
        {'$unwind': '$sample_attributes'},
        {'$match': {'sample_attributes.name': attr}},
        {'$group': {'_id': '$bioproject'}},
    ])))

    values = biometa.aggregate([
        {'$unwind': '$sample_attributes'},
        {'$match': {'sample_attributes.name': attr}},
        {
            '$project': {'_id': '$sample_attributes.value'}
        }
    ])

    exp = format_examples(set([x['_id'] for x in values]))
    print(dedent(
        """\
        There were {0}{2:,}{1} BioSamples and {0}{3:,}{1} BioProjects that had this attribute.
        Here are the values:\n\n{4}\n
        """.format(bcolors.YELLOW, bcolors.ENDC, num_samples, num_projects, exp)
    ))


def format_similar(samples):
    smp = ''
    for i, sample in enumerate(samples):
        if sample in bioAttr.current_attrs:
            color = bcolors.YELLOW
        else:
            color = bcolors.GREEN

        if i % 4 == 3:
            smp += '{0}{1:<60}{2}\n'.format(color, sample, bcolors.ENDC)
        else:
            smp += '{0}{1:<60}{2}\t'.format(color, sample, bcolors.ENDC)

    return smp


def get_similar(attr):
    choices = list(set(sample_attrs).union(set(bioAttr.current_attrs)))
    similar = [x[0] for x in process.extract(attr, sample_attrs, limit=21)]
    similar_fmt = format_similar(similar)
    print("Current similar attributes you have already selected include:\n\n{0}".format(similar_fmt))


def get_user_input(attr):
    print('Current Attribute: \t{0}{1:>30}{2}\n'.format(bcolors.RED, attr, bcolors.ENDC))

    ui = input(dedent("""
          Type "e" to get examples or "s" to get a list of similar attributes.
          Do you want to keep, rename, or ignore this attribute?
          [k/r/i/e]: """))

    if ui == 'k':   # Keep attribute
        bioAttr[attr] = attr
        bioAttr.current_attrs.append(attr)
        os.system('clear')
    elif ui == 'i':     # Ignore attribute
        bioAttr[attr] = 'ignore'
        os.system('clear')
    elif ui == 'r':     # Rename attribute
        newName = input('Type in new name: ')
        bioAttr[attr] = newName
        bioAttr.current_attrs.append(newName)
        os.system('clear')
    elif ui == 'e':
        get_examples(attr)
        get_user_input(attr)
    elif ui == 's':
        get_similar(attr)
        get_user_input(attr)
    elif ui == 'n':
        os.system('clear')
        pass
    elif ui == 'quit':
        return False
    else:
        print('\nType "n" if you really want to skip or "quit" to exit, otherwise select a valid option.')
        get_user_input(attr)


def main():
    # Import commandline arguments.
    args = arguments()

    # Set up autocomplete for later
    readline.parse_and_bind("tab: complete")
    readline.set_completer(autocomplete)

    # Get current biological attributes
    global bioAttr
    bioAttr = BioAttribute(args.config)

    # connect to db
    global biometa
    biometa = connect_mongo(args.host, args.port, args.db)

    # Get list of column attributes
    global sample_attrs
    sample_attrs = get_list_sample_attrs(biometa)

    # Only look at attributes not already in our YAML
    filter_attrs = [x for x in sample_attrs if x not in bioAttr]

    # Iterate over novel attributes and figure out what to do with them
    print(dedent("""
                 Welcome to the attribute selector. This is tool is intended in
                 helping come up with a list of sample attribute types. There
                 are {0}{1:,}{2} attributes that we are going to go through. If
                 at any point you want to stop just type "quit" and all of your
                 changes will be saved to your YAML.\n\n
                 """.format(bcolors.YELLOW, len(filter_attrs), bcolors.ENDC)))

    for attr in sorted(filter_attrs):
        if get_user_input(attr) is not None:
            break

    # Write results
    bioAttr.write_attributes()


if __name__ == '__main__':
    main()
