# ☸️ K3s High-Availability Cluster

A lightweight yet highly available **K3s Kubernetes cluster** designed for homelab and edge deployments.  
This setup combines **PostgreSQL**, **HAProxy**, and **Keepalived** to provide a fully redundant control-plane endpoint with **Cilium** as the CNI.

---

## 🚀 Overview

This cluster runs a **high-availability (HA) K3s control plane** with:

- 🐘 **2 PostgreSQL nodes** — providing a redundant backend database  
- ⚙️ **HAProxy + Keepalived** — handle API server load balancing and failover  
- ☸️ **3 K3s control-plane nodes** — connected to the shared PostgreSQL backend  
- 🧬 **Cilium** — as the CNI (Container Network Interface)

---

## 🎯 Architecture Summary

```text
Clients (kubectl, nodes, apps)
         |
         v
  10.10.10.150 (VIP)
         |
    [Keepalived]
    /          \
pg-node-1    pg-node-2
(MASTER)     (BACKUP)
[HAProxy]    [HAProxy]
    \          /
     \        /
      \      /
   [Load Balance]
      /  |  \
     /   |   \
   cp1  cp2  cp3
  .154 .153 .151
  :6443 each
```

## 🧩 Components

### 🐘 PostgreSQL (K3s Backend)
- Provides a **shared datastore** for all K3s control-plane nodes.  
- Runs in a **primary/replica** configuration for redundancy.  
- Ensures no single point of failure for Kubernetes state.

### ⚙️ HAProxy + Keepalived
- **HAProxy** distributes incoming traffic to all control-plane nodes on port `6443`.  
- **Keepalived** provides a **Virtual IP (VIP)** — `10.10.10.150` — which automatically fails over between both HAProxy nodes.  
- Together, they ensure the Kubernetes API is always available.

### ☸️ K3s Control Plane
- Three control-plane nodes (`cp1`, `cp2`, `cp3`).  
- Each connects to PostgreSQL for consistent cluster state.  
- Fully HA setup with no embedded etcd dependency.

### 🧬 Cilium (CNI)
- Provides **eBPF-powered networking and security**.  
- Replaces Flannel for improved performance and observability.  
- Enables **Hubble** for network flow visibility and debugging.

## ⚙️ IP Scheme

| Role             | Hostname   | IP Address     | Notes                         |
|------------------|-------------|----------------|--------------------------------|
| 🟢 VIP (Keepalived) | -           | **10.10.10.150** | Floating virtual IP             |
| 🐘 HAProxy / DB     | pg-node-1   | 10.10.10.151   | Keepalived MASTER + HAProxy     |
| 🐘 HAProxy / DB     | pg-node-2   | 10.10.10.152   | Keepalived BACKUP + HAProxy     |
| ☸️ K3s Node         | cp1         | 10.10.10.153   | Control plane node              |
| ☸️ K3s Node         | cp2         | 10.10.10.154   | Control plane node              |
| ☸️ K3s Node         | cp3         | 10.10.10.155   | Control plane node              |



## 🧠 Key Benefits

- ✅ **Highly Available Kubernetes API**  
- ✅ **No Single Point of Failure**  
- ✅ **PostgreSQL-backed Cluster Datastore**  
- ✅ **eBPF-powered Networking with Cilium**  
- ✅ **Production-grade Homelab Architecture**

