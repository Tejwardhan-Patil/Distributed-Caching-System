# Scaling Guide

## Horizontal Scaling

1. **Add Cache Nodes**
   - Add new nodes using the `/nodes/add` API endpoint.
   - The system will automatically rebalance data across nodes using consistent hashing.

2. **Shard Management**
   - ShardManager (Java) automatically assigns shards to new nodes.
   - Ensure replication factors are met for fault tolerance.

## Vertical Scaling

1. **Increase Memory/CPU Resources**
   - For individual nodes, increase available CPU and memory resources through the underlying infrastructure.
   - On Kubernetes, use `kubectl edit` to adjust resource limits.

## Auto-scaling

1. **Kubernetes HPA**
   - Configure Horizontal Pod Autoscaler (HPA) to automatically scale based on CPU/memory usage.
