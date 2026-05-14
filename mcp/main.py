from fastmcp import FastMCP
from utils import (
    SqlOperation,
    create_data_lake_namespace,
    describe_data_lake_table,
    execute_data_lake_statement,
    list_data_lake_namespaces,
    list_data_lake_tables,
)

mcp = FastMCP("Iceberg Lake MCP")

@mcp.tool
def list_namespaces(parent_namespace: str | None = None):
    """
    List namespaces in the Iceberg catalog.

    Use parent_namespace to list nested namespaces under an existing namespace.
    """
    return list_data_lake_namespaces(parent_namespace)

@mcp.tool
def create_namespace(namespace: str):
    """
    Create a namespace in the Iceberg catalog if it does not already exist.

    Namespace may be nested using dots, e.g. 'analytics' or 'analytics.events'.
    """
    return create_data_lake_namespace(namespace)

@mcp.tool
def list_tables(namespace: str):
    """
    List table identifiers in a namespace without loading table schemas.
    """
    return list_data_lake_tables(namespace)

@mcp.tool
def describe_table(table_identifier: str):
    """
    Return table metadata, properties, and column documentation for one table.
    """
    return describe_data_lake_table(table_identifier)

@mcp.tool
def execute_read_statement(statement: str, max_rows: int = 100):
    """
    Execute one read-only Spark SQL statement against the Iceberg lake.

    Allowed statements: SELECT, WITH, SHOW, DESCRIBE, DESC, and EXPLAIN.
    Result rows are capped by max_rows.
    """
    return execute_data_lake_statement(statement, SqlOperation.READ, max_rows)

@mcp.tool
def execute_write_statement(statement: str, max_rows: int = 100):
    """
    Execute one data-write Spark SQL statement against the Iceberg lake.

    Allowed statements: INSERT, UPDATE, DELETE, MERGE, and TRUNCATE.
    Use the schema-specific tool for CREATE, ALTER, or DROP statements.
    """
    return execute_data_lake_statement(statement, SqlOperation.WRITE, max_rows)

@mcp.tool
def execute_schema_statement(statement: str, max_rows: int = 100):
    """
    Execute one Iceberg namespace or table schema Spark SQL statement.

    Allowed statements: CREATE, ALTER, and DROP. Catalog, database, function,
    temporary object, and view changes are rejected.
    """
    return execute_data_lake_statement(statement, SqlOperation.SCHEMA, max_rows)

if __name__ == "__main__":
    mcp.run()
