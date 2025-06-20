"""Customer Service Desk workflow for AgentiCraft.

This is the second hero workflow - a multi-tier customer service system with
intelligent routing, load balancing, and human-in-the-loop escalation.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from agenticraft.agents.patterns import (
    EscalationManager,
    EscalationPriority,
    ServiceMesh,
    ServiceNode,
    NodeRole,
)
from agenticraft.core import Agent, Workflow, WorkflowConfig
from agenticraft.core.auth import APIKeyAuth


class CustomerServiceDesk(Workflow):
    """Multi-tier customer service desk with escalation.
    
    This hero workflow demonstrates the power of distributed agent coordination
    by automatically:
    - Routing customer inquiries to appropriate agents
    - Load balancing across service tiers
    - Escalating complex issues
    - Integrating human approval when needed
    
    Example:
        ```python
        from agenticraft.workflows import CustomerServiceDesk
        
        desk = CustomerServiceDesk()
        response = await desk.handle(
            customer_id="cust_123",
            inquiry="I need help with my billing issue"
        )
        ```
    
    Args:
        tiers: List of tier names (default: ["L1", "L2", "Expert"])
        agents_per_tier: Agents per tier (default: [3, 2, 1])
        provider: LLM provider for all agents
        model: Model to use for all agents
        name: Name for this service desk
        enable_auth: Whether to enable API key authentication
        **kwargs: Additional configuration
    """
    
    def __init__(
        self,
        tiers: Optional[List[str]] = None,
        agents_per_tier: Optional[List[int]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        name: str = "CustomerServiceDesk",
        enable_auth: bool = True,
        **kwargs
    ):
        # Initialize workflow
        config = WorkflowConfig(
            name=name,
            description="Multi-tier customer service with intelligent routing and escalation",
            **kwargs
        )
        super().__init__(config)
        
        # Configuration
        self.tiers = tiers or ["L1", "L2", "Expert"]
        self.agents_per_tier = agents_per_tier or [3, 2, 1]
        self.provider = provider
        self.model = model
        
        # Ensure we have the same number of tiers and agent counts
        if len(self.tiers) != len(self.agents_per_tier):
            raise ValueError("Number of tiers must match agents_per_tier list")
        
        # Components
        self.mesh = ServiceMesh()
        self.escalation_manager = EscalationManager(
            default_timeout_minutes=15,
            auto_assign=True
        )
        
        # Authentication
        self.auth_enabled = enable_auth
        if enable_auth:
            self.auth = APIKeyAuth.create_default()
        else:
            self.auth = None
        
        # Set up the service desk
        self._setup_agents()
        self._setup_escalation()
        
        # Metrics
        self.total_handled = 0
        self.escalation_count = 0
        self.resolution_times = []
        self.customer_sessions = {}
    
    def _setup_agents(self):
        """Set up service agents across tiers."""
        # Use default model from settings if not specified
        from agenticraft.core.config import settings
        model = self.model or settings.default_model
        
        # Map tiers to node roles
        role_mapping = {
            0: NodeRole.FRONTLINE,  # L1
            1: NodeRole.SPECIALIST,  # L2
            2: NodeRole.EXPERT,      # Expert/L3
        }
        
        # Topic specialties for different agent types
        specialty_sets = [
            {"billing", "payments", "invoices"},
            {"technical", "bugs", "features"},
            {"account", "security", "privacy"},
            {"general", "how-to", "getting-started"}
        ]
        
        # Create agents for each tier
        total_agents = 0
        for tier_idx, (tier_name, agent_count) in enumerate(zip(self.tiers, self.agents_per_tier)):
            role = role_mapping.get(tier_idx, NodeRole.FRONTLINE)
            
            for agent_idx in range(agent_count):
                # Create specialized agent
                agent_name = f"{tier_name}_Agent_{agent_idx + 1}"
                
                # Assign specialties (rotate through specialty sets)
                specialties = specialty_sets[total_agents % len(specialty_sets)]
                
                # Create agent with appropriate instructions
                if role == NodeRole.FRONTLINE:
                    instructions = f"""You are a {tier_name} customer service agent.
You handle initial customer inquiries with empathy and efficiency.
Your specialties: {', '.join(specialties)}

