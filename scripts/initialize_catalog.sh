set -a; source .env.development; set +a

TOKEN=$(
    curl \
    -u $QUARKUS_DATASOURCE_USERNAME:$QUARKUS_DATASOURCE_PASSWORD \
    -X POST http://localhost:8181/api/catalog/v1/oauth/tokens \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data 'grant_type=client_credentials&scope=PRINCIPAL_ROLE:ALL' \
    | jq -r '.access_token'
)

curl -X POST "http://localhost:8181/api/management/v1/catalogs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "catalog": {
      "name": "iceberg-lake",
      "type": "INTERNAL",
      "readOnly": false,
      "properties": {
        "default-base-location": "file:///data/iceberg-lake"
      },
      "storageConfigInfo": {
        "storageType": "FILE",
        "allowedLocations": [
          "file:///data/iceberg-lake"
        ]
      }
    }
  }'
