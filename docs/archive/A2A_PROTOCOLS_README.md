# 🔗 A2A (Agent-to-Agent) Protocol System

## Overview

The A2A Protocol System provides sophisticated coordination mechanisms for multi-agent systems in AgentiCraft. It enables agents to work together efficiently through various coordination patterns.

## 🌟 Features

### 1. **Multiple Coordination Modes**

- **Centralized** - Task routing with load balancing
- **Decentralized** - Peer-to-peer with consensus
- **Hybrid** - Adaptive mesh networks

### 2. **Protocol Types**

#### 🎯 Task Router (Centralized)
- Intelligent task distribution
- Load balancing across workers
- Priority queuing
- Automatic failover
- Performance tracking

#### 🌐 Mesh Network (Hybrid)
- Self-organizing topology
- Automatic peer discovery
- Fault-tolerant routing
- Distributed task execution
- Dynamic load distribution

#### 🤝 Consensus Protocol (Decentralized)
- Multiple consensus algorithms:
  - Simple Majority
  - Byzantine Fault Tolerance
  - Raft Leader Election
  - Proof of Work
- Distributed decision making
- Fault tolerance

#### 🌉 Protocol Bridge
- Connect different protocol types
- Message translation
- Cross-protocol routing
- Unified coordination

## 🚀 Quick Start

### Basic Usage

```python
from agenticraft.protocols.a2a import ProtocolRegistry
from agenticraft.protocols.a2a.hybrid import MeshNetwork

# Create a mesh network node
mesh = MeshNetwork("agent-node-1")
await mesh.start()

# Register capabilities
mesh.register_capability("research")
mesh.register_capability("analysis")

# Execute distributed task
result = await mesh.execute_distributed(
    task="Analyze market trends",
    capability_required="analysis",
    strategy="round_robin"
)
```

### Using with Workflows

```python
from agenticraft.workflows.a2a_integration import A2AWorkflow

# Create A2A-enabled workflow
workflow = A2AWorkflow(
    name="research-workflow",
    coordination_mode="hybrid",
    protocol_name="mesh_network"
)

# Execute with coordination
result = await workflow.execute_with_coordination(
    task="Research quantum computing",
    required_capabilities=["research", "analysis", "writing"],
    strategy="auto"
)
```

## 📊 Architecture

```
┌─────────────────────────────────────┐
│         A2A Protocol System         │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────┐  ┌──────────────┐ │
│  │ Centralized │  │ Decentralized│ │
│  │   Router    │  │  Consensus   │ │
│  └──────┬──────┘  └──────┬───────┘ │
│         │                 │         │
│         └────────┬────────┘         │
│                  │                  │
│           ┌──────┴──────┐           │
│           │   Hybrid    │           │
│           │Mesh Network │           │
│           └──────┬──────┘           │
│                  │                  │
│           ┌──────┴──────┐           │
│           │  Protocol   │           │
│           │   Bridge    │           │
│           └─────────────┘           │
│                                     │
└─────────────────────────────────────┘
```

## 🔧 Configuration

### Mesh Network Options

```python
mesh = MeshNetwork(
    node_id="agent-1",
    max_connections=5,      # Max direct peer connections
    discovery_interval=30.0  # Peer discovery interval (seconds)
)
```

### Task Router Options

```python
router = TaskRouter(
    node_id="central-router"
)

# Configure router
router.config.update({
    "max_retries": 3,
    "task_timeout": 300.0,    # 5 minutes
    "scheduler_interval": 0.5,
    "monitor_interval": 10.0
})
```

### Consensus Options

```python
consensus = ConsensusProtocol(
    node_id="validator-1",
    consensus_type=ConsensusType.BYZANTINE,
    min_nodes=3  # Minimum nodes for consensus
)
```

## 📈 Adaptive Mode Selection

The system can automatically select the best coordination mode:

```python
from agenticraft.protocols.a2a.hybrid import AdaptiveModeSelector

selector = AdaptiveModeSelector()

# System analyzes context and selects mode
mode = await selector.select_mode(
    task_complexity=0.8,      # 0-1 scale
    agent_count=20,           # Number of agents
    latency_requirement=100,  # Max latency in ms
    reliability_requirement=0.95  # Required success rate
)
# Returns: "centralized", "decentralized", or "hybrid"
```

## 🧪 Testing

### Run Tests
```bash
# Test A2A protocols
python test_a2a_protocols.py

# Run demonstrations
python examples/a2a_protocols_demo.py
```

### Test Individual Protocols

```python
# Test mesh network
mesh1 = MeshNetwork("node1")
mesh2 = MeshNetwork("node2")
await mesh1.start()
await mesh2.start()

# They will auto-discover each other
await asyncio.sleep(2)

# Check network status
status = mesh1.get_network_status()
print(f"Active nodes: {status['active_nodes']}")
```

