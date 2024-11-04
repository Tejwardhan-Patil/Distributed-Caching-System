#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define the directories
ROOT_DIR=$(pwd)
CACHE_DIR="$ROOT_DIR/cache"
DISTRIBUTED_DIR="$ROOT_DIR/distributed"
CONSISTENCY_DIR="$ROOT_DIR/consistency"
COORDINATION_DIR="$ROOT_DIR/coordination"
NETWORKING_DIR="$ROOT_DIR/networking"
MANAGEMENT_DIR="$ROOT_DIR/management"
SECURITY_DIR="$ROOT_DIR/security"
FAULT_TOLERANCE_DIR="$ROOT_DIR/fault_tolerance"
MONITORING_DIR="$ROOT_DIR/monitoring"
TESTS_DIR="$ROOT_DIR/tests"
DEPLOYMENT_DIR="$ROOT_DIR/deployment"

# Build C++ components
echo "Building C++ components..."
g++ -o $CACHE_DIR/eviction_policies/FIFOPolicy $CACHE_DIR/eviction_policies/FIFOPolicy.cpp
g++ -o $CACHE_DIR/SSDStore $CACHE_DIR/SSDStore.cpp
g++ -o $DISTRIBUTED_DIR/DistributedCache $DISTRIBUTED_DIR/DistributedCache.cpp
g++ -o $CONSISTENCY_DIR/StrongConsistency $CONSISTENCY_DIR/StrongConsistency.cpp
g++ -o $CONSISTENCY_DIR/conflict_resolution/LastWriteWins $CONSISTENCY_DIR/conflict_resolution/LastWriteWins.cpp
g++ -o $COORDINATION_DIR/leader_election/Paxos $COORDINATION_DIR/leader_election/Paxos.cpp
g++ -o $COORDINATION_DIR/HeartbeatManager $COORDINATION_DIR/heartbeat/HeartbeatManager.cpp
g++ -o $NETWORKING_DIR/RPCClient $NETWORKING_DIR/rpc/RPCClient.cpp
g++ -o $MANAGEMENT_DIR/AdminConsole $MANAGEMENT_DIR/AdminConsole.cpp
g++ -o $SECURITY_DIR/authentication/APIKeyAuth $SECURITY_DIR/authentication/APIKeyAuth.cpp
g++ -o $SECURITY_DIR/encryption/DataEncryption $SECURITY_DIR/encryption/DataEncryption.cpp
g++ -o $FAULT_TOLERANCE_DIR/data_recovery/LogBasedRecovery $FAULT_TOLERANCE_DIR/data_recovery/LogBasedRecovery.cpp
g++ -o $MONITORING_DIR/dashboard/GrafanaDashboards $MONITORING_DIR/dashboard/GrafanaDashboards.cpp
g++ -o $DEPLOYMENT_DIR/ansible/ServerConfig $DEPLOYMENT_DIR/ansible/ServerConfig.cpp

# Build Java components
echo "Building Java components..."
javac -d $ROOT_DIR/bin $CACHE_DIR/eviction_policies/LRUPolicy.java
javac -d $ROOT_DIR/bin $CACHE_DIR/eviction_policies/LFUPolicy.java
javac -d $ROOT_DIR/bin $CACHE_DIR/serialization/ProtobufSerializer.java
javac -d $ROOT_DIR/bin $DISTRIBUTED_DIR/partitioning/ConsistentHashing.java
javac -d $ROOT_DIR/bin $DISTRIBUTED_DIR/replication/ReplicationStrategy.java
javac -d $ROOT_DIR/bin $DISTRIBUTED_DIR/sharding/ShardManager.java
javac -d $ROOT_DIR/bin $CONSISTENCY_DIR/EventualConsistency.java
javac -d $ROOT_DIR/bin $CONSISTENCY_DIR/conflict_resolution/VectorClocks.java
javac -d $ROOT_DIR/bin $COORDINATION_DIR/leader_election/Raft.java
javac -d $ROOT_DIR/bin $COORDINATION_DIR/membership/MembershipService.java
javac -d $ROOT_DIR/bin $NETWORKING_DIR/rpc/RPCServer.java
javac -d $ROOT_DIR/bin $NETWORKING_DIR/protocols/ThriftProtocol.java
javac -d $ROOT_DIR/bin $MANAGEMENT_DIR/cache_api/Routes.java
javac -d $ROOT_DIR/bin $SECURITY_DIR/authentication/JWTAuth.java
javac -d $ROOT_DIR/bin $SECURITY_DIR/encryption/TLSConfig.java
javac -d $ROOT_DIR/bin $FAULT_TOLERANCE_DIR/failover/FailoverManager.java
javac -d $ROOT_DIR/bin $FAULT_TOLERANCE_DIR/ReplicationRecovery.java
javac -d $ROOT_DIR/bin $MONITORING_DIR/logging/LogConfig.java
javac -d $ROOT_DIR/bin $DEPLOYMENT_DIR/terraform/AWSProvisioning.java

# Install Python dependencies and components
echo "Installing Python components..."
pip install -r $ROOT_DIR/requirements.txt
python -m compileall $CACHE_DIR/persistent_cache/DiskStore.py
python -m compileall $CACHE_DIR/serialization/JsonSerializer.py
python -m compileall $DISTRIBUTED_DIR/replication/MultiMasterReplication.py
python -m compileall $CONSISTENCY_DIR/QuorumConsistency.py
python -m compileall $COORDINATION_DIR/membership/GossipProtocol.py
python -m compileall $NETWORKING_DIR/protocols/GrpcProtocol.py
python -m compileall $MANAGEMENT_DIR/cache_api/API.py
python -m compileall $SECURITY_DIR/authorization/RBAC.py
python -m compileall $FAULT_TOLERANCE_DIR/data_recovery/SnapshotRecovery.py
python -m compileall $MONITORING_DIR/metrics/PrometheusExporter.py

echo "Build process completed successfully."