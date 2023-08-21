import time
import psycopg2
import psycopg2.extensions
from psycopg2.extras import LoggingConnection, LoggingCursor
import logging
import statistics
import csv


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


list_queries=[

# Spot the ships that are positionned in thier port or even within a radius of 500 meters   

{'Q1':"\
    SELECT T.mmsi, P.code, P.description\
    FROM ports  P, trips  T\
    WHERE ST_Intersects(trajectory(T.trip),\
    ST_Transform(ST_MakeEnvelope(P.longitude,P.latitude, P.longitude+0.001409, P.latitude+0.001409, 4326), 4326));\
"},


## The distance traversed during the period
{'Q2':"\
    SELECT T.mmsi, P.pid, P.Period, SUM(length(atTime(T.Trip, P.Period))) AS Dist\
    FROM Trips T, periods_temp P\
    WHERE T.Trip && P.Period\
    GROUP BY T.mmsi, P.pid, P.Period\
    ORDER BY T.mmsi, P.pid;\
"},


#Which port from Ports have been visited by a maximum number of different ship? 
{'Q3':"\
    WITH PortCount AS (\
    SELECT P.code, COUNT(DISTINCT T.mmsi) AS Hits\
    FROM Trips T, ports P\
    WHERE ST_Intersects(trajectory(T.Trip), ST_Transform(ST_MakeEnvelope(P.longitude,P.latitude, P.longitude+0.01, P.latitude+0.01, 4326), 4326))\
    GROUP BY P.code )\
    SELECT p.code, Hits\
    FROM PortCount AS P\
    WHERE P.Hits = ( SELECT MAX(Hits) FROM PortCount );\
    "}
  ]

POSTGRES_USER="USER"
POSTGRES_PASSWORD="*****"
POSTGRES_HOST="34.66.193.90"
POSTGRES_PORT="30001"

list_db=[('MOBILITYDB', "mobilitydb") ]

def  average_execution_time(cursor,query):
    iterations=[]
    for iter in range(1,4):
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
        print("\n Start executing AIS queries for vessels tracking:")
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
result_file = open("ais_experiment2-result-1dbday.txt", "w")
for ex in experiments:
    result_file.write(str(ex.items()))
result_file.close()

with open('cluster-config3-1daydb-result.csv', 'w', newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',',
     quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(['Query', '1day',])
    for ex in experiments:
        spamwriter.writerow([list(ex.keys())[0],
        ex[list(ex.keys())[1]],])
    