## HAProxy + Keepalived

### Installation

```text
sudo apt update
sudo apt install -y haproxy keepalived
```


### Configuration

On both nodes:

```text
sudo tee /etc/haproxy/haproxy.cfg > /dev/null <<'EOF'
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin expose-fd listeners
    stats timeout 30s
    user haproxy
    group haproxy
    daemon
    
    # Increase performance for many connections
    maxconn 4096
    
    # Default SSL/TLS settings
    ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256
    ssl-default-bind-options ssl-min-ver TLSv1.2

defaults
    log     global
    mode    tcp
    option  tcplog
    option  dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000
    timeout tunnel  1h
    
    # Error handling
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http

#---------------------------------------------------------------------
# Statistics page (useful for monitoring)
#---------------------------------------------------------------------
listen stats
    bind *:8404
    mode http
    stats enable
    stats uri /stats
    stats refresh 10s
    stats show-legends
    stats show-node
    # Optional: add authentication
    # stats auth admin:YourSecurePassword123

#---------------------------------------------------------------------
# K3s API Server Load Balancer (Main Configuration)
#---------------------------------------------------------------------
frontend k3s_api_frontend
    bind *:6443
    mode tcp
    option tcplog
    
    # Log all connections for debugging (can disable in production)
    log global
    
    # Use the backend
    default_backend k3s_api_backend

backend k3s_api_backend
    mode tcp
    balance roundrobin
    
    # Enable TCP health checks
    option tcp-check
    
    # Health check settings:
    # - check: enable health checks
    # - inter 2000: check every 2 seconds
    # - rise 2: 2 successful checks = server is UP
    # - fall 3: 3 failed checks = server is DOWN
    # - maxconn 1000: max connections per server
    
    server k3s-cp1 10.10.10.154:6443 check inter 2000 rise 2 fall 3 maxconn 1000
    server k3s-cp2 10.10.10.153:6443 check inter 2000 rise 2 fall 3 maxconn 1000
    server k3s-cp3 10.10.10.151:6443 check inter 2000 rise 2 fall 3 maxconn 1000
EOF
```


### On Master node

```text
# Replace 'ens192' with your actual interface name!
INTERFACE="ens192"  # <-- CHANGE THIS

sudo tee /etc/keepalived/keepalived.conf > /dev/null <<EOF
global_defs {
    router_id K3S_API_LB_MASTER
    enable_script_security
    script_user root
}

# Script to check if HAProxy is running
vrrp_script check_haproxy {
    script "/usr/bin/killall -0 haproxy"
    interval 2        # Check every 2 seconds
    weight 2          # Add 2 to priority if check succeeds
    fall 2            # 2 failures to consider down
    rise 2            # 2 successes to consider up
}

vrrp_instance VI_K3S_API {
    state MASTER
    interface ${INTERFACE}
    virtual_router_id 51      # Must be same on both nodes
    priority 101              # Higher = master (must be higher than backup)
    advert_int 1              # VRRP advertisements every 1 second
    
    authentication {
        auth_type PASS
        auth_pass K3sSecurePass2024  # Change this to a secure password
    }
    
    # The Virtual IP
    virtual_ipaddress {
        10.10.10.150/24 dev ${INTERFACE} label ${INTERFACE}:vip
    }
    
    # Track the HAProxy process
    track_script {
        check_haproxy
    }
    
    # Optional: send email notifications on state change
    # notify_master "/etc/keepalived/notify.sh MASTER"
    # notify_backup "/etc/keepalived/notify.sh BACKUP"
    # notify_fault "/etc/keepalived/notify.sh FAULT"
}
EOF
```


### On backup node

```text
# Replace 'ens192' with your actual interface name!
INTERFACE="ens192"  # <-- CHANGE THIS

sudo tee /etc/keepalived/keepalived.conf > /dev/null <<EOF
global_defs {
    router_id K3S_API_LB_BACKUP
    enable_script_security
    script_user root
}

# Script to check if HAProxy is running
vrrp_script check_haproxy {
    script "/usr/bin/killall -0 haproxy"
    interval 2        # Check every 2 seconds
    weight 2          # Add 2 to priority if check succeeds
    fall 2            # 2 failures to consider down
    rise 2            # 2 successes to consider up
}

vrrp_instance VI_K3S_API {
    state BACKUP
    interface ${INTERFACE}
    virtual_router_id 51      # Must be same on both nodes
    priority 100              # Lower than master
    advert_int 1              # VRRP advertisements every 1 second
    
    authentication {
        auth_type PASS
        auth_pass K3sSecurePass2024  # Must match master password
    }
    
    # The Virtual IP
    virtual_ipaddress {
        10.10.10.50/24 dev ${INTERFACE} label ${INTERFACE}:vip
    }
    
    # Track the HAProxy process
    track_script {
        check_haproxy
    }
}
EOF
```


### Validate Configuration

```text
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
# Should output: "Configuration file is valid"
```


```text
sudo keepalived -t -f /etc/keepalived/keepalived.conf
# Should not show any errors
```


### Start Services

```text
# Enable services to start on boot
sudo systemctl enable haproxy
sudo systemctl enable keepalived

# Start HAProxy first
sudo systemctl restart haproxy
sudo systemctl status haproxy

# Then start Keepalived
sudo systemctl restart keepalived
sudo systemctl status keepalived
```


### Verify VIP

```text
# On master node (should show the VIP):
ip addr show | grep 10.10.10.150

# On backup node (should NOT show the VIP initially):
ip addr show | grep 10.10.10.150
```


### Update DNS

```text
# On all K3s nodes and your workstation:
echo "10.10.10.150 k3s-vm.uclab8.net" | sudo tee -a /etc/hosts
```

### Update K3S Configuration

```text
kubectl config set-cluster default --server=https://k3s-vm.uclab8.net:6443
```