Guidelines:
1. Be friendly and professional
2. Gather necessary information
3. Provide clear solutions when possible
4. Escalate complex issues appropriately
5. Always confirm customer satisfaction"""
                
                elif role == NodeRole.SPECIALIST:
                    instructions = f"""You are a {tier_name} specialist agent.
You handle escalated issues requiring deeper expertise.
Your specialties: {', '.join(specialties)}

Guidelines:
1. Review the full conversation history
2. Provide detailed technical solutions
3. Explain complex issues clearly
4. Escalate to experts only when necessary
5. Document solutions for future reference"""
                
                else:  # EXPERT
                    instructions = f"""You are an expert {tier_name} agent.
You handle the most complex customer issues.
Your specialties: {', '.join(specialties)}

Guidelines:
1. Provide authoritative solutions
2. Make decisions on edge cases
3. Handle sensitive customer situations
4. Coordinate with product teams if needed
5. Ensure complete issue resolution"""
                
                # Create the agent
                agent = Agent(
                    name=agent_name,
                    instructions=instructions,
                    provider=self.provider,
                    model=model
                )
                
                # Add to mesh
                node = self.mesh.add_node(
                    agent=agent,
                    role=role,
                    specialties=specialties,
                    max_capacity=5 if role == NodeRole.FRONTLINE else 3
                )
                
                total_agents += 1
        
        # Add coordinator agent for complex routing decisions
        coordinator = Agent(
            name=f"{self.config.name}_Router",
            instructions="""You are the customer service routing coordinator.
