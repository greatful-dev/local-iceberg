# Project Setup

## General requirements:

I developed this project on macos using podman.

- .sh scripts will not work on windows devices
- not sure if the container networking is docker compatible
- mapped to a connected SSD to preserve os disk space (details in recommendations section)

### Recommendations

- use [podman](https://podman.io/)
- map the iceberg file storage to an SSD to preserve your os disk space

```bash
podman machine stop
podman machine ssh --volume /Volumes:/Volumes # <-- this is a mac convention, fwiw
podman machine start
```

## Primary Services:

1. Postgres Database for polaris metadata store
    1. `scripts/run_postgres.sh`
2. Polaris Server for exposing interfaces for Spark Session config
    1. Build the initial postgres admin: `scripts/bootstrap_polaris.sh`
    2. Run the polaris server: `scripts/run_polaris.sh`
    2. Configure the initial catalog: `scripts/initialize_catalog.sh`
3. Python Jupyter notebook environment for interacting with the data lake
    1. Jupyter notebook browser interface
        1. `uv run jupyter notebook`
        2. Create your `.ipynb` file under `./notebooks`
        3. `from utils import get_spark_session`
        4. `spark = get_spark_session()`
        5. Execute some operations: `spark.sql(...)`
    2. Native IDE (VSCode/Cursor)
        1. Set kernel to local-iceberg (Python 3.12.7)
        2. Create your `.ipynb` file under `./notebooks`
        3. `from utils import get_spark_session`
        4. `spark = get_spark_session()`
        5. Execute some operations: `spark.sql(...)`

4. FastMCP server for allowing agents to interface with local data lake resources
    1. `scripts/run_mcp.sh`
    2. Configure the MCP with your agent
        1. Codex: `codex mcp add local-iceberg --url http://localhost:8000/mcp`
        2. Claude Code: `claude mcp add --transport http local-iceberg http://localhost:8000/mcp`
    3. Perform standard development workflow. I'm just writing notebooks and running them periodically to refresh source data in this project.