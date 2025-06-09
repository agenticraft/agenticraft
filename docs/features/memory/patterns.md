# Memory Patterns Guide

Common patterns and best practices for using AgentiCraft's memory systems effectively.

## Overview

This guide covers practical patterns for implementing memory in your agents, including:
- Conversation memory patterns
- Knowledge management strategies
- Multi-agent memory sharing
- Performance optimization patterns
- Real-world use cases

## Conversation Memory Patterns

### Short-Term vs Long-Term Memory

```python
from agenticraft.memory.vector import ChromaDBMemory
from datetime import datetime, timedelta
from typing import List, Dict, Any

class ConversationMemoryManager:
    """Manage short-term and long-term conversation memory."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        
        # Short-term: In-memory for current session
        self.short_term = []
        self.short_term_limit = 10  # Last 10 exchanges
        
        # Long-term: Persistent vector memory
        self.long_term = ChromaDBMemory(
            collection_name=f"conversations_{agent_id}",
            persist_directory="./memory/conversations"
        )
        
        # Working memory: Current context
        self.working_memory = {}
    
    async def add_exchange(self, user_input: str, agent_response: str):
        """Add a conversation exchange."""
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "agent": agent_response,
            "context": self.working_memory.copy()
        }
        
        # Add to short-term
        self.short_term.append(exchange)
        if len(self.short_term) > self.short_term_limit:
            # Move oldest to long-term
            oldest = self.short_term.pop(0)
            await self._store_long_term(oldest)
        
        # Extract key information for working memory
        await self._update_working_memory(user_input, agent_response)
    
    async def _store_long_term(self, exchange: dict):
        """Store exchange in long-term memory."""
        # Create searchable content
        content = f"User: {exchange['user']}\nAgent: {exchange['agent']}"
        
        await self.long_term.store(
            key=f"exchange_{exchange['timestamp']}",
            value=content,
            metadata={
                "timestamp": exchange["timestamp"],
                "agent_id": self.agent_id,
                "type": "conversation",
                "context": exchange.get("context", {})
            }
        )
    
    async def _update_working_memory(self, user_input: str, agent_response: str):
        """Extract and update working memory."""
        # Extract entities, preferences, facts
        if "my name is" in user_input.lower():
            name = user_input.split("my name is")[-1].strip()
            self.working_memory["user_name"] = name
        
        # Track topics
        if "topics" not in self.working_memory:
            self.working_memory["topics"] = []
        
        # Simple topic extraction (use NLP in production)
        topics = self._extract_topics(user_input)
        self.working_memory["topics"].extend(topics)
    
    async def get_context(self, query: str, include_all: bool = False) -> dict:
        """Get relevant context for a query."""
        context = {
            "working_memory": self.working_memory,
            "recent_exchanges": self.short_term[-5:] if not include_all else self.short_term
        }
        
        # Search long-term memory
        if query:
            relevant_memories = await self.long_term.search(
                query=query,
                limit=5,
                filter={"agent_id": self.agent_id}
            )
            context["relevant_past"] = relevant_memories
        
        return context
    
    def _extract_topics(self, text: str) -> List[str]:
        """Simple topic extraction."""
        # In production, use NLP
        keywords = ["python", "data", "api", "help", "question"]
        return [kw for kw in keywords if kw in text.lower()]
```

### Conversation Summarization

