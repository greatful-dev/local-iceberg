import os
import re
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pyspark.sql import SparkSession
from pydantic_models import ColumnMetadata, SqlExecutionResult, TableMetadata, TableReference
from pyiceberg.catalog import load_catalog

POLARIS_CATALOG_URI = os.getenv("POLARIS_CATALOG_URI", "http://polaris-server:8181/api/catalog")
MAX_SQL_RESULT_ROWS = int(os.getenv("MCP_MAX_SQL_RESULT_ROWS", "500"))

READ_STATEMENTS = {"SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN", "WITH"}
WRITE_STATEMENTS = {"INSERT", "UPDATE", "DELETE", "MERGE", "TRUNCATE"}
SCHEMA_STATEMENTS = {"CREATE", "ALTER", "DROP"}
NON_READ_STATEMENTS = WRITE_STATEMENTS | SCHEMA_STATEMENTS
FORBIDDEN_SCHEMA_TARGETS = {
    "CATALOG",
    "DATABASE",
    "FUNCTION",
    "TEMPORARY",
    "VIEW",
}


class SqlOperation(str, Enum):
    READ = "read"
    WRITE = "write"
    SCHEMA = "schema"

def namespace_to_tuple(namespace: str | None = None) -> tuple[str, ...] | None:
    if not namespace:
        return None
    return tuple(part for part in namespace.split(".") if part)

def identifier_to_tuple(table_identifier: str) -> tuple[str, ...]:
    parts = tuple(part for part in table_identifier.split(".") if part)
    if len(parts) < 2:
        raise ValueError("Table identifier must include namespace and table name, e.g. 'analytics.events'.")
    return parts

def identifier_to_string(identifier: tuple[str, ...]) -> str:
    return ".".join(identifier)

def get_spark_session():
    spark = SparkSession.builder \
        .appName("PolarisConnection") \
        .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2") \
        .config("spark.sql.catalog.iceberg-lake", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.iceberg-lake.type", "rest") \
        .config("spark.sql.catalog.iceberg-lake.uri", POLARIS_CATALOG_URI) \
        .config("spark.sql.catalog.iceberg-lake.warehouse", "iceberg-lake") \
        .config("spark.sql.defaultCatalog", "iceberg-lake") \
        .config("spark.sql.catalog.iceberg-lake.credential", f"{os.getenv('QUARKUS_DATASOURCE_USERNAME')}:{os.getenv('QUARKUS_DATASOURCE_PASSWORD')}") \
        .config("spark.sql.catalog.iceberg-lake.scope", "PRINCIPAL_ROLE:ALL") \
        .getOrCreate()
    
    return spark

def _strip_sql_comments(statement: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", " ", statement, flags=re.DOTALL)
    return re.sub(r"--[^\n\r]*", " ", without_block_comments)

def _normalize_sql_statement(statement: str) -> str:
    cleaned = _strip_sql_comments(statement).strip()
    if not cleaned:
        raise ValueError("SQL statement is required.")

    if ";" in cleaned.rstrip(";"):
        raise ValueError("Only one SQL statement is allowed per tool call.")

    return cleaned.rstrip(";").strip()

def _statement_tokens(statement: str) -> list[str]:
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*", statement.upper())

def _statement_type(statement: str) -> str:
    tokens = _statement_tokens(statement)
    if not tokens:
        raise ValueError("SQL statement must start with a SQL keyword.")
    return tokens[0]

def _validate_sql_statement(statement: str, operation: SqlOperation) -> tuple[str, str]:
    normalized = _normalize_sql_statement(statement)
    statement_type = _statement_type(normalized)

    if operation == SqlOperation.READ and statement_type not in READ_STATEMENTS:
        raise ValueError(
            f"Read statements must start with one of: {', '.join(sorted(READ_STATEMENTS))}."
        )
    if operation == SqlOperation.READ and statement_type == "WITH":
        tokens = _statement_tokens(normalized)
        if any(token in NON_READ_STATEMENTS for token in tokens[1:]):
            raise ValueError("WITH read statements cannot contain write or schema keywords.")

    if operation == SqlOperation.WRITE and statement_type not in WRITE_STATEMENTS:
        raise ValueError(
            f"Write statements must start with one of: {', '.join(sorted(WRITE_STATEMENTS))}."
        )

    if operation == SqlOperation.SCHEMA:
        tokens = _statement_tokens(normalized)
        if statement_type not in SCHEMA_STATEMENTS:
            raise ValueError(
                f"Schema statements must start with one of: {', '.join(sorted(SCHEMA_STATEMENTS))}."
            )
        if any(token in FORBIDDEN_SCHEMA_TARGETS for token in tokens[1:3]):
            raise ValueError(
                "Schema statements are limited to Iceberg namespaces and tables; "
                "catalog, database, function, temporary object, and view changes are not allowed."
            )

    return normalized, statement_type

def _json_safe_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    if isinstance(value, list):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_value(item) for key, item in value.items()}
    return value

