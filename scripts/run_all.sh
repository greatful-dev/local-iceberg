#!/bin/bash

scripts/run_postgres.sh &
scripts/bootstrap_polaris.sh &
scripts/run_polaris.sh &
scripts/initialize_catalog.sh &
scripts/run_mcp.sh

exit 0