```python
class ConversationSummarizer:
    """Summarize conversations for efficient storage."""
    
    def __init__(self, memory: ChromaDBMemory):
        self.memory = memory
        self.summary_threshold = 20  # Summarize after 20 exchanges
    
    async def summarize_conversation(
        self,
        exchanges: List[Dict[str, str]],
        agent_id: str
    ) -> str:
        """Create conversation summary."""
        # In production, use LLM for summarization
        summary_parts = []
        
        # Extract key points
        topics = set()
        decisions = []
        questions = []
        
        for exchange in exchanges:
            user_text = exchange.get("user", "")
            agent_text = exchange.get("agent", "")
            
            # Extract patterns
            if "?" in user_text:
                questions.append(user_text)
            if any(word in agent_text.lower() for word in ["decided", "will", "going to"]):
                decisions.append(agent_text)
            
            # Extract topics (simplified)
            words = user_text.lower().split() + agent_text.lower().split()
            topics.update([w for w in words if len(w) > 5])
        
        # Build summary
        summary = f"Conversation Summary ({len(exchanges)} exchanges)\n"
        summary += f"Topics discussed: {', '.join(list(topics)[:10])}\n"
        summary += f"Questions asked: {len(questions)}\n"
        summary += f"Decisions made: {len(decisions)}\n"
        
        if questions:
            summary += f"\nKey questions:\n"
            for q in questions[:3]:
                summary += f"- {q}\n"
        
        if decisions:
            summary += f"\nKey decisions:\n"
            for d in decisions[:3]:
                summary += f"- {d}\n"
        
        # Store summary
        await self.memory.store(
            key=f"summary_{agent_id}_{datetime.now().timestamp()}",
            value=summary,
            metadata={
                "type": "conversation_summary",
                "agent_id": agent_id,
                "exchange_count": len(exchanges),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return summary
```

## Knowledge Management Patterns

### Fact Verification System

```python
from agenticraft.memory.graph import KnowledgeGraphMemory

class FactVerificationSystem:
    """Verify and manage facts using both memory types."""
    
    def __init__(self):
        self.vector_memory = ChromaDBMemory(
            collection_name="facts",
            persist_directory="./memory/facts"
        )
        self.knowledge_graph = KnowledgeGraphMemory(capacity=50000)
        self.trust_threshold = 0.8
    
    async def add_fact(
        self,
        fact: str,
        source: str,
        confidence: float = 1.0,
        metadata: Dict[str, Any] = None
    ):
        """Add a fact with verification."""
        # Check for contradictions
        contradictions = await self._check_contradictions(fact)
        
        if contradictions:
            # Resolve contradictions
            resolved_fact = await self._resolve_contradictions(
                fact, contradictions, confidence
            )
            if not resolved_fact:
                return {"success": False, "reason": "Contradicts existing facts"}
            fact = resolved_fact
        
        # Store in both systems
        fact_id = f"fact_{datetime.now().timestamp()}"
        
        # Vector memory for semantic search
        await self.vector_memory.store(
            key=fact_id,
            value=fact,
            metadata={
                "source": source,
                "confidence": confidence,
                "verified": confidence >= self.trust_threshold,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
        )
        
        # Knowledge graph for relationships
        await self.knowledge_graph.store(fact_id, fact)
        
        return {"success": True, "fact_id": fact_id}
    
    async def verify_claim(self, claim: str) -> Dict[str, Any]:
        """Verify a claim against known facts."""
        # Search vector memory
        similar_facts = await self.vector_memory.search(
            query=claim,
            limit=10,
            filter={"verified": True}
        )
        
        if not similar_facts:
            return {
                "verified": False,
                "confidence": 0.0,
                "reason": "No supporting facts found"
            }
        
        # Calculate verification score
        max_similarity = max(f["similarity"] for f in similar_facts)
        supporting_facts = [
            f for f in similar_facts 
            if f["similarity"] > 0.8
        ]
        
        # Check knowledge graph for entity relationships
        entities = self.knowledge_graph.extract_entities(claim)
        graph_support = await self._check_graph_support(entities, claim)
        
        # Combined verification
        confidence = (max_similarity + graph_support) / 2
        
        return {
            "verified": confidence >= self.trust_threshold,
            "confidence": confidence,
            "supporting_facts": supporting_facts[:3],
            "entity_support": graph_support > 0.5
        }
    
    async def _check_contradictions(self, fact: str) -> List[Dict]:
        """Check for contradicting facts."""
        # Search for similar facts
        similar = await self.vector_memory.search(fact, limit=20)
        
        contradictions = []
        for existing in similar:
            if existing["similarity"] > 0.9:
                # Very similar - check if contradicting
                if self._facts_contradict(fact, existing["content"]):
                    contradictions.append(existing)
        
        return contradictions
    
    def _facts_contradict(self, fact1: str, fact2: str) -> bool:
        """Simple contradiction detection."""
        # In production, use NLP
        negation_words = ["not", "never", "no", "false", "incorrect"]
        
        # Check for direct negation
        for neg in negation_words:
            if neg in fact1.lower() and neg not in fact2.lower():
                return True
            if neg in fact2.lower() and neg not in fact1.lower():
                return True
        
        return False
    
    async def _resolve_contradictions(
        self,
        new_fact: str,
        contradictions: List[Dict],
        new_confidence: float
    ) -> Optional[str]:
        """Resolve contradictions based on confidence and recency."""
        # Get highest confidence contradiction
        highest_conf = max(
            contradictions,
            key=lambda x: x["metadata"].get("confidence", 0)
        )
        
        if new_confidence > highest_conf["metadata"].get("confidence", 0):
            # New fact has higher confidence
            # Mark old facts as superseded
            for old_fact in contradictions:
                await self.vector_memory.store(
                    key=old_fact["id"] + "_superseded",
                    value=old_fact["content"],
                    metadata={
                        **old_fact["metadata"],
                        "superseded": True,
                        "superseded_by": new_fact,
                        "superseded_at": datetime.now().isoformat()
                    }
                )
            return new_fact
        else:
            # Existing fact has higher confidence
            return None
    
    async def _check_graph_support(
        self,
        entities: List[Dict],
        claim: str
    ) -> float:
        """Check if entities and relationships support the claim."""
        if not entities:
            return 0.0
        
        support_score = 0.0
        for entity in entities:
            # Check if entity exists in graph
            existing = await self.knowledge_graph.get_entities(
                entity_type=entity["type"]
            )
            
            if any(e["name"] == entity["name"] for e in existing):
                support_score += 0.5
                
                # Check relationships
                rels = await self.knowledge_graph.get_relationships(
                    entity["name"]
                )
                if rels:
                    support_score += 0.5
        
        return min(support_score / len(entities), 1.0)
```

