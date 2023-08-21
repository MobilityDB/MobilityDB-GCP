import time
import psycopg2
import psycopg2.extensions
from psycopg2.extras import LoggingConnection, LoggingCursor
import logging
import statistics
import csv


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)





list_queries=[{'Q2':"\
        SELECT COUNT (Licence)\
        FROM Vehicles C\
        WHERE Type = 'passenger';\
        "},
{'Q3':"\
        SELECT DISTINCT L.Licence, I.InstantId, I.Instant AS Instant,\
        valueAtTimestamp(T.Trip, I.Instant)\
        AS Pos\
        FROM Trips T, Licences1 L, Instants1 I\
        WHERE T.VehId = L.VehId AND\
        valueAtTimestamp(T.Trip, I.Instant)\
        IS NOT NULL\
        ORDER BY L.Licence, I.InstantId; \
        "},

{'Q4':"\
        SELECT DISTINCT P.PointId, P.Geom, C.Licence\
        FROM Trips T, Vehicles C, Points P\
        WHERE T.VehId = C.VehId AND T.Trip && stbox(P.Geom) AND\
        ST_Intersects(trajectory(T.Trip), P.Geom)\
        ORDER BY P.PointId, C.Licence;\
        "},

{'Q7':"\
        WITH Timestamps AS (\
        SELECT DISTINCT C.Licence, P.PointId, P.Geom,\
        MIN(startTimestamp(atValues(T.Trip,P.Geom))) AS Instant\
        FROM Trips T, Vehicles C, Points1 P\
        WHERE T.VehId = C.VehId AND C.Type = 'passenger' AND\
        T.Trip && stbox(P.Geom) AND ST_Intersects(trajectory(T.Trip),\
        P.Geom)\
        GROUP BY C.Licence, P.PointId, P.Geom )\
        SELECT T1.Licence, T1.PointId, T1.Geom, T1.Instant\
        FROM Timestamps T1\
        WHERE T1.Instant <= ALL (\
        SELECT T2.Instant\
        FROM Timestamps T2\
        WHERE T1.PointId = T2.PointId )\
        ORDER BY T1.PointId, T1.Licence;\
        "},
{'Q9':"\
        WITH Distances AS (\
        SELECT P.PeriodId, P.Period, T.VehId,\
        SUM(length(atTime(T.Trip, P.Period)))\
         AS Dist FROM Trips T, Periods P\
        WHERE T.Trip && P.Period\
        GROUP BY P.PeriodId, P.Period, T.VehId )\
        SELECT PeriodId, Period, MAX(Dist) AS MaxDist\
        FROM Distances\
        GROUP BY PeriodId, Period\
        ORDER BY PeriodId;\
        "},
{'Q13':"\
        SELECT DISTINCT R.RegionId, P.PeriodId, P.Period, C.Licence\
        FROM Trips T, Vehicles C, Regions1 R, Periods1 P\
        WHERE T.VehId = C.VehId AND T.trip && stbox(R.Geom, P.Period)\
        AND ST_Intersects(trajectory(atTime(T.Trip, P.Period)),\
        R.Geom) ORDER BY R.RegionId, P.PeriodId, C.Licence;\
        "},
        ]

POSTGRES_USER="USER"
POSTGRES_PASSWORD="*****"
POSTGRES_HOST="172.17.0.2"
POSTGRES_PORT="30001"

list_db=[('POSTGRES_DB_S005', "brussels005"), ('POSTGRES_DB_S02', 
"brussels02"), ('POSTGRES_DB_S05',"brussels05"), 
('POSTGRES_DB_S1',"brussels-s1") ]

def  average_execution_time(cursor,query):
    iterations=[]
    for iter in range(1,6):
        start_time= time.time()
        cursor.execute(query)
        end_time= time.time()
        res =(end_time - start_time)
        iterations.append(res)
        print("\nQuery is in iteration "+str(iter)+": "+str(res)+" s")
    avg =statistics.mean(iterations[1:])
    print(str(iter)+" iterations are finished", iterations,
    "\n The average=",avg)
    return round(avg,2)


def fill_configuration_results():
    config_res=[]
    for db in list_db:
        print("New database connection..into",db[1])
        conn = psycopg2.connect(database=db[1], user=POSTGRES_USER,
         password=POSTGRES_PASSWORD, host=POSTGRES_HOST, 
         port=POSTGRES_PORT)
        cur = conn.cursor()
        print("\n Start executing BerlinMOD queries:")
        for query in list_queries:
            average_execution = average_execution_time(cur,
            query[list(query.keys())[0]])
            if query[list(query.keys())[0]] not in\
            [li[list(li.keys())[0]] for li in config_res]:
                new_res= query
                new_res['sf_'+db[1]]=average_execution
                config_res.append(new_res)
                print("\nNew query in config list.",new_res)
            else:
                query_from_config=next(qr for qr in config_res\
                if qr[list(qr.keys())[0]] == query[
                list(query.keys())[0]])
                query_from_config['sf_'+db[1]]=average_execution
                print("\nExisting query was updated.",
                query_from_config)
                
    print("\n Final list of configuration result: ",config_res) 
    return config_res

experiments=fill_configuration_results()
print("Final experiments result:\n",experiments)
result_file = open("experiment_result.txt", "w")
for ex in experiments:
    result_file.write(str(ex.items()))
result_file.close()

with open('cluster-config3-result.csv', 'w', newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',',
     quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(['Query', 'sf005', 'sf02','sf05','sf1'])
    for ex in experiments:
        spamwriter.writerow([list(ex.keys())[0],
        ex[list(ex.keys())[1]], ex[list(ex.keys())[2]],
        ex[list(ex.keys())[3]], ex[list(ex.keys())[4]]])