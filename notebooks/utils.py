from pyspark.sql import SparkSession

def get_spark_session():
    spark = SparkSession.builder \
        .appName("PolarisConnection") \
        .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2") \
        .config("spark.sql.catalog.iceberg-lake", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.iceberg-lake.type", "rest") \
        .config("spark.sql.catalog.iceberg-lake.uri", "http://localhost:8181/api/catalog") \
        .config("spark.sql.catalog.iceberg-lake.warehouse", "iceberg-lake") \
        .config("spark.sql.catalog.iceberg-lake.credential", "root:root") \
        .config("spark.sql.catalog.iceberg-lake.scope", "PRINCIPAL_ROLE:ALL") \
        .getOrCreate()
    
    return spark