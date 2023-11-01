#!/bin/sh

# shellcheck disable=SC2068
PYTHONPATH=$PATH:$(pwd)/src python -m src.app.service -c=src/config/config.yml $@
