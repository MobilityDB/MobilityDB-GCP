#!/bin/bash

echo "shared_preload_libraries = 'citus, postgis-3.so'" >> $PGDATA/postgresql.conf
echo "Shared citus and mobilityDB extension in postgresql.conf file"

set -e

# Create the 'mobilitydb' extension in the mobilitydb database
echo "Loading MobilityDB extension into mobilitydb"
psql --user="$POSTGRES_USER" --dbname="$POSTGRES_DB" <<- 'EOSQL'
	CREATE EXTENSION IF NOT EXISTS citus;
	CREATE EXTENSION IF NOT EXISTS mobilitydb CASCADE;
	-- add Docker flag to node metadata
	UPDATE pg_dist_node_metadata SET metadata=jsonb_insert(metadata, '{docker}', 'true');
	COMMIT;	
EOSQL
