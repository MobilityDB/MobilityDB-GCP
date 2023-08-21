#!/bin/bash
kubectl create -f "./postgres-secret.yaml"
sleep 5
kubectl create -f "./coordinator-deployment.yaml"
sleep 5
kubectl create -f "./workers-deployment.yaml"
