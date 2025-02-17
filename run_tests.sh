#!/bin/bash

# Set PYTHONPATH to the project root
PYTHONPATH=$PYTHONPATH:$(pwd)

# Run tests with pytest
pytest "$@" 