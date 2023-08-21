import time
import psycopg2
import psycopg2.extensions
from psycopg2.extras import LoggingConnection, LoggingCursor
import os
from google.auth import compute_engine
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.client import configuration
from google.cloud import container_v1
import sys
import argparse
from kubernetes.stream import stream



POSTGRES_DB= os.environ['POSTGRES_DB']
POSTGRES_USER= os.environ['POSTGRES_USER']
POSTGRES_PORT= os.environ['POSTGRES_PORT']
POSTGRES_PASSWORD= os.environ['POSTGRES_PASSWORD']



def sample_get_operation(gcp_client,zone,project_id,operation_id):
    # Create a client
    #client = container_v1.ClusterManagerClient()

    # Initialize request argument(s)
    request = container_v1.GetOperationRequest(operation_id=operation_id,
        zone=zone,
        project_id=project_id
    )

    # Make the request
    response = gcp_client.get_operation(request=request)

    # Handle the response
    
    return response.status


def sample_set_node_pool_size(cluster_id,zone,project_id,new_size):
    # Create a client
    res =False
    gcp_client = container_v1.ClusterManagerClient()
    config.load_kube_config()

    ##get the node pool name

    request = container_v1.GetClusterRequest(cluster_id=cluster_id,zone=zone,
        project_id=project_id
    )

    # Make the request
    response_pool = gcp_client.get_cluster(request=request)
    node_pool_id =response_pool.node_pools[0].name
    #print("node_pool_id",node_pool_id)

    # Initialize the Kubernetes client
    v1 = client.AppsV1Api()
    core = client.CoreV1Api()
    
    # compare the new size with the existing cluster size
    # Initialize request argument(s)
    request_size = container_v1.GetNodePoolRequest(project_id=project_id,
        cluster_id=cluster_id,
        node_pool_id=str(node_pool_id),
        zone=zone
    )

    # Make the request
    response = gcp_client.get_node_pool(request=request_size)
    print("new size and existing size",new_size,response.initial_node_count)
    if new_size == response.initial_node_count:
        print("The specified size is the same as your actual GKE cluster size, \
please privide new size other than "+str(response.initial_node_count))
    elif new_size<=2:
        print("The size should be at least 2 nodes, 1 node for the citus-coordinator and 1 node for citus-worker")
    pod_list= core.list_pod_for_all_namespaces(watch=False)
    pods_hosts= [(str(pod.metadata.name),str(pod.spec.node_name),str(pod.status.pod_ip)) for pod in pod_list.items if  pod.metadata.labels.get('app')=='citus-workers']
    print("pods_hosts!!",pods_hosts)
    # Decide wether we scale out or scale in
    if len(pods_hosts) <new_size-1:
        print("Resizing scale-out",new_size)
        # Initialize request argument(s)
        request = container_v1.SetNodePoolSizeRequest(project_id=project_id,zone=zone,
        cluster_id=cluster_id,
        node_pool_id=node_pool_id ,
        node_count=new_size,
        ) 
        # Make the request
        resize_response = gcp_client.set_node_pool_size(request=request)
        operation_id=resize_response.name
        print("Settting up the new size...",operation_id)
        while True:
            operations_status= sample_get_operation(gcp_client,zone,project_id,operation_id)
            print("The resize operation is still...",str(operations_status).split('.')[-1])
            if str(operations_status).split('.')[-1] == 'DONE':
                print("Operation finished...",operations_status)
                print("Resizing citus cluster to ", new_size-1)
                scale_workers=scale_out_workers_stateful_set(v1,core,new_size-1)
                if scale_workers:
                    res = True
                break
    else:
        ###scale in with len(pods_host) -new_size-1
        nb_node_to_delete= len(pods_hosts)- (new_size - 1)
        print("this is the list of host to drain",len(pods_hosts),nb_node_to_delete,pods_hosts,"\n\n",pods_hosts[len(pods_hosts)-nb_node_to_delete:]) 
        scale_workers= scale_in_workers_stateful_set(cluster_id,node_pool_id, zone,project_id,v1,core,gcp_client,nb_node_to_delete,pods_hosts[len(pods_hosts)-nb_node_to_delete:])
        if scale_workers:
            res=True            
    # Handle the response
    print("All consistency operations completed. ")
    return res


def scale_in_workers_stateful_set(cluster_id,node_pool_id,zone,project_id,v1,core,gcp_client,num_nodes,hosts):
        time.sleep(5)
        res = False
     
        #loop on list_pods and mark them
        rebalance_tables_in= scale_in_rebalancing(v1,core,hosts)
        if rebalance_tables_in:
            #for node in hosts:
            #    delete_node=core.delete_node(name=node[1],)
            print("Patching from scale IN...")
            worker_sts=v1.read_namespaced_stateful_set(name="citus-workers", namespace="default")
            worker_sts.spec.replicas-=num_nodes
            firs_op=v1.patch_namespaced_stateful_set(name=worker_sts.metadata.name,
             namespace="default", body=worker_sts) 
            print("Resizing the cluster after scale-in",hosts)
            request = container_v1.SetNodePoolSizeRequest(project_id=project_id,zone=zone,
                cluster_id=cluster_id,
                node_pool_id=node_pool_id ,
                node_count=worker_sts.spec.replicas+1,
                ) 
             # Make the request
            resize_response = gcp_client.set_node_pool_size(request=request)
            operation_id=resize_response.name
            print("Settting up the new size after Scale In...",operation_id)
            while True:
                operations_status= sample_get_operation(gcp_client,zone,project_id,operation_id)
                print("The resize operation is still...",str(operations_status).split('.')[-1])
                if str(operations_status).split('.')[-1] == 'DONE':
                    print("Operation finished...",operations_status)
                    res = True
                    break
        return res
        