def execute_data_lake_statement(
    statement: str,
    operation: SqlOperation,
    max_rows: int = 100,
) -> dict:
    normalized, statement_type = _validate_sql_statement(statement, operation)
    if max_rows < 0:
        raise ValueError("max_rows must be greater than or equal to 0.")
    if max_rows > MAX_SQL_RESULT_ROWS:
        raise ValueError(f"max_rows cannot exceed {MAX_SQL_RESULT_ROWS}.")

    spark = get_spark_session()
    dataframe = spark.sql(normalized)

    rows = []
    truncated = False
    if max_rows > 0:
        collected_rows = dataframe.limit(max_rows + 1).collect()
        truncated = len(collected_rows) > max_rows
        rows = [
            {
                key: _json_safe_value(value)
                for key, value in row.asDict(recursive=True).items()
            }
            for row in collected_rows[:max_rows]
        ]

    return SqlExecutionResult(
        statement_type=statement_type,
        columns=dataframe.columns,
        rows=rows,
        row_count=len(rows),
        truncated=truncated,
    ).model_dump()

def get_catalog():
    catalog = load_catalog(
        "polaris",
        **{
            "uri": POLARIS_CATALOG_URI,
            "credential": f"{os.getenv('QUARKUS_DATASOURCE_USERNAME')}:{os.getenv('QUARKUS_DATASOURCE_PASSWORD')}",
            "scope": "PRINCIPAL_ROLE:ALL",
            "header.X-Iceberg-Access-Delegation": "",
            "warehouse": "iceberg-lake",
            "type": "rest",
        }
    )

    return catalog

def list_data_lake_namespaces(parent_namespace: str | None = None) -> list[str]:
    catalog = get_catalog()
    namespace_tuple = namespace_to_tuple(parent_namespace)
    namespaces = catalog.list_namespaces(namespace_tuple) if namespace_tuple else catalog.list_namespaces()
    return [identifier_to_string(namespace) for namespace in namespaces]

def create_data_lake_namespace(namespace: str) -> dict:
    catalog = get_catalog()
    namespace_tuple = namespace_to_tuple(namespace)
    if not namespace_tuple:
        raise ValueError("Namespace is required, e.g. 'analytics' or 'analytics.events'.")

    catalog.create_namespace_if_not_exists(namespace_tuple)
    return {
        "namespace": identifier_to_string(namespace_tuple),
        "created": True,
    }

def list_data_lake_tables(namespace: str) -> list[dict]:
    catalog = get_catalog()
    namespace_tuple = namespace_to_tuple(namespace)
    if not namespace_tuple:
        raise ValueError("Namespace is required, e.g. 'analytics'.")

    tables = catalog.list_tables(namespace_tuple)
    return [
        TableReference(
            namespace=identifier_to_string(table_id[:-1]),
            table=table_id[-1],
            identifier=identifier_to_string(table_id),
        ).model_dump()
        for table_id in tables
    ]

def describe_data_lake_table(table_identifier: str) -> dict:
    catalog = get_catalog()
    table_id = identifier_to_tuple(table_identifier)
    table = catalog.load_table(table_id)
    namespace = identifier_to_string(table_id[:-1])
    table_name = table_id[-1]

    return TableMetadata(
        namespace=namespace,
        table=table_name,
        identifier=identifier_to_string(table_id),
        description=table.metadata.properties.get("comment"),
        properties=dict(table.metadata.properties),
        columns=[
            ColumnMetadata(
                name=field.name,
                type=str(field.field_type),
                description=field.doc,
            )
            for field in table.schema().fields
        ],
    ).model_dump()
