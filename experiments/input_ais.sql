--CREATE OR REPLACE FUNCTION input_ais()
--RETURNS text AS $$
--BEGIN

DROP TABLE IF EXISTS AISInput;
CREATE TABLE AISInput(
T timestamp,
TypeOfMobile varchar(500),
MMSI integer,
Latitude float,
Longitude float,
navigationalStatus varchar(200),
ROT float,
SOG float,
COG float,
Heading integer,
IMO varchar(500),
Callsign varchar(500),
Name varchar(200),
ShipType varchar(500),
CargoType varchar(200),
Width float,
Length float,
TypeOfPositionFixingDevice varchar(500),
Draught float,
Destination varchar(500),
ETA varchar(500),
DataSourceType varchar(500),
SizeA float,
SizeB float,
SizeC float,
SizeD float,
Geom geometry(Point, 4326)
);

--  RAISE INFO 'Reading CSV files ...';

SET datestyle = dmy;
\COPY AISInput(T, TypeOfMobile, MMSI, Latitude, Longitude, NavigationalStatus,ROT, SOG, COG, Heading, IMO, CallSign, Name, ShipType, CargoType, Width, Length,TypeOfPositionFixingDevice, Draught, Destination, ETA, DataSourceType,SizeA, SizeB, SizeC, SizeD) FROM './aisdk-2023-03-07.csv' DELIMITER ',' CSV HEADER;
--  RAISE INFO 'Updating AISInput table ...';
    
UPDATE AISInput SET
--NavigationalStatus = CASE NavigationalStatus WHEN 'Unknown value' THEN NULL END,
Geom = ST_SetSRID( ST_MakePoint( Longitude, Latitude ), 4326);
--  RAISE INFO 'Creating AISInputFiltered table ...';

DROP TABLE IF EXISTS AISInputFiltered (T,TypeOfMobile,MMSI,Latitude,Longitude,navigationalStatus,ROT,SOG,COG,Name,Width, Length,Destination,Geom);
CREATE TABLE AISInputFiltered AS
SELECT DISTINCT ON(mmsi,T) *
FROM AISInput
WHERE Longitude BETWEEN -16.1 and 32.88 AND Latitude BETWEEN 40.18 AND 84.17;


DROP TABLE IF EXISTS Ships;
CREATE TABLE Ships AS
SELECT DISTINCT on (MMSI) mmsi, name, width, length
FROM AISInputFiltered




-- Generate series of periods with 10 minutes as interval
create table periods_temp (pid serial, period tstzspan NOT NULL );
INSERT INTO periods_temp(period)
SELECT span(i, i + interval '10 minutes', true, false)
FROM generate_series(timestamptz '2023-03-07 00:00:00', timestamptz '2023-03-08 00:00:00', interval '10 minutes') i;

CREATE TABLE Ports (
code varchar(20),
description varchar(200),
latitude float,
longitude float,
geom geometry);
\COPY Ports(code, description, latitude, Longitude) FROM './danish_ports_new.csv' DELIMITER ',' CSV HEADER;

UPDATE Ports SET
geom = ST_SetSRID( ST_MakePoint( Longitude, Latitude ), 4326);


CREATE TABLE trips(MMSI, Trip, SOG, COG) AS
SELECT MMSI,
tgeompoint_seq(array_agg(tgeompoint_inst( ST_Transform(Geom, 4326), T) ORDER BY T)),
tfloat_seq(array_agg(tfloat_inst(SOG, T) ORDER BY T) FILTER (WHERE SOG IS NOT NULL)),
tfloat_seq(array_agg(tfloat_inst(COG, T) ORDER BY T) FILTER (WHERE COG IS NOT NULL))
FROM AISInputFiltered
GROUP BY MMSI;



--Distribution phase

SELECT create_reference_table('Ports');
SELECT truncate_local_data_after_distributing_table($$public.Ports$$);
SELECT create_reference_table('periods_temp');
SELECT truncate_local_data_after_distributing_table($$public.periods_temp$$);
SELECT create_distributed_table('trips', 'mmsi');
SELECT truncate_local_data_after_distributing_table($$public.trips$$);
