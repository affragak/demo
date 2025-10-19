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
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.31.6+k3s1 sh -
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


