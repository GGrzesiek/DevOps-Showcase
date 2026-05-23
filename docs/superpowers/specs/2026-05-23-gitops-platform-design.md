# GitOps DevOps Interview Showcase — Design Spec

**Date:** 2026-05-23
**Author:** GGrzesiek
**Status:** Approved

---

## Overview

A production-grade, GitOps-first DevOps platform built to demonstrate full-lifecycle engineering skills in interviews. The project covers six components: Infrastructure-as-Code (Terraform), GitOps deployment (ArgoCD), Application (Flask), CI/CD pipeline (GitHub Actions), Helm chart, and Observability (Prometheus + Grafana + AlertManager). Every resource — app, dashboards, alerts, infra — is declared in Git. Nothing is applied manually.

**Target role:** Full-stack DevOps / Platform Engineer (generalist)
**Stack:** AWS, Terraform, Kubernetes (EKS), ArgoCD, GitHub Actions, Prometheus, Grafana
**Build timeline:** 3 days

---

## Repository Structure

Mono-repo layout with four clearly separated layers:

```
execon-platform/
├── app/                        # Flask microservice
│   ├── src/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── infra/                      # Terraform
│   ├── modules/
│   │   ├── vpc/
│   │   ├── eks/
│   │   └── ecr/
│   └── environments/
│       ├── dev/
│       └── prod/
├── charts/                     # Helm charts
│   ├── flask-app/
│   └── monitoring/
├── manifests/                  # ArgoCD Application CRDs
│   ├── root-app.yaml
│   ├── flask-app-app.yaml
│   └── monitoring-app.yaml
└── .github/
    └── workflows/
        ├── ci.yaml
        └── terraform-plan.yaml
```

---

## Pillar 1 — Infrastructure (Terraform)

### Remote State

- S3 bucket for state storage, per-environment prefix (`dev/`, `prod/`)
- DynamoDB table for state locking
- Both provisioned first via a `bootstrap/` root module (run once manually)

### Modules

**`modules/vpc`**
- 3 public + 3 private subnets across 3 AZs
- NAT gateway (single, cost-optimised for demo)
- VPC flow logs enabled (S3)

**`modules/eks`**
- EKS managed node group: `t3.medium`, min 2 / max 4 nodes
- OIDC provider enabled (required for IRSA)
- aws-load-balancer-controller installed via Helm provider
- ArgoCD installed via Helm provider (bootstraps the GitOps layer)
- IRSA role for ArgoCD to pull from ECR

**`modules/ecr`**
- Private ECR repository
- Image scan on push enabled
- Lifecycle policy: keep last 10 images

### Environments

`infra/environments/dev/` and `infra/environments/prod/` each have their own `terraform.tfvars` and reference the shared modules. Terraform workspaces are used to isolate state.

### CI for Terraform

`.github/workflows/terraform-plan.yaml`: runs `terraform fmt`, `validate`, and `plan` on pull requests targeting `infra/`. Plan output is posted as a PR comment.

---

## Pillar 2 — GitOps (ArgoCD)

### App-of-Apps Pattern

ArgoCD is bootstrapped by Terraform (Helm provider). A single root Application watches `manifests/` and manages all child Applications:

```
root-app (ArgoCD Application)
  └── watches manifests/
       ├── flask-app-app.yaml   → charts/flask-app/
       └── monitoring-app.yaml → charts/monitoring/
```

Sync policy: `automated` with `selfHeal: true` and `prune: true`. Any drift from Git is auto-corrected within 3 minutes.

### Image Tag Update Flow

After CI pushes a new image to ECR, the pipeline commits an updated `image.tag` value to `charts/flask-app/values.yaml`. ArgoCD detects the Git change and syncs the new image to EKS automatically. No `kubectl apply` is ever run by a human.

---

## Pillar 3 — Application (Flask)

### Endpoints

| Route | Purpose | Used by |
|---|---|---|
| `GET /` | Application response | Users |
| `GET /health` | Liveness probe | Kubernetes |
| `GET /ready` | Readiness probe (checks app is ready) | Kubernetes |
| `GET /metrics` | Prometheus scrape endpoint | Prometheus |

### Custom Prometheus Metrics