### Knowledge Evolution

```python
class EvolvingKnowledgeBase:
    """Knowledge base that evolves and improves over time."""
    
    def __init__(self):
        self.vector_memory = ChromaDBMemory(collection_name="evolving_kb")
        self.knowledge_graph = KnowledgeGraphMemory()
        self.confidence_decay = 0.95  # Monthly decay
        self.learning_rate = 0.1
    
    async def learn(self, information: str, source: str, feedback: float = 0.0):
        """Learn from new information with feedback."""
        # Extract facts and entities
        facts = self._extract_facts(information)
        entities = self.knowledge_graph.extract_entities(information)
        
        for fact in facts:
            # Check if fact exists
            existing = await self.vector_memory.search(
                fact,
                limit=1,
                filter={"type": "fact"}
            )
            
            if existing and existing[0]["similarity"] > 0.95:
                # Update existing fact
                await self._update_fact(existing[0], feedback)
            else:
                # Add new fact
                await self._add_new_fact(fact, source, feedback)
        
        # Update knowledge graph
        await self.knowledge_graph.store(
            f"info_{datetime.now().timestamp()}",
            information
        )
        
        # Consolidate and prune periodically
        if await self._should_consolidate():
            await self.consolidate()
    
    async def _update_fact(self, existing_fact: Dict, feedback: float):
        """Update existing fact with feedback."""
        current_confidence = existing_fact["metadata"].get("confidence", 0.5)
        
        # Apply feedback with learning rate
        new_confidence = current_confidence + self.learning_rate * (
            feedback - current_confidence
        )
        
        # Apply time decay
        age_days = (
            datetime.now() - 
            datetime.fromisoformat(existing_fact["metadata"]["timestamp"])
        ).days
        decay_factor = self.confidence_decay ** (age_days / 30)
        new_confidence *= decay_factor
        
        # Update
        await self.vector_memory.store(
            key=existing_fact["id"],
            value=existing_fact["content"],
            metadata={
                **existing_fact["metadata"],
                "confidence": new_confidence,
                "last_updated": datetime.now().isoformat(),
                "update_count": existing_fact["metadata"].get("update_count", 0) + 1
            }
        )
    
    async def consolidate(self):
        """Consolidate knowledge base."""
        # Remove low-confidence facts
        all_facts = await self.vector_memory.search(
            "",
            limit=10000,
            filter={"type": "fact"}
        )
        
        for fact in all_facts:
            if fact["metadata"].get("confidence", 0) < 0.3:
                await self.vector_memory.delete(fact["id"])
        
        # Merge similar facts
        await self.vector_memory.consolidate_memories(
            similarity_threshold=0.95
        )
        
        # Prune orphaned entities in graph
        entities = await self.knowledge_graph.get_entities()
        for entity in entities:
            rels = await self.knowledge_graph.get_relationships(entity["name"])
            if not rels and entity["count"] < 2:
                # Remove rarely mentioned, unconnected entities
                self.knowledge_graph.entities.pop(entity["name"], None)
    
    def _extract_facts(self, text: str) -> List[str]:
        """Extract facts from text."""
        # Simple sentence splitting (use NLP in production)
        sentences = text.split(". ")
        facts = []
        
        for sentence in sentences:
            # Filter for factual statements
            if len(sentence.split()) > 3 and not sentence.endswith("?"):
                facts.append(sentence.strip())
        
        return facts
    
    async def _should_consolidate(self) -> bool:
        """Check if consolidation is needed."""
        stats = self.vector_memory.get_stats()
        return stats["total_memories"] > 1000
```

