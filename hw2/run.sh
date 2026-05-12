#!/bin/bash

# Сборка образа
docker build -f docker/Dockerfile -t my-app-img .

# Установка Istio (может занять время)
curl -L https://istio.io/downloadIstio | sh -
cd istio-1.25.2 && export PATH=$PWD/bin:$PATH && cd ../

# Кластер и namespace
k3d cluster create my-cluster && k3d image import my-app-img --cluster my-cluster
kubectl create namespace space-with-istio

# Установка Istio в кластер
istioctl install --set profile=default -y
kubectl label namespace space-with-istio istio-injection=enabled

# Основные манифесты приложения
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/app_deployment.yaml

# Istio ресурсы
kubectl apply -f kubernetes/gateway.yaml
kubectl apply -f kubernetes/virtual_service.yaml
kubectl apply -f kubernetes/destination_rule_my_app.yaml

# Для тестирования:
# kubectl run curl-test --image=curlimages/curl -it --rm -- /bin/sh
# curl -v http://istio-ingressgateway.istio-system.svc.cluster.local/api