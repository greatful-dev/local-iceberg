# Project Setup

## Primary Services:

1. Postgres Database for polaris metadata store
    1. `scripts/run_postgres.sh`
2. Polaris Server for exposing interfaces for Spark Session config
    1. Build the initial postgres admin: `scripts/bootstrap_polaris`
    2. Run the polaris server: `scripts/run_polaris.sh`
    2. Configure the initial catalog: `scripts/initialize_catalog`
3. Python Jupyter notebook environment for interacting with the data lake
    1. `uv run jupyter notebook`
    2. Open `example.ipynb`
    3. Run the SparkSession builder (cell 1/2)
    4. Execute some operations

4. FastMCP server for allowing agents to interface with local data lake resources
    1. `scripts/run_mcp.py`
    2. Configure the MCP with your agent
        1. Codex: `codex mcp add local-iceberg --url http://localhost:8000/mcp`
        2. Claude Code: `claude mcp add --transport http local-iceberg http://localhost:8000/mcp`
    3. Perform standard development workflow. I'm just writing notebooks and running them periodically to refresh source data in this project.