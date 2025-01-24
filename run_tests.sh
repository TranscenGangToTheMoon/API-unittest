#!/bin/bash

if [ ! -d "tests" ]; then
    cd ./API-unittest
fi

TESTS_FOLDER=./tests/
echo "Running API unittest "
python3 -m unittest discover -s $TESTS_FOLDER -p "test_*.py"
