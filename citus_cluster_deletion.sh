#!/bin/bash
kubectl delete -f "./postgres-secret.yaml"
sleep 5
kubectl delete -f "./workers-deployment.yaml"
sleep 5
kubectl delete -f "./coordinator-deployment.yaml"
