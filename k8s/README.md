# K8s - Kubernetes (Future)

Ce dossier contient les manifestes Kubernetes pour le deploiement cloud de VertiFlow.

## Structure

```
k8s/
└── manifests/
    ├── namespace.yaml               # Namespace vertiflow
    └── deployments.yaml             # Deployments des services
```

## Status

**En cours de developpement** - Les manifestes sont prepares pour un deploiement futur sur Kubernetes.

## Manifestes

### namespace.yaml
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vertiflow
  labels:
    app: vertiflow
    environment: production
```

### deployments.yaml
Deployments pour :
- ClickHouse (StatefulSet)
- Kafka (StatefulSet via Strimzi)
- NiFi (Deployment)
- Services applicatifs

## Deploiement prevu

### Prerequis
- Cluster Kubernetes 1.25+
- Helm 3.x
- Strimzi Operator (Kafka)
- Cert-Manager (TLS)

### Installation
```bash
# Creer le namespace
kubectl apply -f k8s/manifests/namespace.yaml

# Deployer les services
kubectl apply -f k8s/manifests/deployments.yaml
```

## Architecture cible

```
┌─────────────────────────────────────────────────┐
│                  Kubernetes Cluster              │
├─────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │ Kafka   │  │ClickHse │  │ MongoDB │         │
│  │ (3 pods)│  │ (3 pods)│  │ (3 pods)│         │
│  └─────────┘  └─────────┘  └─────────┘         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │  NiFi   │  │ Grafana │  │   ML    │         │
│  │ (2 pods)│  │ (1 pod) │  │ (2 pods)│         │
│  └─────────┘  └─────────┘  └─────────┘         │
└─────────────────────────────────────────────────┘
```

## Roadmap

- [ ] Helm Charts pour chaque service
- [ ] Horizontal Pod Autoscaler
- [ ] Network Policies
- [ ] Secrets management (Vault)
- [ ] Monitoring (Prometheus Operator)
