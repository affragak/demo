🧠 K3s High-Availability Cluster

A lightweight yet highly available K3s Kubernetes cluster designed for homelab and edge deployments.
This setup combines PostgreSQL, HAProxy, and Keepalived to provide a fully redundant control-plane endpoint with Cilium as the CNI.

🚀 Overview

This cluster runs a high-availability (HA) K3s control plane with:

2 PostgreSQL nodes providing a redundant backend database

HAProxy + Keepalived on the same nodes for API server load balancing and failover

3 K3s control-plane nodes connected to the shared PostgreSQL backend

Cilium as the CNI (Container Network Interface)

The architecture ensures fault tolerance, automatic failover, and stable networking for all workloads.

🎯 Architecture Summary
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

🧩 Components
🐘 PostgreSQL (K3s Backend)

Provides a shared datastore for the K3s control planes.

Both nodes replicate the K3s data, ensuring no single point of failure.

PostgreSQL runs in a primary/replica setup.

⚙️ HAProxy + Keepalived

HAProxy load-balances incoming K3s API requests (:6443) across all control-plane nodes.

Keepalived provides a Virtual IP (VIP) — 10.10.10.150 — which floats between both HAProxy nodes.

Ensures continuous API availability even if one node fails.

☸️ K3s Control Plane

3 nodes: cp1, cp2, and cp3

All control-plane nodes connect to PostgreSQL for state synchronization.

Each runs the K3s API server and scheduler.

🧬 Cilium (CNI)

Provides eBPF-powered networking and security.

Replaces Flannel for high-performance network policies and observability.

Enables direct routing and Hubble for network visibility.

⚙️ IP Scheme
Role	Hostname	IP Address	Notes
VIP (Keepalived)	-	10.10.10.150	Floating virtual IP
HAProxy / DB	pg-node-1	10.10.10.156	Keepalived MASTER + HAProxy
HAProxy / DB	pg-node-2	10.10.10.155	Keepalived BACKUP + HAProxy
K3s Node	cp1	10.10.10.154	Control plane node
K3s Node	cp2	10.10.10.153	Control plane node
K3s Node	cp3	10.10.10.151	Control plane node
