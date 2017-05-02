#!/bin/bash

conda build conda-recipe

if [[ $TRAVIS_BRANCH = "master" && $TRAVIS_PULL_REQUEST = "false" ]]; then
  conda install anaconda-client -y
  anaconda \
    -t $ANACONDA_TOKEN \
    upload \
    -u jfear \
    $(conda build --output conda-recipe)
fi
