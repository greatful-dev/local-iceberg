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

## Interfacing from networked 3rd party services

```python
from pyspark.sql import SparkSession

spark = (SparkSession.builder
    .config("spark.jars.packages", "org.apache.polaris:polaris-spark-3.5_2.13:1.1.0-incubating,org.apache.iceberg:iceberg-aws-bundle:1.10.0,io.delta:delta-spark_2.12:3.3.1,org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.10.0")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions,io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.polaris", "org.apache.polaris.spark.SparkCatalog")
    .config("spark.sql.catalog.polaris.uri", "http://polaris:8181/api/catalog")
    .config("spark.sql.catalog.polaris.warehouse", "lakehouse")
    .config("spark.sql.catalog.polaris.credential", "{client_id}:{client_secret}")
    .config("spark.sql.catalog.polaris.scope", "PRINCIPAL_ROLE:ALL")
    .config("spark.sql.catalog.polaris.header.X-Iceberg-Access-Delegation", "vended-credentials")
    .config("spark.sql.catalog.polaris.token-refresh-enabled", "true")
    .getOrCreate())

spark.sql(f'''SELECT * FROM iceberg-lake.{some_schema}.{some_table}''')
```