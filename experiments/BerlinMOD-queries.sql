---distribute vehicle table to all worker 
SELECT create_reference_table('vehicles');

explain SELECT COUNT(*), SUM(duration(Trip)), SUM(length(Trip)) / 1e3 FROM Trips;

---
SELECT
CASE
WHEN T.sourcenode = V.homenode AND date_part('dow', T.day) BETWEEN 1 AND 5 AND
date_part('hour', startTimestamp(trip)) < 12 THEN 'home_work'
WHEN T.sourcenode = V.worknode AND date_part('dow', T.day) BETWEEN 1 AND 5 AND
date_part('hour', startTimestamp(trip)) > 12 THEN 'work_home'
WHEN date_part('dow', T.day) BETWEEN 1 AND 5 THEN 'leisure_weekday'
ELSE 'leisure_weekend'
END AS TripType, COUNT(*), MIN(duration(Trip)), MAX(duration(Trip)), AVG(duration(Trip))
FROM Trips T, vehiclenodes V
WHERE T.vehid = V.vehid
GROUP BY TripType;

---

SELECT vehicle, seq, source, target, round(length(Trip)::numeric / 1e3, 3),
startTimestamp(Trip), duration(Trip)
FROM Trips
WHERE length(Trip) > 50000 LIMIT 1;

---
SELECT vehid, seqno, sourcenode, targetnode, round(length(Trip)::numeric / 1e3, 3),
startTimestamp(Trip), duration(Trip)
FROM Trips
WHERE length(Trip) > 50000 LIMIT 1;

--

SELECT MIN(twavg(speed(Trip))) * 3.6, MAX(twavg(speed(Trip))) * 3.6,
AVG(twavg(speed(Trip))) * 3.6
FROM Trips;

--- take more than 8 mins(canceled) without distributing edges table 
CREATE TABLE HeatMap AS
SELECT E.id, E.geom, count(*)
FROM Edges E, Trips T
WHERE st_intersects(E.geom, T.trajectory)
GROUP BY E.id, E.geom;




select citus_update_node(nodeid, 'new-address', nodeport)
  from pg_dist_node
 where nodename = 'old-address';



SELECT * from citus_add_node('10.0.1.5', 5432);
INSERT INTO pod_information(pod_ip, pod_hostname) SELECT '$POD_IP', '${HOSTNAME}' WHERE NOT EXISTS (SELECT pod_ip FROM pod_information WHERE pod_ip = '$POD_IP');









-- correcting the do query after my meating with zimanyi
DO
$do$
BEGIN
   if NOT EXISTS (SELECT pod_ip FROM pod_information WHERE pod_ip = '10.0.0.3') then
      SELECT * from citus_add_node('10.0.0.3', 5432);
   ELSE
      select citus_update_node((select nodeid from pod_information where pod_ip='10.0.0.3'),'10.0.2.10', 5432) 
      from pg_dist_node
    where nodename = '10.0.0.3';
    UPDATE pod_information
      SET  pod_ip = '10.0.2.10' 
    WHERE nodeid = (select nodeid from pg_dist_node where nodename='10.0.0.3');
    
   END IF;
END
$do$






select citus_update_node((select nodeid from pod_information 
              where pod_hostname='citus-workers-0'),'10.0.2.4', 5432) 
from pg_dist_node  
where nodename =(select pod_ip from pod_information 
              where pod_hostname='citus-workers-0'); 

UPDATE pod_information SET  pod_ip = '10.0.2.4' 
WHERE nodeid = (select nodeid from pod_information where pod_hostname='citus-workers-0');





############# BERLINMOD 17 QUERIES

### query #6
SELECT V1. licence AS Licence1 , V2. licence AS Licence2
FROM vehicles V1,trips T1, vehicles V2, trips T2
WHERE T1.vehid=V1.vehid and T2.vehid=V2.vehid and  V1.licence < V2.licence AND V1.type = 'truck'
AND V2.type = 'truck'
AND sometimes( distance(T1.Trip ,T2.Trip) <= 10.0);


### Query 1
SELECT DISTINCT L.Licence, C.Model AS Model
FROM Vehicles C, Licences L
WHERE C.Licence = L.Licence;

### Query 2