## Multi-Agent Memory Patterns

### Shared Knowledge Pool

```python
class SharedKnowledgePool:
    """Shared memory across multiple agents."""
    
    def __init__(self):
        # Shared vector memory
        self.shared_memory = ChromaDBMemory(
            collection_name="shared_knowledge",
            persist_directory="./memory/shared"
        )
        
        # Shared knowledge graph
        self.shared_graph = KnowledgeGraphMemory(capacity=100000)
        
        # Agent-specific memories
        self.agent_memories = {}
        
        # Access control
        self.permissions = {}
    
    async def register_agent(
        self,
        agent_id: str,
        permissions: List[str] = None
    ):
        """Register an agent with the shared pool."""
        # Create agent-specific memory
        self.agent_memories[agent_id] = ChromaDBMemory(
            collection_name=f"agent_{agent_id}",
            persist_directory=f"./memory/agents/{agent_id}"
        )
        
        # Set permissions
        self.permissions[agent_id] = permissions or ["read", "write"]
    
    async def share_knowledge(
        self,
        source_agent: str,
        content: str,
        visibility: str = "public",
        tags: List[str] = None
    ):
        """Share knowledge from an agent."""
        if "write" not in self.permissions.get(source_agent, []):
            raise PermissionError(f"Agent {source_agent} cannot write")
        
        # Store in shared memory
        knowledge_id = f"knowledge_{datetime.now().timestamp()}"
        
        await self.shared_memory.store(
            key=knowledge_id,
            value=content,
            metadata={
                "source_agent": source_agent,
                "visibility": visibility,
                "tags": tags or [],
                "timestamp": datetime.now().isoformat(),
                "access_count": 0
            }
        )
        
        # Update knowledge graph
        await self.shared_graph.store(knowledge_id, content)
        
        # Notify interested agents
        await self._notify_agents(source_agent, content, tags)
        
        return knowledge_id
    
    async def query_knowledge(
        self,
        agent_id: str,
        query: str,
        include_private: bool = True
    ) -> List[Dict]:
        """Query shared knowledge."""
        if "read" not in self.permissions.get(agent_id, []):
            raise PermissionError(f"Agent {agent_id} cannot read")
        
        # Build filter
        filter_dict = {}
        if not include_private:
            filter_dict["visibility"] = "public"
        
        # Search shared memory
        shared_results = await self.shared_memory.search(
            query=query,
            limit=10,
            filter=filter_dict
        )
        
        # Search agent's own memory
        if agent_id in self.agent_memories:
            own_results = await self.agent_memories[agent_id].search(
                query=query,
                limit=5
            )
            
            # Combine results
            all_results = shared_results + own_results
            
            # Sort by relevance
            all_results.sort(key=lambda x: x["similarity"], reverse=True)
            
            return all_results[:10]
        
        return shared_results
    
    async def _notify_agents(
        self,
        source_agent: str,
        content: str,
        tags: List[str]
    ):
        """Notify agents about new knowledge."""
        # In production, use actual notification system
        for agent_id in self.agent_memories:
            if agent_id != source_agent:
                # Check if agent is interested (by tags, etc.)
                # Store notification in agent's memory
                await self.agent_memories[agent_id].store(
                    key=f"notification_{datetime.now().timestamp()}",
                    value=f"New knowledge from {source_agent}: {content[:100]}...",
                    metadata={
                        "type": "notification",
                        "source": source_agent,
                        "tags": tags,
                        "timestamp": datetime.now().isoformat()
                    }
                )
```

