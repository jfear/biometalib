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


@pytest.fixture()
def bioAttr(yaml):
    return BioAttribute(yaml)


def test_BioAttribute(bioAttr):

    # Make sure it looks right
    assert len(bioAttr._storage['one']) == 3
    assert len(bioAttr._storage['two']) == 1

    # Check reverse mapping
    assert bioAttr['Sex'] == 'sex'

    # Make some changes and write out
    bioAttr['one'] = 'three'
    bioAttr.write_attributes()

    # Import again and check
    bio2 = BioAttribute(bioAttr.fn)
    assert len(bio2._storage['three']) == 1

