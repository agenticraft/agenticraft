#!/usr/bin/env python3
"""A2A Protocol Demonstration for AgentiCraft"""

import asyncio
import sys
from datetime import datetime

sys.path.insert(0, '/Users/zahere/Desktop/TLV/agenticraft')

from agenticraft.protocols.a2a import ProtocolRegistry
from agenticraft.protocols.a2a import MeshNetwork, AdaptiveModeSelector
from agenticraft.protocols.a2a import TaskRouter
from agenticraft.protocols.a2a import ConsensusProtocol, ConsensusType
from agenticraft.core.agent import Agent


async def demo_mesh_network():
    """Demonstrate mesh network for distributed agents."""
    print("\n🌐 Demo 1: Mesh Network - Distributed Agent Coordination")
    print("-" * 60)
    
    # Create a distributed research team
    print("Creating distributed research nodes...")
    
    # Node 1: Data Collection
    mesh1 = MeshNetwork("data-collector-1")
    await mesh1.start()
    mesh1.register_capability("data_collection")
    mesh1.register_capability("web_scraping")
    
    # Node 2: Data Analysis
    mesh2 = MeshNetwork("analyzer-1")
    await mesh2.start()
    mesh2.register_capability("data_analysis")
    mesh2.register_capability("statistics")
    
    # Node 3: Report Generation
    mesh3 = MeshNetwork("reporter-1")
    await mesh3.start()
    mesh3.register_capability("report_writing")
    mesh3.register_capability("visualization")
    
    print("✅ 3 specialized nodes created")
    
    # Wait for network formation
    await asyncio.sleep(2)
    
    # Show network topology
    print("\nNetwork Topology:")
    for i, mesh in enumerate([mesh1, mesh2, mesh3], 1):
        status = mesh.get_network_status()
        print(f"  Node {i}: {status['node_id']}")
        print(f"    - Active nodes: {status['active_nodes']}")
        print(f"    - Capabilities: {mesh.nodes[mesh.node_id].capabilities}")
    
    # Demonstrate distributed task execution
    print("\n📋 Executing distributed research task...")
    
    tasks = [
        ("Collect market data", "data_collection"),
        ("Analyze trends", "data_analysis"),
        ("Generate report", "report_writing")
    ]
    
    for task_desc, capability in tasks:
        print(f"\n  Task: {task_desc}")
        try:
            # Find nodes with capability
            capable_nodes = await mesh1.discover_capability(capability)
            print(f"  Found {len(capable_nodes)} capable nodes: {capable_nodes}")
            
            # Execute distributed
            result = await mesh1.execute_distributed(
                task=task_desc,
                capability_required=capability,
                strategy="round_robin"
            )
            print(f"  Result: {result}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    # Show metrics
    print("\n📊 Network Metrics:")
    metrics = mesh1.get_metrics()
    print(f"  Messages sent: {metrics['messages_sent']}")
    print(f"  Tasks executed: {metrics['tasks_executed']}")
    print(f"  Connections: {metrics['connections']}")
    
    # Cleanup
    await mesh1.stop()
    await mesh2.stop()
    await mesh3.stop()
    
    print("\n✅ Mesh network demo completed")


async def demo_task_router():
    """Demonstrate centralized task routing."""
    print("\n🎯 Demo 2: Task Router - Centralized Load Balancing")
    print("-" * 60)
    
    # Create central router
    router = TaskRouter("central-dispatcher")
    await router.start()
    print("✅ Central task router started")
    
    # Register worker agents
    workers = [
        ("worker-alpha", ["compute", "optimize"]),
        ("worker-beta", ["compute", "analyze"]),
        ("worker-gamma", ["analyze", "report"]),
        ("worker-delta", ["optimize", "report"])
    ]
    
    print("\nRegistering workers:")
    for worker_id, capabilities in workers:
        router.register_worker(worker_id, capabilities)
        print(f"  - {worker_id}: {capabilities}")
    
    # Submit tasks with different priorities
    print("\n📥 Submitting tasks...")
    
    task_list = [
        ("High Priority: Optimize algorithm", "optimize", 10),
        ("Medium Priority: Analyze dataset", "analyze", 5),
        ("Low Priority: Generate report", "report", 1),
        ("High Priority: Compute results", "compute", 9),
    ]
    
    # Note: In real scenario, workers would process these
    # For demo, we'll just show task distribution
    
    for task_name, capability, priority in task_list:
        print(f"\n  Submitting: {task_name}")
        print(f"    Capability: {capability}, Priority: {priority}")
        
        # In real implementation, this would wait for results
        # For demo, we'll just show the routing decision
        available = router._get_available_workers(capability)
        print(f"    Available workers: {available}")
        
        if available:
            from agenticraft.protocols.a2a.task_router import Task
            task = Task(name=task_name, capability_required=capability, priority=priority)
            selected = router._select_worker(available, task)
            print(f"    Selected worker: {selected}")
    
    # Show router statistics
    print("\n📊 Router Statistics:")
    stats = router.get_stats()
    print(f"  Total tasks: {stats['total_tasks']}")
    print(f"  Task queues: {stats['queues']}")
    print(f"  Worker stats: {stats['workers']}")
    
    # Cleanup
    await router.stop()
    
    print("\n✅ Task router demo completed")


async def demo_consensus():
    """Demonstrate consensus protocol for critical decisions."""
    print("\n🤝 Demo 3: Consensus Protocol - Distributed Decision Making")
    print("-" * 60)
    
    # Create consensus cluster
    print("Creating consensus cluster...")
    nodes = []
    node_names = ["validator-1", "validator-2", "validator-3", "validator-4", "validator-5"]
    
    for name in node_names:
        node = ConsensusProtocol(
            name,
            consensus_type=ConsensusType.BYZANTINE,
            min_nodes=3
        )
        await node.start()
        nodes.append(node)
    
    print(f"✅ Created {len(nodes)} consensus nodes (Byzantine fault tolerance)")
    
    # Wait for cluster formation
    await asyncio.sleep(1)
    
    # Demonstrate consensus proposals
    proposals = [
        {
            "action": "deploy_model",
            "model_name": "gpt-4-turbo",
            "resource_required": 80,
            "resource_available": 100,
            "risk_level": 0.3
        },
        {
            "action": "scale_infrastructure", 
            "scale_factor": 2.0,
            "cost_increase": 150,
            "budget_available": 100,
            "necessity": 0.9
        },
        {
            "action": "update_security_policy",
            "policy_change": "enable_2fa",
            "user_impact": 0.2,
            "security_improvement": 0.8
        }
    ]
    
    print("\n🗳️ Running consensus proposals...")
    
    for i, proposal_content in enumerate(proposals, 1):
        print(f"\n  Proposal {i}: {proposal_content['action']}")
        print(f"    Details: {proposal_content}")
        
        try:
            # Node 0 proposes
            result = await nodes[0].propose(proposal_content, timeout=5.0)
            
            if result:
                print(f"    ✅ ACCEPTED by consensus")
            else:
                print(f"    ❌ REJECTED by consensus")
                
        except Exception as e:
            print(f"    ⚠️ Error: {e}")
    
    # Show consensus statistics
    print("\n📊 Consensus Statistics:")
    stats = nodes[0].get_consensus_stats()
    print(f"  Consensus type: {stats['consensus_type']}")
    print(f"  Total proposals: {stats['total_proposals']}")
    print(f"  Accepted: {stats['proposals_accepted']}")
    print(f"  Rejected: {stats['proposals_rejected']}")
    
    # Cleanup
    for node in nodes:
        await node.stop()
    
    print("\n✅ Consensus demo completed")


async def demo_adaptive_coordination():
    """Demonstrate adaptive mode selection."""
    print("\n🔄 Demo 4: Adaptive Coordination - Smart Protocol Selection")
    print("-" * 60)
    
    # Create mode selector
    selector = AdaptiveModeSelector()
    
    # Different scenarios
    scenarios = [
        {
            "name": "Simple task, few agents",
            "task_complexity": 0.2,
            "agent_count": 3,
            "latency_requirement": 100,
            "reliability_requirement": 0.8
        },
        {
            "name": "Complex task, many agents",
            "task_complexity": 0.9,
            "agent_count": 50,
            "latency_requirement": 5000,
            "reliability_requirement": 0.99
        },
        {
            "name": "Real-time critical task",
            "task_complexity": 0.5,
            "agent_count": 10,
            "latency_requirement": 50,
            "reliability_requirement": 0.95
        },
        {
            "name": "Batch processing",
            "task_complexity": 0.7,
            "agent_count": 20,
            "latency_requirement": 60000,
            "reliability_requirement": 0.9
        }
    ]
    
    print("Analyzing scenarios for optimal coordination mode...\n")
    
    for scenario in scenarios:
        print(f"📌 Scenario: {scenario['name']}")
        print(f"   - Task complexity: {scenario['task_complexity']:.1%}")
        print(f"   - Agent count: {scenario['agent_count']}")
        print(f"   - Latency requirement: {scenario['latency_requirement']}ms")
        print(f"   - Reliability requirement: {scenario['reliability_requirement']:.1%}")
        
        # Select mode
        mode = await selector.select_mode(**{k: v for k, v in scenario.items() if k != 'name'})
        print(f"   🎯 Recommended mode: {mode.upper()}")
        
        # Simulate execution and update performance
        import random
        success = random.random() < scenario['reliability_requirement']
        latency = random.uniform(50, scenario['latency_requirement'])
        
        selector.update_performance(
            mode=mode,
            success=success,
            latency=latency,
            resource_usage={"cpu": random.uniform(20, 80)}
        )
        
        print(f"   📊 Simulated result: {'✅ Success' if success else '❌ Failed'} ({latency:.0f}ms)\n")
    
    # Show performance statistics
    print("📈 Mode Performance Statistics:")
    stats = selector.get_mode_stats()
    for mode, perf in stats.items():
        print(f"  {mode}:")
        print(f"    - Success rate: {perf['success_rate']:.1%}")
        print(f"    - Avg latency: {perf['avg_latency']:.0f}ms")
        print(f"    - Total tasks: {perf['total_tasks']}")
    
    print("\n✅ Adaptive coordination demo completed")


async def demo_real_world_scenario():
    """Demonstrate a real-world multi-agent scenario."""
    print("\n🏢 Demo 5: Real-World Scenario - Multi-Agent Customer Support")
    print("-" * 60)
    
    print("Setting up distributed customer support system...\n")
    
    # Create specialized support nodes
    nodes = {
        "triage": MeshNetwork("support-triage"),
        "technical": MeshNetwork("support-technical"),
        "billing": MeshNetwork("support-billing"),
        "escalation": MeshNetwork("support-escalation")
    }
    
    # Start all nodes
    for node in nodes.values():
        await node.start()
    
    # Register capabilities
    nodes["triage"].register_capability("initial_assessment")
    nodes["triage"].register_capability("routing")
    
    nodes["technical"].register_capability("troubleshooting")
    nodes["technical"].register_capability("bug_reporting")
    
    nodes["billing"].register_capability("payment_issues")
    nodes["billing"].register_capability("subscription_management")
    
    nodes["escalation"].register_capability("complex_issues")
    nodes["escalation"].register_capability("management_approval")
    
    print("✅ Support system initialized with 4 specialized nodes")
    
    # Simulate customer requests
    customer_requests = [
        ("My app keeps crashing", "troubleshooting"),
        ("I was charged twice", "payment_issues"),
        ("Need to cancel subscription", "subscription_management"),
        ("Critical bug affecting business", "complex_issues")
    ]
    
    print("\n📞 Processing customer requests...")
    
    for request, required_capability in customer_requests:
        print(f"\n  Customer: '{request}'")
        
        # Triage first
        print("  → Triaging request...")
        
        # Find appropriate handler
        capable_nodes = []
        for node in nodes.values():
            node_caps = await node.discover_capability(required_capability)
            capable_nodes.extend(node_caps)
        
        if capable_nodes:
            print(f"  → Routing to: {required_capability} specialist")
            
            # Simulate handling
            await asyncio.sleep(0.5)
            
            # Check if escalation needed
            if "critical" in request.lower() or "business" in request.lower():
                print("  → Escalating to management")
                escalation_result = await nodes["escalation"].execute_distributed(
                    task=f"Handle escalated issue: {request}",
                    capability_required="management_approval",
                    strategy="round_robin"
                )
                print(f"  ✅ Resolved with escalation")
            else:
                print(f"  ✅ Resolved by {required_capability} team")
        else:
            print(f"  ❌ No handler available for {required_capability}")
    
    # Show system metrics
    print("\n📊 Support System Metrics:")
    total_messages = 0
    total_tasks = 0
    
    for name, node in nodes.items():
        metrics = node.get_metrics()
        total_messages += metrics.get("messages_sent", 0)
        total_tasks += metrics.get("tasks_executed", 0)
        print(f"  {name}: {metrics.get('messages_sent', 0)} messages, {metrics.get('tasks_executed', 0)} tasks")
    
    print(f"\n  Total: {total_messages} messages, {total_tasks} tasks handled")
    
    # Cleanup
    for node in nodes.values():
        await node.stop()
    
    print("\n✅ Real-world scenario demo completed")


async def main():
    """Run all A2A protocol demonstrations."""
    print("🚀 AgentiCraft A2A Protocol Demonstrations")
    print("=" * 60)
    print("This demo showcases various A2A coordination patterns:")
    print("1. Mesh Network - Distributed coordination")
    print("2. Task Router - Centralized load balancing")
    print("3. Consensus - Distributed decision making")
    print("4. Adaptive Mode - Smart protocol selection")
    print("5. Real-World - Multi-agent customer support")
    print("=" * 60)
    
    demos = [
        demo_mesh_network,
        demo_task_router,
        demo_consensus,
        demo_adaptive_coordination,
        demo_real_world_scenario
    ]
    
    for demo in demos:
        await demo()
        print("\n" + "=" * 60)
        await asyncio.sleep(1)
    
    print("\n🎉 All demonstrations completed!")
    print("\nKey Takeaways:")
    print("- Mesh networks enable decentralized, fault-tolerant coordination")
    print("- Task routers provide efficient centralized load balancing")
    print("- Consensus protocols ensure agreement on critical decisions")
    print("- Adaptive selection optimizes coordination strategy")
    print("- A2A protocols scale from simple to complex multi-agent systems")


if __name__ == "__main__":
    asyncio.run(main())