### Collaborative Learning

```python
class CollaborativeLearning:
    """Agents learn together and share insights."""
    
    def __init__(self):
        self.shared_pool = SharedKnowledgePool()
        self.learning_sessions = {}
    
    async def start_learning_session(
        self,
        session_id: str,
        topic: str,
        participating_agents: List[str]
    ):
        """Start a collaborative learning session."""
        self.learning_sessions[session_id] = {
            "topic": topic,
            "agents": participating_agents,
            "insights": [],
            "consensus": {},
            "started_at": datetime.now()
        }
        
        # Notify agents
        for agent_id in participating_agents:
            await self.shared_pool.share_knowledge(
                agent_id,
                f"Learning session started: {topic}",
                visibility="group",
                tags=["learning_session", session_id]
            )
    
    async def contribute_insight(
        self,
        session_id: str,
        agent_id: str,
        insight: str,
        confidence: float = 0.8
    ):
        """Agent contributes an insight."""
        if session_id not in self.learning_sessions:
            raise ValueError("Invalid session")
        
        session = self.learning_sessions[session_id]
        if agent_id not in session["agents"]:
            raise ValueError("Agent not in session")
        
        # Store insight
        insight_data = {
            "agent_id": agent_id,
            "insight": insight,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        session["insights"].append(insight_data)
        
        # Share with group
        await self.shared_pool.share_knowledge(
            agent_id,
            insight,
            visibility="group",
            tags=["insight", session_id, session["topic"]]
        )
        
        # Check for consensus
        await self._check_consensus(session_id)
    
    async def _check_consensus(self, session_id: str):
        """Check if agents reach consensus."""
        session = self.learning_sessions[session_id]
        insights = session["insights"]
        
        if len(insights) < len(session["agents"]):
            return  # Not all agents contributed
        
        # Group similar insights
        insight_groups = {}
        for insight_data in insights:
            # Simple grouping by similarity
            matched = False
            for group_key, group in insight_groups.items():
                # In production, use semantic similarity
                if self._insights_similar(
                    insight_data["insight"],
                    group[0]["insight"]
                ):
                    group.append(insight_data)
                    matched = True
                    break
            
            if not matched:
                insight_groups[insight_data["insight"]] = [insight_data]
        
        # Find consensus
        for insight_text, group in insight_groups.items():
            if len(group) >= len(session["agents"]) * 0.6:  # 60% agreement
                avg_confidence = sum(
                    i["confidence"] for i in group
                ) / len(group)
                
                session["consensus"][insight_text] = {
                    "confidence": avg_confidence,
                    "support_count": len(group),
                    "supporting_agents": [i["agent_id"] for i in group]
                }
                
                # Store consensus as verified knowledge
                await self.shared_pool.share_knowledge(
                    "consensus",
                    f"Consensus reached: {insight_text}",
                    visibility="public",
                    tags=["consensus", session["topic"], "verified"]
                )
    
    def _insights_similar(self, insight1: str, insight2: str) -> bool:
        """Check if insights are similar."""
        # Simple word overlap (use embeddings in production)
        words1 = set(insight1.lower().split())
        words2 = set(insight2.lower().split())
        
        overlap = len(words1.intersection(words2))
        total = len(words1.union(words2))
        
        return overlap / total > 0.6 if total > 0 else False
```

## Performance Optimization Patterns

### Memory Hierarchies

