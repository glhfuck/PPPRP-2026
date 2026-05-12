# Добавление Istio в существующую Kubernetes-систему

Этот проект расширяет предыдущую систему логирования, добавляя Service Mesh на базе Istio. Вся конфигурация вынесена в отдельный namespace `space-with-istio`, чтобы не пересекаться с другими проектами.

## Что сделано

* Настроен Istio Ingress Gateway для внешнего доступа к API

* Создан VirtualService с маршрутизацией `/api` на основное приложение и возвратом 404 для неизвестных путей

* Настроен DestinationRule с политиками load balancing (LEAST\_CONN, фактически LEAST\_REQUEST) и connection pool

* Включён mutual TLS между сервисами

* Реализован fault injection для тестирования отказоустойчивости: задержка 2с и таймаут 1с на маршруте `/api/log`

* Добавлен специальный эндпоинт `/api/log/delayed` (sleep 5s) для проверки таймаутов

## Установка и запуск

### 0. Подготовка кластера и Istio

```bash
# Собираем образ приложения
docker build -f docker/Dockerfile -t my-app-img .

# Устанавливаем Istio
curl -L https://istio.io/downloadIstio | sh -
cd istio-1.25.2 && export PATH=$PWD/bin:$PATH && cd ../

# Создаём кластер в k3d и настраиваем namespace
k3d cluster create my-cluster && k3d image import my-app-img --cluster my-cluster
kubectl create namespace space-with-istio
istioctl install --set profile=default -y
kubectl label namespace space-with-istio istio-injection=enabled
```

### 1. Развёртывание приложения и Istio-ресурсов

```bash
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/app_deployment.yaml
kubectl apply -f kubernetes/gateway.yaml
kubectl apply -f kubernetes/virtual_service.yaml
kubectl apply -f kubernetes/destination_rule_my_app.yaml
```

Проверяем поды:

```bash
kubectl get deployments -n space-with-istio
kubectl get pods -n space-with-istio
```

![](images/check_namespace.png)

### 2. Тестирование Gateway и маршрутов

Запускаем временный pod с curl:

```bash
kubectl run curl-test --image=curlimages/curl -it --rm -- /bin/sh
```

Обращаемся через ingress-шлюз:

```bash
curl -v http://istio-ingressgateway.istio-system.svc.cluster.local/api
curl -v http://istio-ingressgateway.istio-system.svc.cluster.local/wrong
```

![](images/test_gateway.png)

Видно, что `/api` работает, а неизвестный путь возвращает 404 (настроен в VirtualService).

### 3. Проверка DestinationRule

Смотрим конфигурацию кластеров Envoy до и после применения DestinationRule:

```bash
istioctl proxy-config clusters istio-ingressgateway-<pod>.istio-system --port 5003 -o json
```

![](images/load_balance.png)

После применения:

* `maxConnections: 3`

* `maxPendingRequests: 5`

* `maxRequestsPerConnection: 1`

* Режим балансировки `LEAST_REQUEST` (автоматически подставился вместо deprecated `LEAST_CONN`)

Обратил внимание, что `LEAST_CONN` помечен как устаревший в документации. Istio silently заменяет его на `LEAST_REQUEST`, что логично.

### 4. Проверка отказоустойчивости

Задержка на 2 секунды для `/api/log`:

```bash
time curl -s -o /dev/null -X POST http://istio-ingressgateway.istio-system.svc.cluster.local/api/log -H 'Content-Type: application/json' -d '{"example":"data"}'
```

```
real  0m 2.03s
user  0m 0.00s
sys   0m 0.00s
```

Таймаут 1 секунда для `/api/log/delayed`:

```bash
time curl -s -v -X POST http://istio-ingressgateway.istio-system.svc.cluster.local/api/log/delayed -H 'Content-Type: application/json' -d '{"example":"data"}'
```

```
* Host istio-ingressgateway.istio-system.svc.cluster.Local:80 was resolved.
* IPv6: (none)
* IPV4: 10.43.97.0
*   Trying 10.43.97.0:80...
* Connected to istio-ingressgateway.istio-system.svc.cluster.local (10.43.97.0) port 80
* using HTTP/1.x
> POST /api/Log/delayed HTTP/1.1
> Host: istio-ingressgateway-istio-system.svc.cluster.local
> User-Agent: curL/8.13.0
> Accept: */*
> Content-Type: appLication/json
> Content-Length: 18
>
* upload completely sent off: 18 bytes
< HTTP/1.1 504 Gateway Timeout
< content-length: 24
< content-type: text/plain
< date: Tue, 12 May 2026 18:45:05 GMT
< server: istio-envoy
<
* Connection #0 to host istio-ingressgateway. istio-system.svc.cluster.Local left intact
upstream request timeoutreal  Øm 3.02s
user  Øm 0.00s
sys   Øm 0.02s

```


Как и ожидалось, получаем `504 Gateway Timeout`, потому что суммарная задержка > 1с.

### 5. Автоматический деплой

Весь процесс свёрнут в скрипт `run.sh`, который можно запустить через `bash run.sh` или `make setup`.
