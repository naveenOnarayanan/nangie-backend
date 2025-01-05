#!/bin/bash

REPO_ROOT=$(git rev-parse --show-toplevel)
pip install -r $REPO_ROOT/requirements.txt --target $REPO_ROOT/package
cd $REPO_ROOT/package
zip -r ../deployment.zip .
cd ..
zip -g deployment.zip app/main.py