```python
class HierarchicalMemory:
    """Multi-level memory hierarchy for performance."""
    
    def __init__(self):
        # L1: Hot cache (in-memory)
        self.l1_cache = {}
        self.l1_size = 100
        self.l1_hits = 0
        self.l1_misses = 0
        
        # L2: Warm cache (Redis)
        self.l2_cache = None  # Redis client
        self.l2_ttl = 3600  # 1 hour
        
        # L3: Cold storage (ChromaDB)
        self.l3_storage = ChromaDBMemory(
            collection_name="hierarchical_memory"
        )
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve with cache hierarchy."""
        # Check L1
        if key in self.l1_cache:
            self.l1_hits += 1
            self._promote_l1(key)
            return self.l1_cache[key]["value"]
        
        self.l1_misses += 1
        
        # Check L2
        if self.l2_cache:
            value = await self.l2_cache.get(key)
            if value:
                # Promote to L1
                await self._add_to_l1(key, value)
                return value
        
        # Check L3
        result = await self.l3_storage.retrieve(key)
        if result:
            # Promote to L2 and L1
            if self.l2_cache:
                await self.l2_cache.set(key, result, ex=self.l2_ttl)
            await self._add_to_l1(key, result)
            return result
        
        return None
    
    async def store(self, key: str, value: Any, metadata: Dict = None):
        """Store with write-through to all levels."""
        # Store in L3 (persistent)
        await self.l3_storage.store(key, value, metadata)
        
        # Store in L2
        if self.l2_cache:
            await self.l2_cache.set(key, value, ex=self.l2_ttl)
        
        # Store in L1
        await self._add_to_l1(key, value)
    
    async def search(self, query: str, **kwargs) -> List[Dict]:
        """Search with query caching."""
        # Check if query is cached
        query_key = f"query:{query}:{str(kwargs)}"
        
        cached = await self.retrieve(query_key)
        if cached:
            return cached
        
        # Perform search
        results = await self.l3_storage.search(query, **kwargs)
        
        # Cache results
        await self.store(query_key, results, {"type": "query_cache"})
        
        return results
    
    async def _add_to_l1(self, key: str, value: Any):
        """Add to L1 cache with LRU eviction."""
        if len(self.l1_cache) >= self.l1_size:
            # Evict least recently used
            lru_key = min(
                self.l1_cache.keys(),
                key=lambda k: self.l1_cache[k]["access_time"]
            )
            del self.l1_cache[lru_key]
        
        self.l1_cache[key] = {
            "value": value,
            "access_time": datetime.now()
        }
    
    def _promote_l1(self, key: str):
        """Update access time for LRU."""
        if key in self.l1_cache:
            self.l1_cache[key]["access_time"] = datetime.now()
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_requests = self.l1_hits + self.l1_misses
        hit_rate = self.l1_hits / total_requests if total_requests > 0 else 0
        
        return {
            "l1_size": len(self.l1_cache),
            "l1_hits": self.l1_hits,
            "l1_misses": self.l1_misses,
            "l1_hit_rate": hit_rate,
            "total_requests": total_requests
        }
```

### Batch Processing

```python
class BatchMemoryProcessor:
    """Efficient batch memory operations."""
    
    def __init__(self, memory: ChromaDBMemory):
        self.memory = memory
        self.batch_size = 100
        self.pending_stores = []
        self.pending_searches = []
    
    async def batch_store(
        self,
        items: List[Dict[str, Any]],
        progress_callback=None
    ):
        """Store items in batches."""
        total = len(items)
        
        for i in range(0, total, self.batch_size):
            batch = items[i:i + self.batch_size]
            
            # Prepare batch data
            ids = []
            documents = []
            metadatas = []
            
            for item in batch:
                ids.append(item["key"])
                documents.append(str(item["value"]))
                metadatas.append(item.get("metadata", {}))
            
            # Batch insert
            self.memory.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            # Progress callback
            if progress_callback:
                progress = (i + len(batch)) / total
                await progress_callback(progress)
    
    async def parallel_search(
        self,
        queries: List[str],
        max_concurrent: int = 10
    ) -> Dict[str, List[Dict]]:
        """Search multiple queries in parallel."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def search_with_limit(query: str):
            async with semaphore:
                return query, await self.memory.search(query)
        
        # Create tasks
        tasks = [search_with_limit(q) for q in queries]
        
        # Execute in parallel
        results = await asyncio.gather(*tasks)
        
        # Return as dictionary
        return dict(results)
```

## Real-World Use Cases

### Customer Support Memory

