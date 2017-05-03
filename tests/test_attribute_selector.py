import pytest
import os

from biometalib.utils.attribute_selector import BioAttribute, connect_mongo

@pytest.fixture()
def yaml(tmpdir):
    conf = """\
    one:
      - one
      - two
      - three
    two:
      - one
    sex:
      - sex
      - Sex
    """

    fn = os.path.join(str(tmpdir), 'test.yaml')
    with open(fn, 'w') as fh:
        fh.write(conf)
    return fn


def test_BioAttribute(yaml):
    # import
    bio = BioAttribute(yaml)

    # Make sure it looks right
    assert len(bio._storage['one']) == 3
    assert len(bio._storage['two']) == 1

    # Make some changes and write out
    del(bio._storage['one'])
    del(bio._storage['two'])
    bio._storage['three'] = ['one']
    bio.write_attributes()

    # Import again and check
    bio2 = BioAttribute(yaml)
    assert len(bio2._storage['three']) == 1

def test_connect_mongo():
    biometa = connect_mongo('localhost', 27022, 'sra')
    assert biometa.find().count() > 0