## 🎯 Use Cases

### 1. **Distributed Research Team**
```python
# Multiple agents with different expertise
researcher = Agent(name="Researcher", capabilities=["research"])
analyst = Agent(name="Analyst", capabilities=["analysis"])
writer = Agent(name="Writer", capabilities=["writing"])

# Coordinate through mesh network
mesh = MeshNetwork("research-coordinator")
await mesh.register_agent(researcher)
await mesh.register_agent(analyst)
await mesh.register_agent(writer)
```

### 2. **Load-Balanced Processing**
```python
# Central router distributes tasks
router = TaskRouter("load-balancer")

# Register worker pools
for i in range(10):
    router.register_worker(f"worker-{i}", ["compute", "process"])

# Submit tasks with priorities
await router.route_task(
    "Process dataset",
    capability="process",
    priority=10  # High priority
)
```

### 3. **Critical Decision Making**
```python
# Consensus for important decisions
nodes = []
for i in range(5):
    node = ConsensusProtocol(f"validator-{i}")
    await node.start()
    nodes.append(node)

# Propose critical change
accepted = await nodes[0].propose({
    "action": "deploy_to_production",
    "version": "2.0",
    "risk_assessment": 0.3
})
```

## 📊 Monitoring

### Get Protocol Metrics

```python
# Mesh network metrics
metrics = mesh.get_metrics()
print(f"Messages sent: {metrics['messages_sent']}")
print(f"Tasks executed: {metrics['tasks_executed']}")

# Router statistics  
stats = router.get_stats()
print(f"Pending tasks: {stats['pending_tasks']}")
print(f"Worker performance: {stats['workers']}")

# Consensus statistics
consensus_stats = consensus.get_consensus_stats()
print(f"Proposals accepted: {consensus_stats['proposals_accepted']}")
```

### Protocol Registry Statistics

```python
registry = ProtocolRegistry()
stats = registry.get_statistics()
print(f"Total protocols: {stats['total_protocols']}")
print(f"Active instances: {stats['total_instances']}")
```

## ⚡ Performance Considerations

1. **Mesh Networks**
   - Best for: Distributed, fault-tolerant systems
   - Overhead: ~10-50ms per hop
   - Scalability: Good (100+ nodes)

2. **Task Router**
   - Best for: High-throughput, centralized control
   - Overhead: ~1-5ms per task
   - Scalability: Excellent (1000+ tasks/sec)

3. **Consensus Protocol**
   - Best for: Critical decisions, Byzantine environments
   - Overhead: ~100-500ms per decision
   - Scalability: Limited (optimal: 5-20 nodes)

## 🔒 Security Features

- Message authentication
- Node identity verification
- Byzantine fault tolerance (consensus)
- Timeout protection
- Resource limit enforcement

## 🐛 Troubleshooting

### Common Issues

1. **"No nodes found with capability"**
   - Ensure nodes are started and connected
   - Check capability registration
   - Wait for discovery timeout

2. **"Consensus timeout"**
   - Increase timeout value
   - Check minimum node requirement
   - Verify network connectivity

3. **"Task routing failed"**
   - Check worker registration
   - Verify worker capabilities
   - Monitor worker health

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Get detailed protocol info
print(mesh.get_network_status())
print(router.get_stats())
print(consensus.get_consensus_stats())
```

## 🔄 Migration Guide

### From Basic Workflows to A2A

```python
# Before: Basic workflow
workflow = Workflow("research")
result = await workflow.execute("Research AI")

# After: A2A-enabled workflow
workflow = A2AWorkflow(
    "research",
    coordination_mode="hybrid"
)
result = await workflow.execute_with_coordination(
    "Research AI",
    required_capabilities=["research", "analysis"]
)
```

## 📚 API Reference

### Core Classes

- `Protocol` - Base protocol interface
- `MeshNetwork` - Distributed mesh coordination
- `TaskRouter` - Centralized task routing
- `ConsensusProtocol` - Consensus algorithms
- `ProtocolBridge` - Cross-protocol communication
- `ProtocolRegistry` - Protocol management
- `A2AWorkflow` - A2A-enabled workflows

### Key Methods

- `start()` / `stop()` - Lifecycle management
- `register_capability()` - Declare node capabilities
- `execute_distributed()` - Distributed execution
- `route_task()` - Route task to worker
- `propose()` - Propose for consensus
- `get_network_status()` - Network information
- `get_metrics()` / `get_stats()` - Performance data

---

For more examples, see `examples/a2a_protocols_demo.py`