Analyze customer inquiries and route them to the most appropriate agent based on:
1. Topic and required expertise
2. Agent availability and current load
3. Customer priority and history
4. Issue complexity""",
            provider=self.provider,
            model=model
        )
        
        self.mesh.coordinator = coordinator
        
    def _setup_escalation(self):
        """Set up human reviewers for escalation."""
        # Add some default reviewers
        self.escalation_manager.add_reviewer(
            "supervisor_1",
            "Sarah Johnson",
            max_concurrent=3,
            specialties={"billing", "refunds", "complaints"}
        )
        
        self.escalation_manager.add_reviewer(
            "supervisor_2",
            "Mike Chen",
            max_concurrent=3,
            specialties={"technical", "features", "bugs"}
        )
        
        self.escalation_manager.add_reviewer(
            "manager_1",
            "Lisa Rodriguez",
            max_concurrent=5,
            specialties=set()  # Handles all escalations
        )
        
        # Register escalation callbacks
        self.mesh.register_escalation_handler(self._handle_service_escalation)
    
    async def handle(
        self,
        customer_id: str,
        inquiry: str,
        context: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle a customer service inquiry.
        
        Args:
            customer_id: Customer identifier
            inquiry: Customer's question or issue
            context: Additional context (order ID, account info, etc.)
            priority: Priority level (1-10)
            api_key: API key for authentication (if enabled)
            
        Returns:
            Dictionary containing:
            - response: Agent's response to customer
            - agent: Name of agent who handled it
            - resolution_path: List of agents involved
            - escalated: Whether it was escalated
            - resolution_time: Time to resolve in seconds
        """
        start_time = datetime.utcnow()
        
        # Authenticate if enabled
        if self.auth_enabled:
            if not api_key:
                return {
                    "error": "API key required",
                    "status": "unauthorized"
                }
            
            client_id = self.auth.authenticate(api_key)
            if not client_id:
                return {
                    "error": "Invalid API key",
                    "status": "unauthorized"
                }
        
        # Track customer session
        if customer_id not in self.customer_sessions:
            self.customer_sessions[customer_id] = []
        
        session = {
            "timestamp": start_time.isoformat(),
            "inquiry": inquiry,
            "context": context
        }
        self.customer_sessions[customer_id].append(session)
        
        # Determine topic from inquiry
        topic = await self._analyze_topic(inquiry, context)
        
        # Route to appropriate agent
        request = await self.mesh.route_request(
            customer_id=customer_id,
            query=inquiry,
            topic=topic,
            priority=priority
        )
        
        # Handle the request
        resolution_path = []
        escalated = False
        final_response = None
        
        try:
            # Process with assigned agent
            max_attempts = len(self.tiers)
            attempt = 0
            
            while attempt < max_attempts and request.status != "resolved":
                if request.assigned_to:
                    node = self.mesh.nodes.get(request.assigned_to)
                    if node:
                        resolution_path.append({
                            "agent": node.agent.name,
                            "role": node.role.value,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                        # Get response from agent
                        agent_response = await self._get_agent_response(
                            node.agent,
                            inquiry,
                            context,
                            request.history
                        )
                        
                        # Check if issue is resolved
                        if await self._is_resolved(agent_response, inquiry):
                            # Mark as resolved
                            await self.mesh.resolve_request(
                                request.request_id,
                                agent_response,
                                node.node_id
                            )
                            final_response = agent_response
                            break
                        
                        # Not resolved - escalate if possible
                        if attempt < max_attempts - 1:
                            escalated = True
                            self.escalation_count += 1
                            
                            # Check if human escalation needed
                            if node.role == NodeRole.EXPERT or self._needs_human_escalation(agent_response):
                                # Create human escalation
                                await self._create_human_escalation(
                                    request,
                                    node.agent.name,
                                    agent_response
                                )
                                final_response = agent_response + "\n\n[Escalated to human supervisor for review]"
                                break
                            else:
                                # Escalate to next tier
                                await self.mesh.escalate_request(
                                    request.request_id,
                                    f"Unable to fully resolve. Agent response: {agent_response[:100]}..."
                                )
                        else:
                            # Final attempt
                            final_response = agent_response
                
                attempt += 1
            
            # If no response yet, provide fallback
            if not final_response:
                final_response = (
                    "I apologize, but I'm having difficulty processing your request at the moment. "
                    "Please try again later or contact our support team directly."
                )
        
        except Exception as e:
            final_response = (
                "I apologize for the technical difficulty. "
                "Your request has been logged and will be addressed by our team."
            )
            resolution_path.append({
                "agent": "System",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Calculate resolution time
        end_time = datetime.utcnow()
        resolution_time = (end_time - start_time).total_seconds()
        self.resolution_times.append(resolution_time)
        
        # Update metrics
        self.total_handled += 1
        
        # Prepare response
        result = {
            "response": final_response,
            "agent": resolution_path[-1]["agent"] if resolution_path else "System",
            "resolution_path": resolution_path,
            "escalated": escalated,
            "resolution_time": resolution_time,
            "request_id": request.request_id,
            "topic": topic,
            "status": request.status
        }
        
        return result
    
    async def _analyze_topic(self, inquiry: str, context: Optional[Dict[str, Any]]) -> str:
        """Analyze inquiry to determine topic."""
        # Simple keyword matching - in production would use NLP
        inquiry_lower = inquiry.lower()
        
        if any(word in inquiry_lower for word in ["bill", "payment", "charge", "refund", "invoice"]):
            return "billing"
        elif any(word in inquiry_lower for word in ["bug", "error", "broken", "crash", "slow"]):
            return "technical"
        elif any(word in inquiry_lower for word in ["account", "password", "login", "security"]):
            return "account"
        elif any(word in inquiry_lower for word in ["how", "tutorial", "guide", "help"]):
            return "how-to"
        else:
            return "general"
    
    async def _get_agent_response(
        self,
        agent: Agent,
        inquiry: str,
        context: Optional[Dict[str, Any]],
        history: List[Dict[str, Any]]
    ) -> str:
        """Get response from an agent."""
        # Build prompt with context
        prompt = f"Customer inquiry: {inquiry}"
        
        if context:
            prompt += f"\n\nContext:\n"
            for key, value in context.items():
                prompt += f"- {key}: {value}\n"
        
        if history:
            prompt += f"\n\nPrevious attempts:\n"
            for entry in history[-3:]:  # Last 3 attempts
                if entry.get("action") == "assigned":
                    prompt += f"- Assigned to {entry.get('agent', 'Unknown')}\n"
        
        prompt += "\n\nProvide a helpful response to resolve the customer's issue."
        
        # Get response
        response = await agent.arun(prompt)
        
        # Extract content
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
    
    async def _is_resolved(self, response: str, inquiry: str) -> bool:
        """Check if the response resolves the inquiry."""
        # Simple heuristic - in production would use more sophisticated checks
        response_lower = response.lower()
        
        # Positive resolution indicators
        resolved_phrases = [
            "resolved",
            "fixed",
            "completed",
            "processed",
            "all set",
            "taken care of",
            "should work now",
            "issue has been addressed"
        ]
        
        # Check for resolution phrases
        if any(phrase in response_lower for phrase in resolved_phrases):
            return True
        
        # Check for follow-up questions (indicates not resolved)
        if "?" in response and any(word in response_lower for word in ["can you", "could you", "please provide"]):
            return False
        
        # Default to resolved if response is substantial
        return len(response) > 100
    
    def _needs_human_escalation(self, response: str) -> bool:
        """Check if human escalation is needed."""
        response_lower = response.lower()
        
        # Escalation triggers
        escalation_triggers = [
            "need supervisor",
            "require approval",
            "beyond my authority",
            "complex issue",
            "special case",
            "policy exception",
            "manual review"
        ]
        
        return any(trigger in response_lower for trigger in escalation_triggers)
    
    async def _create_human_escalation(
        self,
        request: "ServiceRequest",
        agent_name: str,
        agent_response: str
    ):
        """Create human escalation request."""
        escalation = await self.escalation_manager.create_escalation(
            title=f"Customer Service Escalation - {request.topic}",
            description=f"Customer {request.customer_id} requires assistance.\n\n"
                       f"Original inquiry: {request.query}\n\n"
                       f"Agent ({agent_name}) response: {agent_response}",
            requester_id=request.assigned_to or "system",
            requester_name=agent_name,
            priority=EscalationPriority.HIGH if request.priority > 7 else EscalationPriority.MEDIUM,
            context={
                "request_id": request.request_id,
                "customer_id": request.customer_id,
                "topic": request.topic,
                "history": request.history
            }
        )
        
        # Register callback for when escalation is resolved
        async def on_resolved(esc_request):
            # Update service request with resolution
            await self.mesh.resolve_request(
                request.request_id,
                f"Resolved by {esc_request.resolved_by}: {esc_request.resolution}",
                esc_request.resolved_by
            )
        
        self.escalation_manager.register_approval_callback(
            escalation.request_id,
            on_resolved
        )
    
    async def _handle_service_escalation(self, request: "ServiceRequest"):
        """Handle service mesh escalation events."""
        # This is called when the mesh escalates
        # Could trigger notifications, logging, etc.
        pass
    
    async def get_desk_status(self) -> Dict[str, Any]:
        """Get current service desk status."""
        mesh_status = await self.mesh.get_node_status()
        escalation_stats = self.escalation_manager.get_statistics()
        
        avg_resolution_time = (
            sum(self.resolution_times) / len(self.resolution_times)
            if self.resolution_times else 0
        )
        
        return {
            "desk_name": self.config.name,
            "total_handled": self.total_handled,
            "escalation_rate": (
                self.escalation_count / self.total_handled if self.total_handled > 0 else 0
            ),
            "avg_resolution_time": avg_resolution_time,
            "mesh_status": mesh_status,
            "escalation_stats": escalation_stats,
            "auth_enabled": self.auth_enabled,
            "registered_clients": (
                len(self.auth.list_clients()) if self.auth else 0
            )
        }
    
    async def add_human_reviewer(
        self,
        reviewer_id: str,
        name: str,
        max_concurrent: int = 5,
        specialties: Optional[Set[str]] = None
    ):
        """Add a human reviewer for escalations.
        
        Args:
            reviewer_id: Unique identifier
            name: Reviewer's name
            max_concurrent: Max concurrent escalations
            specialties: Topics they specialize in
        """
        self.escalation_manager.add_reviewer(
            reviewer_id=reviewer_id,
            name=name,
            max_concurrent=max_concurrent,
            specialties=specialties
        )
    
    def add_api_key(
        self,
        api_key: str,
        client_id: str,
        client_name: Optional[str] = None,
        permissions: Optional[Set[str]] = None
    ) -> bool:
        """Add an API key for authentication.
        
        Args:
            api_key: The API key
            client_id: Client identifier
            client_name: Client display name
            permissions: Set of permissions
            
        Returns:
            True if added successfully
        """
        if not self.auth:
            raise RuntimeError("Authentication not enabled")
        
        return self.auth.add_key(
            api_key=api_key,
            client_id=client_id,
            client_name=client_name,
            permissions=permissions
        )
    
    def __repr__(self) -> str:
        """String representation."""
        total_agents = len(self.mesh.nodes)
        return (
            f"CustomerServiceDesk(name='{self.config.name}', "
            f"tiers={self.tiers}, "
            f"agents={total_agents}, "
            f"handled={self.total_handled})"
        )
