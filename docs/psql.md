## Setting Up PostgreSQL on Ubuntu

### ⚙️ IP Scheme

| Role             | Hostname   | IP Address     | Notes                         |
|------------------|-------------|----------------|--------------------------------|
| 🐘 Master / DB     | pg-node-1   | 10.10.10.156   | Keepalived MASTER + HAProxy     |
| 🐘 Standby / DB     | pg-node-2   | 10.10.10.155   | Keepalived BACKUP + HAProxy     |

### Installation
```text

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL common files
sudo apt install -y postgresql-common

# Add PostgreSQL repository
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

# Install PostgreSQL 17
sudo apt install -y postgresql-17 postgresql-contrib-17
```


### Configuration on Master Node

Replication and External Access.  
Edit the file: /etc/postgresql/17/main/postgresql.conf

```text

listen_addresses = '*'   # This makes PostgreSQL listen on all network interfaces

# Replication settings
wal_level = replica      # Enable write-ahead logging needed for replication
max_wal_senders = 10     # Allow up to 10 simultaneous replication connections
wal_keep_size = 1GB      # Retain 1GB of WAL logs for replicas to catch up
```


Client Authentication.  
Edit the file: /etc/postgresql/17/main/pg_hba.conf

```text

host    all             all             10.10.10.0/24           scram-sha-256
host    replication     replica         10.10.10.155/32         scram-sha-256
```


### Start PostgreSQL automatically on boot

```text
sudo systemctl enable --now postgresql
```


### K3S Database

```text

-- Create the k3s user with superuser privileges
CREATE ROLE k3s WITH LOGIN SUPERUSER PASSWORD 'login_password';

-- Create database for K3s with the k3s user as owner
CREATE DATABASE k3s OWNER k3s;
-- Verify the user has superuser privileges
\du k3s
-- Create user for replication
CREATE ROLE replica WITH REPLICATION PASSWORD 'replica_password' LOGIN;
-- Exit PostgreSQL
\q
```


### Restart PostgreSQL

```text
sudo systemctl restart postgresql
```

### Replication Setup on Standby Node

```text
# Stop PostgreSQL service
systemctl stop postgresql

# Remove existing data directory (if it exists)
rm -rf /var/lib/postgresql/17/main/

# Create a base backup from the primary server
sudo -u postgres pg_basebackup -h 10.10.10.156 -D /var/lib/postgresql/17/main -U replica -P -v -R
```

Enter the replica_password when prompted.  

Create a standby signal file to tell PostgreSQL this is a replica server:

```text
touch /var/lib/postgresql/17/main/standby.signal
chown postgres:postgres /var/lib/postgresql/17/main/standby.signal
```


### Start PostgreSQL

```text
sudo systemctl start postgresql
```

### Verify Replication

```text
sudo -u postgres psql

-- Check if server is in recovery mode (should be true for replicas)
SELECT pg_is_in_recovery();

-- Check replication lag in seconds
SELECT extract(epoch from now() - pg_last_xact_replay_timestamp()) AS lag_seconds;
-- Exit
\q
```

The first query should return t (true), confirming the server is in recovery mode.  
The second query shows how far behind the replica is from the master - ideally this should be very low (less than a second).  

