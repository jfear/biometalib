#!/bin/bash

if [[ $TRAVIS_BRANCH = "master" && $TRAVIS_PULL_REQUEST = "false" ]]; then
    curl -H "Content-Type: application/json" \
        --data '{"docker_tag": "master"}' \
        -X POST https://registry.hub.docker.com/u/jfear/biometalib/trigger/d939d877-913f-422f-b411-4f6719eb3fa7/
fi

if [[ $TRAVIS_TAG ]]; then
    curl -H "Content-Type: application/json" \
        --data "{\"source_type\": \"Tag\", \"source_name\": \"$TRAVIS_TAG\"}" \
        -X POST https://registry.hub.docker.com/u/jfear/biometalib/trigger/d939d877-913f-422f-b411-4f6719eb3fa7/
fi
