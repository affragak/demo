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


### K3S DB 

```text
ubuntu@ubuntu-db1:~$ sudo -u postgres psql
psql (17.6 (Ubuntu 17.6-2.pgdg24.04+1))
Type "help" for help.

postgres=# \l
                                                 List of databases
   Name    |  Owner   | Encoding | Locale Provider | Collate |  Ctype  | Locale | ICU Rules |   Access privileges
-----------+----------+----------+-----------------+---------+---------+--------+-----------+-----------------------
 k3s       | k3s      | UTF8     | libc            | C.UTF-8 | C.UTF-8 |        |           |
 postgres  | postgres | UTF8     | libc            | C.UTF-8 | C.UTF-8 |        |           |
 template0 | postgres | UTF8     | libc            | C.UTF-8 | C.UTF-8 |        |           | =c/postgres          +
           |          |          |                 |         |         |        |           | postgres=CTc/postgres
 template1 | postgres | UTF8     | libc            | C.UTF-8 | C.UTF-8 |        |           | =c/postgres          +
           |          |          |                 |         |         |        |           | postgres=CTc/postgres
(4 rows)

postgres=# \c k3s
You are now connected to database "k3s" as user "postgres".
k3s=# \dt
       List of relations
 Schema | Name | Type  | Owner
--------+------+-------+-------
 public | kine | table | k3s
(1 row)

k3s=# SELECT * FROM pg_tables WHERE schemaname = 'public';
 schemaname | tablename | tableowner | tablespace | hasindexes | hasrules | hastriggers | rowsecurity
------------+-----------+------------+------------+------------+----------+-------------+-------------
 public     | kine      | k3s        |            | t          | f        | f           | f
(1 row)

k3s=# \d kine
                                 Table "public.kine"
     Column      |  Type   | Collation | Nullable |             Default
-----------------+---------+-----------+----------+----------------------------------
 id              | bigint  |           | not null | nextval('kine_id_seq'::regclass)
 name            | text    | C         |          |
 created         | integer |           |          |
 deleted         | integer |           |          |
 create_revision | bigint  |           |          |
 prev_revision   | bigint  |           |          |
 lease           | integer |           |          |
 value           | bytea   |           |          |
 old_value       | bytea   |           |          |
Indexes:
    "kine_pkey" PRIMARY KEY, btree (id)
    "kine_id_deleted_index" btree (id, deleted)
    "kine_list_query_index" btree (name, id DESC, deleted)
    "kine_name_id_index" btree (name, id)
    "kine_name_index" btree (name)
    "kine_name_prev_revision_uindex" UNIQUE, btree (name, prev_revision)
    "kine_prev_revision_index" btree (prev_revision)

k3s=#
k3s=# SELECT DISTINCT split_part(name, '/', 1) AS resource_type, COUNT(*)
FROM kine
WHERE deleted = 0
GROUP BY resource_type
ORDER BY resource_type;
       resource_type       | count
---------------------------+-------
                           |  2456
 compact_rev_key           |     1
 compact_rev_key_apiserver |     2
(3 rows)

k3s=#
k3s=#
k3s=# SELECT name, created, create_revision
FROM kine
WHERE name LIKE '/registry/namespaces/%'
AND deleted = 0;
                 name                 | created | create_revision
--------------------------------------+---------+-----------------
 /registry/namespaces/cilium-secrets  |       1 |               0
 /registry/namespaces/default         |       1 |               0
 /registry/namespaces/kube-node-lease |       1 |               0
 /registry/namespaces/kube-public     |       1 |               0
 /registry/namespaces/kube-system     |       1 |               0
(5 rows)

k3s=#
k3s=# SELECT name, created
FROM kine
WHERE name LIKE '/registry/pods/%'
AND deleted = 0;
                            name                             | created
-------------------------------------------------------------+---------
 /registry/pods/kube-system/metrics-server-7bc79d68c6-rqsns  |       0
 /registry/pods/kube-system/cilium-pwjzf                     |       0
 /registry/pods/kube-system/cilium-envoy-fgtkx               |       0
 /registry/pods/kube-system/cilium-operator-757859d448-vfb2p |       0
 /registry/pods/kube-system/cilium-envoy-p9wl5               |       0
 /registry/pods/kube-system/cilium-ldwnp                     |       0
 /registry/pods/kube-system/coredns-89d768874-kj5n5          |       0
 /registry/pods/kube-system/cilium-envoy-xsf6d               |       0
 /registry/pods/kube-system/cilium-82fml                     |       0
(9 rows)

k3s=#
```