SELECT COUNT (Licence)
FROM Vehicles C
WHERE Type = 'passenger';

### Query 3 >>> 2.33 secondes>>>cluster 1 (1 coordinator, 3 workers)
SELECT DISTINCT L.Licence, I.InstantId, I.Instant AS Instant,
valueAtTimestamp(T.Trip, I.Instant) AS Pos
FROM Trips T, Licences1 L, Instants1 I
WHERE T.VehId = L.VehId AND valueAtTimestamp(T.Trip, I.Instant) IS NOT NULL
ORDER BY L.Licence, I.InstantId;

### Query 4  >>>9.58 secondes >>>cluster 1 (1 coordinator, 3 workers)
##Which vehicles have passed the points from Points. 
EXPLAIN
SELECT DISTINCT P.PointId, P.Geom, C.Licence
FROM Trips T, Vehicles C, Points P
WHERE T.VehId = C.VehId AND T.Trip && stbox(P.Geom) AND
ST_Intersects(trajectory(T.Trip), P.Geom)
ORDER BY P.PointId, C.Licence;



### Query 5 >>> >>>cluster 1 (1 coordinator, 3 workers)
#ERROR:  complex joins are only supported when all distributed tables are co-located and joined on their distribution columns
SELECT L1.Licence AS Licence1, L2.Licence AS Licence2,
MIN(ST_Distance(trajectory(T1.Trip), trajectory(T2.Trip))) AS MinDist
FROM Trips T1, Licences1 L1, Trips T2, Licences2 L2
WHERE T1.VehId = L1.VehId AND T2.VehId = L2.VehId AND T1.VehId < T2.VehId
GROUP BY L1.Licence, L2.Licence
ORDER BY L1.Licence, L2.Licence;
###query 6 MobilityDB


## By setting up this config varialbe, the query 6 work peffectly without an error as mentioned in the article
##Distributed moving object data management in MobilityDB
Set citus.enable_repartition_joins to on;

SELECT DISTINCT C1.Licence AS Licence1, C2.Licence AS Licence2
FROM Trips T1, Vehicles C1, Trips T2, Vehicles C2
WHERE T1.VehId = C1.VehId AND T2.VehId = C2.VehId AND
T1.VehId < T2.VehId AND C1.Type = 'truck' AND C2.Type = 'truck' AND
T1.Trip && expandSpace(T2.Trip, 10) AND
tdwithin(T1.Trip, T2.Trip, 10.0) ?= true
ORDER BY C1.Licence, C2.Licence;




### query 7>>> 1 seconde >>>>>>cluster 1 (1 coordinator, 3 workers)

WITH Timestamps AS (
SELECT DISTINCT C.Licence, P.PointId, P.Geom,
MIN(startTimestamp(atValues(T.Trip,P.Geom))) AS Instant
FROM Trips T, Vehicles C, Points1 P
WHERE T.VehId = C.VehId AND C.Type = 'passenger' AND
T.Trip && stbox(P.Geom) AND ST_Intersects(trajectory(T.Trip), P.Geom)
GROUP BY C.Licence, P.PointId, P.Geom )
SELECT T1.Licence, T1.PointId, T1.Geom, T1.Instant
FROM Timestamps T1
WHERE T1.Instant <= ALL (
SELECT T2.Instant
FROM Timestamps T2
WHERE T1.PointId = T2.PointId )
ORDER BY T1.PointId, T1.Licence;
## query 8 >>>1 seconde>>> cluster 1 (1 coordinator, 3 workers)

SELECT L.Licence, P.PeriodId, P.Period, SUM(length(atTime(T.Trip, P.Period))) AS Dist
FROM Trips T, Licences1 L, Periods1 P
WHERE T.VehId = L.VehId AND T.Trip && P.Period
GROUP BY L.Licence, P.PeriodId, P.Period
ORDER BY L.Licence, P.PeriodId;



### Query 9 >>>00:02:45.065>>> should be taken 

WITH Distances AS (
SELECT P.PeriodId, P.Period, T.VehId, SUM(length(atTime(T.Trip, P.Period))) AS Dist
FROM Trips T, Periods P
WHERE T.Trip && P.Period
GROUP BY P.PeriodId, P.Period, T.VehId )
SELECT PeriodId, Period, MAX(Dist) AS MaxDist
FROM Distances
GROUP BY PeriodId, Period
ORDER BY PeriodId;