def scale_out_workers_stateful_set(v1,core,num_nodes):
    time.sleep(5)
    res = False
    print("Patching from scale OUT..") 
    worker_sts=v1.read_namespaced_stateful_set(name="citus-workers", namespace="default")
    worker_sts.spec.replicas=num_nodes
    firs_op=v1.patch_namespaced_stateful_set(name=worker_sts.metadata.name,
             namespace="default", body=worker_sts)    
    #print("First operation........",firs_op)
    while True:
                pod_list= core.list_pod_for_all_namespaces(watch=False)
                time.sleep(1)
                pod_list = list(filter(lambda i: i.metadata.labels.get('app')=='citus-workers' ,pod_list.items))
                #print("POD LIST", pod_list)
                status=[pod.status.phase for pod in pod_list]
                print("Pods status...", status)
                if len(status)==num_nodes and 'Pending' not in status:
                    #Rebalance the distributed tables
                    rebalance_tables_out= scale_out_rebalancing(v1,core)
                    if rebalance_tables_out:
                        res= True
                        break    

    print("Response. after scale-in or scale-out........")
    return res

def scale_in_rebalancing(v1,core,list_pod):
    time.sleep(5)
    print("######Citus rebalancing for scaling In######",list_pod)
    res =False

    ###run Citus_rebalance()    
    response= core.list_pod_for_all_namespaces()
    for pod in response.items:
        #get only the coordinator
        if pod.metadata.labels.get('app')=='citus-coordinator':
            print("\n => POD " + str(pod.metadata.name)+" have as label:"+str(pod.metadata.labels.get('app'))  + " is " + str(pod.status.phase) + " on Node " + str(pod.spec.node_name))
            node_id = core.read_node(pod.spec.node_name)
            coordinator_host = next((adr.address for adr in node_id.status.addresses if adr.type == "ExternalIP"), None)
            print("coordinatror host",coordinator_host)
            conn = psycopg2.connect(database=POSTGRES_DB, user=POSTGRES_USER,
            password=POSTGRES_PASSWORD, host=coordinator_host, 
            port=POSTGRES_PORT)
            cur = conn.cursor()
            for li in list_pod:
                cur.execute("SELECT * FROM citus_set_node_property('%s' , 5432, 'shouldhaveshards', false) ;"% li[2])
            time.sleep(3)
            cur.execute("SELECT * FROM citus_rebalance_start(drain_only := true);")
            time.sleep(3)
            conn.commit()
            while True:
                cur.execute("SELECT details FROM citus_rebalance_status();")
                records = cur.fetchall()
                ##print("rebalancing still running...",records[0][0].get('task_state_counts'))
                print("rebalancing still running...",records)
                if len(records)!=0 and 'blocked' not in records[0][0].get('task_state_counts').keys() and 'running'\
                 not in records[0][0].get('task_state_counts').keys()\
                 and 'runnable' not in records[0][0].get('task_state_counts').keys():
                    print("deleting the drained node")
                    time.sleep(5)
                    conn.commit()
                    for li in list_pod:
                        cur.execute("DELETE from pg_dist_node where nodename = '%s';" %li[2])
                        #cur.execute("SELECT citus_remove_node('%s', 5432);"%li[2])

                    conn.commit()   
                    cur.close()
                    res =True
                    break
                elif len(records)==0:
                    break
            print("Rebalancing scale in finished")
            # Close the cursor
                                    
            print("Query result",records)
        
    return res