| Metric | Type | Labels |
|---|---|---|
| `http_requests_total` | Counter | `method`, `endpoint`, `status` |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint` |
| `app_info` | Gauge | `version`, `environment` |

### Dockerfile

Multi-stage build:
1. **Builder stage** (`python:3.12-slim`): installs dependencies
2. **Runtime stage** (`gcr.io/distroless/python3`): copies only the app + installed packages. No shell, no package manager in prod image.

---

## Pillar 4 — CI/CD Pipeline (GitHub Actions)

File: `.github/workflows/ci.yaml` — triggered on push to `main`.

### Stages (sequential, fail-fast)

1. **Lint & Test** — `flake8` + `pytest` with coverage. Fails if coverage < 80%.
2. **Build Image** — `docker buildx build`, tagged with `git-<SHA>` and `latest`.
3. **Security Scan** — Trivy scans the built image. Pipeline fails on `CRITICAL` CVEs.
4. **Push to ECR** — Authenticates via GitHub OIDC (no static AWS credentials stored in repo secrets). Pushes both `git-<SHA>` and `latest` tags.
5. **Update Manifest** — Commits the new `image.tag` to `charts/flask-app/values.yaml`. ArgoCD picks up the change and deploys.

---

## Pillar 5 — Helm Chart (flask-app)

All resources are parameterised via `values.yaml`. Image tag is the only value updated by CI; everything else is stable.

| Resource | Configuration |
|---|---|
| `Deployment` | Resource limits/requests, liveness + readiness probes, rolling update (maxUnavailable: 0) |
| `HorizontalPodAutoscaler` | Scale 2→10 replicas at 70% CPU |
| `PodDisruptionBudget` | `minAvailable: 1` — safe during node drains |
| `ServiceMonitor` | Tells Prometheus to scrape `/metrics` every 15s |
| `Ingress` | AWS Load Balancer Controller annotation → ALB provisioned automatically |
| `NetworkPolicy` | Allow ingress → app; app → Prometheus. Deny all other ingress/egress. |

---

## Pillar 6 — Observability

### Stack

Installed as an ArgoCD Application via `kube-prometheus-stack` Helm chart:
- Prometheus (15s scrape, 7-day retention)
- Grafana (dashboards loaded from ConfigMaps — GitOps-managed, no manual import)
- AlertManager (routes to Slack webhook via secret)
- node-exporter (node-level metrics, zero extra config)

### Grafana Dashboards

Both dashboards are stored as ConfigMap YAML in `charts/monitoring/templates/` and provisioned automatically.

**Dashboard 1: Flask App — RED Metrics**
- Request rate (req/sec) over time
- Error rate (5xx %) — stat panel + time series
- Latency percentiles: p50 / p95 / p99
- Pod count vs HPA maximum (saturation signal)

**Dashboard 2: Kubernetes Cluster Health**
- Per-node CPU and memory usage
- Pod status breakdown (Running / Pending / Failed)
- Deployment desired vs available replicas
- ArgoCD sync status per Application

### AlertManager Rules (PrometheusRule CRD)

All rules stored as PrometheusRule templates in `charts/monitoring/templates/` and deployed by ArgoCD as part of the monitoring Helm chart.

| Severity | Condition | Channel |
|---|---|---|
| Critical | Error rate > 5% for 2 minutes | Slack #alerts |
| Warning | p99 latency > 500ms for 5 minutes | Slack #alerts |
| Warning | Pod restarts > 3 in 10 minutes | Slack #alerts |

---

## Day-by-Day Build Plan

### Day 1 — Infra Foundation
- Write S3 + DynamoDB bootstrap module, apply manually
- Write and apply `modules/vpc`, `modules/ecr`
- Write and apply `modules/eks` (EKS + OIDC + aws-load-balancer-controller)
- Bootstrap ArgoCD via Terraform Helm provider
- Verify: ArgoCD UI accessible, cluster healthy

### Day 2 — GitOps + App
- Flask app: endpoints, custom metrics, tests
- Multi-stage Dockerfile
- Helm chart (`flask-app`) with all 6 resources
- ArgoCD app-of-apps manifests
- GitHub Actions CI pipeline (all 5 stages)
- Verify: push to `main` → image in ECR → ArgoCD syncs → app live behind ALB

### Day 3 — Observability + Polish
- `charts/monitoring` Helm chart with kube-prometheus-stack values
- 2 custom Grafana dashboards as ConfigMaps
- PrometheusRule CRD with 3 alerting rules
- AlertManager Slack webhook integration
- README with architecture diagram (Mermaid or PNG)
- Live demo recording / screenshots

---

## Security Considerations

- **No static AWS credentials** in GitHub secrets — OIDC federation only
- **Distroless runtime image** — no shell attack surface in production pods
- **Trivy in CI** — CRITICAL CVEs block the pipeline
- **NetworkPolicy** — least-privilege pod-to-pod communication
- **IRSA** — ArgoCD and app pods use fine-grained IAM roles, not node instance profile
- **ECR image scanning** — enabled on push at the registry level

---

## Success Criteria

- `git push` to `main` results in a running deployment on EKS with zero manual steps
- ArgoCD UI shows all Applications `Synced` and `Healthy`
- Grafana dashboards display live RED metrics from the Flask app
- At least one AlertManager rule fires and appears in Slack during a simulated error
- Entire infra can be created with `terraform apply` and destroyed with `terraform destroy`
- README explains the architecture clearly enough for an interviewer to follow without asking
