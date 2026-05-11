#!/bin/bash

docker build -f docker/Dockerfile -t my-app-img .
# docker compose -f docker/docker-compose.yaml up

k3d cluster create my-cluster && k3d image import my-app-img --cluster my-cluster

kubectl apply -f kubernetes/configmap.yaml
# kubectl apply -f kubernetes/pod.yaml

kubectl apply -f kubernetes/app_deployment.yaml

# Для тестирования балансировки
# kubectl run curl-test --image=curlimages/curl -it --rm -- /bin/sh
# curl http://my-app-service:5003/

kubectl apply -f kubernetes/daemon_set.yaml

kubectl apply -f kubernetes/cron_job.yaml