def scale_out_rebalancing(v1, core):
    time.sleep(5)
    print("######Citus rebalancing for scaling out######")
    res =False

    ###run Citus_rebalance()
    response= core.list_pod_for_all_namespaces()
    for pod in response.items:
        #get only the coordinator
        if pod.metadata.labels.get('app')=='citus-coordinator':
            print("\n => POD " + str(pod.metadata.name)+" have as label:"+str(pod.metadata.labels.get('app'))  + " is " + str(pod.status.phase) + " on Node " + str(pod.spec.node_name))
            node_id = core.read_node(pod.spec.node_name)
            print("\n\nNODE:::",node_id.status.addresses)
            coordinator_host = next((adr.address for adr in node_id.status.addresses if adr.type == "ExternalIP"), None)
            print("coordinatror host",coordinator_host)
            conn = psycopg2.connect(database=POSTGRES_DB, user=POSTGRES_USER,
            password=POSTGRES_PASSWORD, host=coordinator_host, 
            port=POSTGRES_PORT)
            cur = conn.cursor()
            print("Start rebalancing the distributed tables..")
            cur.execute("SELECT citus_rebalance_start();")
            time.sleep(5)
            conn.commit()
            while True:
                cur.execute("SELECT details FROM citus_rebalance_status();")
                records = cur.fetchall()
                #print("rebalancing still running...",records[0][0].get('task_state_counts'))
                print("rebalancing still running...",records)
                if len(records)!=0 and 'blocked' not in records[0][0].get('task_state_counts').keys() and 'running'\
                 not in records[0][0].get('task_state_counts').keys()\
                 and 'runnable' not in records[0][0].get('task_state_counts').keys():
                    res =True
                    break
                elif len(records)==0:
                    break
            print("Rebalancing finished")
            # Closing
            cur.close()                        
            print("Query result",records)
        
    return res



def sample_stop_cluster(cluster_id,zone,project_id):
    # Create a client
    res =False
    gcp_client = container_v1.ClusterManagerClient()

    # Initialize request argument(s)
    request = container_v1.GetClusterRequest(cluster_id=cluster_id,zone=zone,
        project_id=project_id
    )

    # Make the request
    response = gcp_client.get_cluster(request=request)
    node_pool_id =response.node_pools[0].name
    request = container_v1.SetNodePoolSizeRequest(project_id=project_id,zone=zone,
        cluster_id=cluster_id,
        node_pool_id=node_pool_id ,
        node_count=0
        ) 
        # Make the request
    resize_response = gcp_client.set_node_pool_size(request=request)
    operation_id=resize_response.name
    print("The cluster "+str(cluster_id)+" will be stopped...")
    while True:
            operations_status= sample_get_operation(gcp_client,zone,project_id,operation_id)
            if str(operations_status).split('.')[-1] == 'DONE':
                print("Operation finished...",operations_status)
                res = True
                break
    if res:
        print("The cluster "+str(cluster_id)+" is stopped.")
    
    # Handle the response
    #print(response)


def sample_start_cluster(cluster_id,zone,project_id,num_nodes):
    # Create a client
    res =False
    gcp_client = container_v1.ClusterManagerClient()

    # Initialize request argument(s)
    request = container_v1.GetClusterRequest(cluster_id=cluster_id,zone=zone,
        project_id=project_id
    )

    # Make the request
    response = gcp_client.get_cluster(request=request)
    node_pool_id =response.node_pools[0].name
    request = container_v1.SetNodePoolSizeRequest(project_id=project_id,zone=zone,
        cluster_id=cluster_id,
        node_pool_id=node_pool_id ,
        node_count=num_nodes
        ) 
        # Make the request
    resize_response = gcp_client.set_node_pool_size(request=request)
    operation_id=resize_response.name
    print("The cluster "+str(cluster_id)+" will be started......")
    while True:
            operations_status= sample_get_operation(gcp_client,zone,project_id,operation_id)
            #print("",str(operations_status).split('.')[-1])
            if str(operations_status).split('.')[-1] == 'DONE':
                print("Operation finished...",operations_status)
                res = True
                break
    if res:
        print("The cluster "+str(cluster_id)+" is started.")
    return res



parser = argparse.ArgumentParser(description='Scaling Citus cluster on GKE.')

parser.add_argument('action', choices=['init','start', 'stop', 'resize','delete'],
                        help='Citus cluster management commands.')
    

parser.add_argument('--cluster-name', dest='cluster_name',
                        help='Name of the cluster.')

parser.add_argument('--cluster-zone', dest='cluster_zone',
                        help='The zone of the cluster.')

parser.add_argument('--cluster-project', dest='cluster_project',
                        help='Project name cluster.')

parser.add_argument('--num-nodes', dest='num_nodes',
                        help='The desired number of nodes to resize the cluster.')
    
args = parser.parse_args()



if args.action=="init":
    
    os.popen('sh ./citus_cluster_initialization.sh')
elif args.action=="start":
    if args.num_nodes and args.cluster_name and args.cluster_zone and args.cluster_project and args.num_nodes:
        #scale_out(args.num_nodes)
        #
        sample_start_cluster(args.cluster_name,args.cluster_zone, args.cluster_project,int(args.num_nodes))
    else:
        print("Number of nodes not specified in the argument --num-nodes")
elif args.action=="stop" and args.cluster_name and args.cluster_zone and args.cluster_project :        
        sample_stop_cluster(args.cluster_name,args.cluster_zone, args.cluster_project)

elif args.action=="resize":
    if args.num_nodes and args.cluster_name and args.cluster_zone and args.cluster_project and args.num_nodes:
        sample_set_node_pool_size(args.cluster_name,args.cluster_zone, args.cluster_project,int(args.num_nodes))
    else:
        print("Number of nodes/name of cluster or zone are not specified in the argument list")
elif args.action=="delete":
        os.popen('sh ./citus_cluster_deletion.sh')