```python
class CustomerSupportMemory:
    """Memory system for customer support agents."""
    
    def __init__(self):
        self.ticket_memory = ChromaDBMemory(
            collection_name="support_tickets"
        )
        self.solution_memory = ChromaDBMemory(
            collection_name="support_solutions"
        )
        self.customer_graph = KnowledgeGraphMemory()
    
    async def log_ticket(
        self,
        ticket_id: str,
        customer_id: str,
        issue: str,
        category: str
    ):
        """Log a support ticket."""
        # Store ticket
        await self.ticket_memory.store(
            key=ticket_id,
            value=issue,
            metadata={
                "customer_id": customer_id,
                "category": category,
                "status": "open",
                "created_at": datetime.now().isoformat()
            }
        )
        
        # Update customer graph
        self.customer_graph.add_entity(customer_id, "CUSTOMER")
        self.customer_graph.add_entity(category, "ISSUE_CATEGORY")
        self.customer_graph.add_relationship(
            customer_id,
            "reported",
            category
        )
    
    async def find_similar_issues(
        self,
        issue_description: str,
        limit: int = 5
    ) -> List[Dict]:
        """Find similar past issues and solutions."""
        # Search tickets
        similar_tickets = await self.ticket_memory.search(
            query=issue_description,
            limit=limit,
            filter={"status": "resolved"}
        )
        
        # Get solutions for similar tickets
        solutions = []
        for ticket in similar_tickets:
            ticket_id = ticket["id"]
            
            # Search for solution
            solution_results = await self.solution_memory.search(
                query=ticket_id,
                limit=1
            )
            
            if solution_results:
                solutions.append({
                    "ticket": ticket,
                    "solution": solution_results[0],
                    "similarity": ticket["similarity"]
                })
        
        return solutions
    
    async def store_solution(
        self,
        ticket_id: str,
        solution: str,
        resolved_by: str
    ):
        """Store a solution for a ticket."""
        # Get original ticket
        ticket = await self.ticket_memory.retrieve(ticket_id)
        
        if ticket:
            # Store solution
            await self.solution_memory.store(
                key=f"solution_{ticket_id}",
                value=solution,
                metadata={
                    "ticket_id": ticket_id,
                    "resolved_by": resolved_by,
                    "resolved_at": datetime.now().isoformat(),
                    "category": ticket["metadata"]["category"]
                }
            )
            
            # Update ticket status
            await self.ticket_memory.store(
                key=ticket_id,
                value=ticket["content"],
                metadata={
                    **ticket["metadata"],
                    "status": "resolved",
                    "resolved_at": datetime.now().isoformat()
                }
            )
            
            # Update success metrics
            await self._update_resolution_metrics(
                resolved_by,
                ticket["metadata"]["category"]
            )
    
    async def _update_resolution_metrics(
        self,
        agent_id: str,
        category: str
    ):
        """Track resolution success."""
        self.customer_graph.add_entity(agent_id, "SUPPORT_AGENT")
        self.customer_graph.add_relationship(
            agent_id,
            "resolved",
            category,
            attributes={"count": 1}  # Increment in real implementation
        )
```

## Best Practices Summary

### 1. Memory Lifecycle

```python
# Always implement cleanup
async def cleanup_old_memories(memory: BaseMemory, days: int = 30):
    """Remove old memories."""
    cutoff = datetime.now() - timedelta(days=days)
    # Implementation depends on memory type
```

### 2. Error Handling

```python
# Graceful degradation
async def safe_retrieve(memory: BaseMemory, key: str, default=None):
    """Retrieve with fallback."""
    try:
        return await memory.retrieve(key)
    except Exception as e:
        logger.warning(f"Memory retrieval failed: {e}")
        return default
```

### 3. Monitoring

```python
# Track memory health
def monitor_memory_health(memory: BaseMemory) -> Dict:
    """Monitor memory system health."""
    stats = memory.get_stats()
    
    health = {
        "status": "healthy",
        "warnings": [],
        "metrics": stats
    }
    
    # Check thresholds
    if stats["total_memories"] > 100000:
        health["warnings"].append("High memory count")
    
    if stats.get("query_latency_ms", 0) > 100:
        health["warnings"].append("High query latency")
        health["status"] = "degraded"
    
    return health
```

## Next Steps

- [Memory Overview](README.md) - Memory system concepts
- [Vector Memory Guide](vector-memory.md) - ChromaDB details
- [Knowledge Graph Guide](knowledge-graph.md) - Graph operations
- [API Reference](api-reference.md) - Complete API docs
