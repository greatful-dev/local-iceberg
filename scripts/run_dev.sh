#!/bin/bash

scripts/run_postgres.sh &
scripts/bootstrap_polaris.sh &
scripts/run_polaris.sh &
scripts/initialize_catalog.sh

exit 0
