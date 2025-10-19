## K3S Setup

Create configuration directory and file.  

```text
mkdir -p /etc/rancher/k3s
vim /etc/rancher/k3s/config.yaml
```


Add configuration:
```yaml

# TLS configuration - specify all the IPs and hostnames the API server should listen on
tls-san:
  - 10.10.10.154
  - 10.10.10.153
  - 10.10.10.151
  - k3s-vm.uclab8.net  # DNS name for our future load balancer

# Database configuration - connect directly to the PostgreSQL master
datastore-endpoint: "postgres://k3s:login_password=@10.10.10.156:5432/k3s?sslmode=disable"

# Disabled components - we'll use Cilium instead of these built-in components
disable:  
  - traefik      # Default ingress controller
  - servicelb    # Default load balancer
  - local-storage # Default storage class

# Network configuration - disable built-in networking for Cilium
flannel-backend: none
disable-network-policy: true

# Node configuration
node-ip: 10.10.10.154
node-external-ip: 10.10.10.154
```


### Installation

```text
curl -sfL https://get.k3s.io | sh -
```


### Monitor

```text
journalctl -u k3s -f

# get the server token, this is needed to add more nodes
cat /var/lib/rancher/k3s/server/token
```


### Install Cilium CLI

```text
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
CLI_ARCH=amd64
if [ "$(uname -m)" = "aarch64" ]; then CLI_ARCH=arm64; fi
curl -L --fail --remote-name-all https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}
sha256sum --check cilium-linux-${CLI_ARCH}.tar.gz.sha256sum
sudo tar xzvfC cilium-linux-${CLI_ARCH}.tar.gz /usr/local/bin
rm cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}
```

### Install Cilium

```yaml
# cilium-values.yaml
k8sServiceHost: "10.10.10.154"  # The API server IP
k8sServicePort: "6443"           # The API server port
kubeProxyReplacement: true       # Replace kube-proxy functionality
l2announcements:
  enabled: true                  # Enable L2 announcements for load balancer IPs
externalIPs:
  enabled: true                  # Enable support for externalIPs
k8sClientRateLimit:
  qps: 50                        # Queries per second limit
  burst: 200                     # Burst limit
operator:
  replicas: 1                    # Run a single operator replica
  rollOutPods: true              # Roll out operator pods when config changes
rollOutCiliumPods: true          # Roll out Cilium pods when config changes
gatewayAPI:
  enabled: true                  # Enable Gateway API support
envoy:
  enabled: true                  # Enable Envoy proxy
  securityContext:
    capabilities:
      keepCapNetBindService: true # Required for Envoy to bind to privileged ports
debug:
  enabled: true                  # Enable debug logging
socketLB:
  hostNamespaceOnly: true        # Restrict socket LB to host namespace
```


```text
cilium install -f cilium-values.yaml
```


### Add additional K3S nodes

```text
token: TOKEN # Get this from /var/lib/rancher/k3s/server/node-token on first server
server: https://k3s-vm.uclab8.net:6443  # Connect to the load balancer

# TLS configuration
tls-san:
  - 10.10.10.154
  - 10.10.10.153
  - 10.10.10.151
  - "k3s-vm.uclab8.net"
# Database configuration - use the same master PostgreSQL server as the initial node
datastore-endpoint: "postgres://k3s:login_password=@10.10.10.156:5432/k3s?sslmode=disable"
# Disabled components
disable:
  - traefik
  - servicelb
  - local-storage
# Network configuration
flannel-backend: none
disable-network-policy: true
# Node configuration
node-ip: 10.10.10.151  # Change for each node
node-external-ip: 10.10.10.151  # Change for each node
```



### Verify

On the PostgreSQL master, verify that all nodes are connecting to the database:  
```text
ubuntu@ubuntu-db1:~$ sudo -u postgres psql -c "SELECT client_addr, usename, application_name, state FROM pg_stat_activity WHERE datname='k3s';"

 client_addr  | usename | application_name | state
--------------+---------+------------------+-------
 10.10.10.154 | k3s     |                  | idle
 10.10.10.154 | k3s     |                  | idle
 10.10.10.154 | k3s     |                  | idle
 10.10.10.151 | k3s     |                  | idle
 10.10.10.153 | k3s     |                  | idle
 10.10.10.151 | k3s     |                  | idle
 10.10.10.153 | k3s     |                  | idle
 10.10.10.151 | k3s     |                  | idle
 10.10.10.153 | k3s     |                  | idle
(9 rows)
```


Cilium status:
```text
❯ cilium status --wait
    /¯¯\
 /¯¯\__/¯¯\    Cilium:             OK
 \__/¯¯\__/    Operator:           OK
 /¯¯\__/¯¯\    Envoy DaemonSet:    OK
 \__/¯¯\__/    Hubble Relay:       disabled
    \__/       ClusterMesh:        disabled

DaemonSet              cilium                   Desired: 3, Ready: 3/3, Available: 3/3
DaemonSet              cilium-envoy             Desired: 3, Ready: 3/3, Available: 3/3
Deployment             cilium-operator          Desired: 1, Ready: 1/1, Available: 1/1
Containers:            cilium                   Running: 3
                       cilium-envoy             Running: 3
                       cilium-operator          Running: 1
                       clustermesh-apiserver
                       hubble-relay
Cluster Pods:          2/2 managed by Cilium
Helm chart version:    1.18.0
Image versions         cilium             quay.io/cilium/cilium:v1.18.0@sha256:dfea023972d06ec183cfa3c9e7809716f85daaff042e573ef366e9ec6a0c0ab2: 3
                       cilium-envoy       quay.io/cilium/cilium-envoy:v1.34.4-1753677767-266d5a01d1d55bd1d60148f991b98dac0390d363@sha256:231b5bd9682dfc648ae97f33dcdc5225c5a526194dda08124f5eded833bf02bf: 3
                       cilium-operator    quay.io/cilium/operator-generic:v1.18.0@sha256:398378b4507b6e9db22be2f4455d8f8e509b189470061b0f813f0fabaf944f51: 1


```

K3S nodes:
```text
❯ k get nodes -o wide
NAME         STATUS   ROLES                  AGE     VERSION        INTERNAL-IP    EXTERNAL-IP    OS-IMAGE             KERNEL-VERSION     CONTAINER-RUNTIME
ubuntu-cp1   Ready    control-plane,master   2d21h   v1.31.6+k3s1   10.10.10.154   10.10.10.154   Ubuntu 24.04.3 LTS   6.8.0-71-generic   containerd://2.0.2-k3s2
ubuntu-cp2   Ready    control-plane,master   2d20h   v1.31.6+k3s1   10.10.10.153   10.10.10.153   Ubuntu 24.04.3 LTS   6.8.0-85-generic   containerd://2.0.2-k3s2
ubuntu-cp3   Ready    control-plane,master   2d20h   v1.31.6+k3s1   10.10.10.151   10.10.10.151   Ubuntu 24.04.3 LTS   6.8.0-85-generic   containerd://2.0.2-k3s2

```
