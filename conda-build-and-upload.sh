#!/bin/bash

export BIOMETALIB_BUILD=$(git rev-list --count `git describe --tags --abbrev=0`..HEAD --count)

conda build conda-recipe

#if [[ $TRAVIS_BRANCH = "master" && $TRAVIS_PULL_REQUEST = "false" ]]; then
#  conda install anaconda-client -y
#  anaconda \
#    -t $ANACONDA_TOKEN \
#    upload \
#    -u jfear \
#    --force \
#    $(conda build --output conda-recipe)
#fi
