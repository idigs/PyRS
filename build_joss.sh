#!/bin/sh

docker run --rm \
    --volume $PWD/paper:/data \
    --user $(id -u):$(id -g) \
    --env JOURNAL=joss \
    openjournals/paperdraft
