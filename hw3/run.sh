#!/bin/bash

docker build -f docker/Dockerfile -t my-app-img .
# docker compose -f docker/docker-compose.yaml up

curl -L https://istio.io/downloadIstio | sh -
cd istio-1.25.2 && export PATH=$PWD/bin:$PATH && cd ../

k3d cluster create my-cluster && k3d image import my-app-img --cluster my-cluster
kubectl create namespace space-with-istio

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace

istioctl install --set profile=default -y
kubectl -n istio-system patch svc istio-ingressgateway --type='json' -p '[{"op":"add","path":"/spec/ports/-","value":{"name":"http-envoy-prom","protocol":"TCP","port":15090,"targetPort":15090}}]'
kubectl label namespace space-with-istio istio-injection=enabled

helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace

kubectl apply -f kubernetes/configmap.yaml
# kubectl apply -f kubernetes/pod.yaml

kubectl apply -f kubernetes/app_deployment.yaml
kubectl apply -f kubernetes/gateway.yaml
kubectl apply -f kubernetes/virtual_service.yaml
kubectl apply -f kubernetes/monitor_istio.yaml
kubectl apply -f kubernetes/monitor_my_app.yaml
# kubectl apply -f kubernetes/destination_rule_my_app.yaml

# Для тестирования балансировки
# kubectl run curl-test --image=curlimages/curl -it --rm -- /bin/sh
# curl -v http://istio-ingressgateway.istio-system.svc.cluster.local/api

