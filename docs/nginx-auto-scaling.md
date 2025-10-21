# KEDA Autoscaling with Nginx

A demonstration of Kubernetes Event-Driven Autoscaling (KEDA) with Nginx deployment, featuring automated load testing and real-time scaling monitoring.

## 📋 Overview

This project demonstrates horizontal pod autoscaling using KEDA based on CPU utilization. The setup automatically scales an Nginx deployment between 3-10 replicas when CPU usage exceeds 40%.

## 🚀 Features

- **CPU-Based Autoscaling**: Scales based on 40% CPU utilization threshold
- **Configurable Replica Range**: 3 minimum, 10 maximum pods
- **Intelligent Cooldown**: 30-second cooldown period between scaling events
- **Load Testing Script**: Python-based concurrent load generator
- **Real-Time Monitoring**: Live pod count and request distribution tracking
- **Even Load Distribution**: Kubernetes service ensures balanced traffic across pods

## 📁 Configuration

### KEDA ScaledObject (`nginx-scaler.yaml`)

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: nginx-scaler
spec:
  scaleTargetRef:
    name: nginx
  minReplicaCount: 3
  maxReplicaCount: 10
  cooldownPeriod: 30
  pollingInterval: 10
  triggers:
    - type: cpu
      metricType: Utilization
      metadata:
        value: "40"
```

### Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `minReplicaCount` | 3 | Minimum number of pods |
| `maxReplicaCount` | 10 | Maximum number of pods |
| `cooldownPeriod` | 30s | Wait time before scaling down |
| `pollingInterval` | 10s | Frequency of metric checks |
| `cpu.value` | 40% | CPU threshold for scaling |

## 📦 Baseline Setup

### Initial Deployment State

Before load testing, the environment was configured with:

**Pods (3 replicas at minimum):**
```bash
kubectl get pods
```
```
NAME                    READY   STATUS    RESTARTS   AGE
nginx-8974df4cf-ljcjn   1/1     Running   0          2d1h
nginx-8974df4cf-xm6dz   1/1     Running   0          2d1h
nginx-8974df4cf-ztlsm   1/1     Running   0          2d1h
```

**Service (LoadBalancer):**
```bash
kubectl get svc
```
```
NAME    TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
nginx   LoadBalancer   10.43.212.55   10.10.10.50   80:30858/TCP   2d2h
```

The LoadBalancer exposes Nginx at `10.10.10.50:80`, which serves as the target for load testing.

## 🧪 Load Testing

### Running the Test

```bash
uv run nginx-keda.py http://10.10.10.50 240 200
```

**Arguments:**
- `http://10.10.10.50` - Target URL
- `240` - Duration in seconds
- `200` - Concurrent users

### Real-Time Scaling Events

The load test script monitors pod scaling in real-time:

```
======================================================================
KEDA AUTOSCALING LOAD TEST
======================================================================
Target URL: http://10.10.10.50
Duration: 240 seconds
Concurrent Users: 200
Initial Pod Count: 3
======================================================================
======================================================================
MONITORING POD SCALING
======================================================================
Time (s)   Pods       Requests     Errors     HPA Status
----------------------------------------------------------------------
35         6          17923        0          3     6
🚀 SCALING EVENT: 3 -> 6 pods
User  3 completed: 543 requests    128        6     6
User  2 completed: 560 requests
```

### Scaling Behavior

The test demonstrates effective autoscaling:
- **Initial State**: 3 pods
- **Scaling Trigger**: CPU utilization exceeded 40% threshold
- **Scale Up Time**: 35 seconds (3 → 6 pods)
- **Requests at Scale Event**: 17,923 requests processed
- **Final State**: 6 pods maintained throughout test
- **Load Distribution**: Even distribution across all pods (~15k-21k requests per pod)

### Test Results

```
======================================================================
LOAD TEST RESULTS
======================================================================
Test Duration: 251.9 seconds
Total Requests: 107830
Successful: 107702
Errors: 128
Requests/sec: 428.07
Final Pod Count: 6
======================================================================
```

## 📊 Pod Distribution

Traffic was evenly distributed across scaled pods:

```
nginx-8974df4cf-ztlsm: 20997 (19.5%) █████████
nginx-8974df4cf-ljcjn: 20854 (19.4%) █████████
nginx-8974df4cf-xm6dz: 20832 (19.3%) █████████
nginx-8974df4cf-h8pbd: 15073 (14.0%) ██████
nginx-8974df4cf-248n5: 15061 (14.0%) ██████
nginx-8974df4cf-t6htr: 14885 (13.8%) ██████
```

## 🔍 Monitoring Commands

### Check HPA Status
```bash
kubectl get hpa keda-hpa-nginx-scaler
```

Output:
```
NAME                    REFERENCE          TARGETS       MINPODS   MAXPODS   REPLICAS   AGE
keda-hpa-nginx-scaler   Deployment/nginx   cpu: 0%/40%   3         10        3          2d1h
```

### Watch Pods Scale
```bash
kubectl get pods -l app=nginx -w
```

### View Current Pods
```bash
kubectl get pods
```

## 🛠️ Setup

### Prerequisites

- Kubernetes cluster
- KEDA installed ([installation guide](https://keda.sh/docs/latest/deploy/))
- kubectl configured
- Python 3.x with `uv` (for load testing)

### Installation

1. **Deploy the ScaledObject**:
   ```bash
   kubectl apply -f nginx-scaler.yaml
   ```

2. **Verify KEDA Configuration**:
   ```bash
   kubectl get scaledobject nginx-scaler
   ```

3. **Check HPA Creation**:
   ```bash
   kubectl get hpa
   ```

## 💡 Key Insights

- **Responsive Scaling**: Pods scaled up in 35 seconds under load
- **Load Balancing**: Kubernetes service distributed ~108k requests evenly
- **Stability**: 99.88% success rate (107,702/107,830 requests)
- **Performance**: Sustained 428 requests/second with 200 concurrent users

## 📚 Additional Resources

- [KEDA Documentation](https://keda.sh/docs/)
- [KEDA CPU Scaler](https://keda.sh/docs/latest/scalers/cpu/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