### Query 10  >>> no result for scale 0.005

WITH Values AS (
SELECT DISTINCT L1.Licence AS QueryLicence, C2.Licence AS OtherLicence,
atTime(T1.Trip, getTime(atValues(tdwithin(T1.Trip, T2.Trip, 3.0), TRUE))) AS Pos
FROM Trips T1, Licences1 L1, Trips T2, Licences2 C2
WHERE T1.VehId = L1.VehId AND T2.VehId = C2.VehId AND T1.VehId < T2.VehId AND
expandSpace(T1.Trip, 3) && expandSpace(T2.Trip, 3) AND
edwithin(T1.Trip, T2.Trip, 3.0) )
SELECT QueryLicence, OtherLicence, array_agg(Pos ORDER BY startTimestamp(Pos)) AS Pos
FROM Values
GROUP BY QueryLicence, OtherLicence
ORDER BY QueryLicence, OtherLicence;



### Query 11 >>> no result in sc 0.005


SELECT P.PointId, P.Geom, I.InstantId, I.Instant, C.Licence
FROM Trips T, Vehicles C, Points1 P, Instants1 I
WHERE T.VehId = C.VehId AND T.Trip @> stbox(P.Geom, I.Instant) AND
valueAtTimestamp(T.Trip, I.Instant) = P.Geom
ORDER BY P.PointId, I.InstantId, C.Licence;


### Query 12 no result



SELECT DISTINCT P.PointId, P.Geom, I.InstantId, I.Instant,
C1.Licence AS Licence1, C2.Licence AS Licence2
FROM Trips T1, Vehicles C1, Trips T2, Vehicles C2, Points1 P, Instants1 I
WHERE T1.VehId = C1.VehId AND T2.VehId = C2.VehId AND T1.VehId < T2.VehId AND
T1.Trip @> stbox(P.Geom, I.Instant) AND T2.Trip @> stbox(P.Geom, I.Instant) AND
valueAtTimestamp(T1.Trip, I.Instant) = P.Geom AND
valueAtTimestamp(T2.Trip, I.Instant) = P.Geom
ORDER BY P.PointId, I.InstantId, C1.Licence, C2.Licence;


##Query 13 >>> 00:02:18.847>>>should be taken 
EXPLAIN ANALYZE SELECT DISTINCT R.RegionId, P.PeriodId, P.Period, C.Licence
FROM Trips T, Vehicles C, Regions1 R, Periods1 P
WHERE T.VehId = C.VehId AND T.trip && stbox(R.Geom, P.Period) AND
ST_Intersects(trajectory(atTime(T.Trip, P.Period)), R.Geom)
ORDER BY R.RegionId, P.PeriodId, C.Licence;


##query 14>>>> 00:02:02.888>> again is relevant

SELECT DISTINCT R.RegionId, I.InstantId, I.Instant, C.Licence
FROM Trips T, Vehicles C, Regions1 R, Instants1 I
WHERE T.VehId = C.VehId AND T.Trip && stbox(R.Geom, I.Instant) AND
ST_Contains(R.Geom, valueAtTimestamp(T.Trip, I.Instant))
ORDER BY R.RegionId, I.InstantId, C.Licence;

##query 15






##creation schema script for BerlinMOD

CREATE TABLE Vehicles(vehId int PRIMARY KEY, licence text, type text,
    model text);
CREATE TABLE Points(pointId int PRIMARY KEY, PosX float, PosY float, geom geometry(Point));
CREATE TABLE Regions(regionId int PRIMARY KEY, geom geometry(Polygon));
CREATE TABLE Instants(instantId int PRIMARY KEY, instant timestamptz);
CREATE TABLE Licences(licenceId int PRIMARY KEY, licence text, vehId int);
CREATE TABLE Periods(periodId int PRIMARY KEY, BeginP TimestampTz, EndP TimestampTz, period tstzspan);
CREATE TABLE Trips(tripId SERIAL PRIMARY KEY, vehId int, day date, seqNo int,
    sourceNode bigint, targetNode bigint, trip tgeompoint, trajectory geometry);