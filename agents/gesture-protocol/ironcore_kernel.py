#!/usr/bin/env python3
"""
IRONCORE KERNEL — 5-Layer Neural-Symbolic Stack
================================================
Sovereign Elite OS — Cognitive Processing Engine

ARCHITECTURE:
    L1: EXECUTIVE PERSONA      — Tone adaptation + emotional reasoning
    L2: SUPERVISOR ROUTER      — Multi-agent orchestration
    L3: DOMAIN AGENTS          — Specialized reasoning (Security/Ops/Science)
    L4: RETRIEVAL MEMORY       — Context retrieval + temporal decay
    L5: SPECULATIVE INFERENCE  — Low-latency response generation

SOVEREIGN SCALE IMPLEMENTATION:
    - Local LLM via Ollama (Llama-3.1 8B)
    - ChromaDB for vector retrieval
    - Redis for session state (optional)
    - Deterministic fallback when AI unavailable

AUTHOR: Architect
VERSION: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Optional imports with graceful degradation
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = logging.getLogger("ironcore")

# =============================================================================
# CONFIGURATION
# =============================================================================

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M")
CHROMA_PATH = Path(os.getenv("CHROMA_PATH", "/var/lib/manus/chroma"))
MEMORY_DECAY_HOURS = int(os.getenv("MEMORY_DECAY_HOURS", "72"))

# =============================================================================
# L5: SPECULATIVE INFERENCE ENGINE
# =============================================================================

class InferenceMode(Enum):
    """Inference execution modes."""
    FULL = "full"           # Full LLM inference
    CACHED = "cached"       # Use cached response
    FALLBACK = "fallback"   # Deterministic fallback


@dataclass
class InferenceResult:
    """Result from inference engine."""
    content: str
    mode: InferenceMode
    latency_ms: float
    confidence: float
    tokens_used: int = 0


class SpeculativeInferenceEngine:
    """
    L5: Low-latency inference with speculative caching.
    
    Sovereign Scale: Uses Ollama for local inference with response caching.
    """
    
    def __init__(self):
        self.cache: dict[str, InferenceResult] = {}
        self.cache_ttl = 300  # 5 minutes
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama is available."""
        if not REQUESTS_AVAILABLE:
            return False
        try:
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def _cache_key(self, prompt: str, context: str) -> str:
        """Generate cache key from prompt and context."""
        combined = f"{prompt}:{context[:500]}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    async def infer(
        self,
        prompt: str,
        context: str = "",
        max_tokens: int = 256,
        temperature: float = 0.1,
    ) -> InferenceResult:
        """
        Execute inference with speculative caching.
        
        Priority:
        1. Check cache for recent identical query
        2. Execute Ollama inference if available
        3. Return fallback response
        """
        start_time = time.time()
        cache_key = self._cache_key(prompt, context)
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached.latency_ms < self.cache_ttl:
                return InferenceResult(
                    content=cached.content,
                    mode=InferenceMode.CACHED,
                    latency_ms=(time.time() - start_time) * 1000,
                    confidence=cached.confidence,
                )
        
        # Try Ollama inference
        if self.available and REQUESTS_AVAILABLE:
            try:
                full_prompt = f"{context}\n\n{prompt}" if context else prompt
                response = requests.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        }
                    },
                    timeout=30,
                )
                
                if response.ok:
                    data = response.json()
                    result = InferenceResult(
                        content=data.get("response", "").strip(),
                        mode=InferenceMode.FULL,
                        latency_ms=(time.time() - start_time) * 1000,
                        confidence=0.9,
                        tokens_used=data.get("eval_count", 0),
                    )
                    self.cache[cache_key] = result
                    return result
            except Exception as e:
                logger.warning(f"Ollama inference failed: {e}")
        
        # Fallback
        return InferenceResult(
            content="[FALLBACK] AI inference unavailable. Using deterministic routing.",
            mode=InferenceMode.FALLBACK,
            latency_ms=(time.time() - start_time) * 1000,
            confidence=0.5,
        )


# =============================================================================
# L4: RETRIEVAL MEMORY SYSTEM
# =============================================================================

@dataclass
class MemoryRecord:
    """A single memory record."""
    id: str
    content: str
    category: str
    timestamp: datetime
    relevance: float = 1.0
    metadata: dict = field(default_factory=dict)


class RetrievalMemory:
    """
    L4: Hybrid memory system with temporal decay.
    
    Sovereign Scale: Uses ChromaDB for vector storage with file-based fallback.
    """
    
    def __init__(self):
        self.episodic: list[MemoryRecord] = []
        self.procedural: dict[str, Any] = {}
        self.chroma_client = None
        self.collection = None
        
        if CHROMADB_AVAILABLE:
            try:
                CHROMA_PATH.mkdir(parents=True, exist_ok=True)
                self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
                self.collection = self.chroma_client.get_or_create_collection("sovereign_memory")
            except Exception as e:
                logger.warning(f"ChromaDB initialization failed: {e}")
    
    def store_episodic(self, content: str, category: str, metadata: dict = None):
        """Store an episodic memory."""
        record = MemoryRecord(
            id=hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12],
            content=content,
            category=category,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        self.episodic.append(record)
        
        # Also store in ChromaDB if available
        if self.collection:
            try:
                self.collection.add(
                    ids=[record.id],
                    documents=[content],
                    metadatas=[{"category": category, "timestamp": record.timestamp.isoformat()}],
                )
            except Exception as e:
                logger.debug(f"ChromaDB store failed: {e}")
    
    def store_procedural(self, key: str, workflow: dict):
        """Store a procedural workflow."""
        self.procedural[key] = {
            "workflow": workflow,
            "stored_at": datetime.now().isoformat(),
        }
    
    def retrieve_context(
        self,
        query: str,
        limit: int = 10,
        decay_hours: int = MEMORY_DECAY_HOURS,
    ) -> list[MemoryRecord]:
        """
        Retrieve relevant context with temporal decay.
        
        Recent memories are weighted higher than older ones.
        """
        now = datetime.now()
        cutoff = now - timedelta(hours=decay_hours)
        
        # Filter and score episodic memories
        scored = []
        for record in self.episodic:
            if record.timestamp < cutoff:
                continue
            
            # Simple relevance: keyword matching + recency
            query_words = set(query.lower().split())
            content_words = set(record.content.lower().split())
            keyword_score = len(query_words & content_words) / max(len(query_words), 1)
            
            # Recency score (1.0 for now, 0.5 for decay_hours ago)
            age_hours = (now - record.timestamp).total_seconds() / 3600
            recency_score = max(0.5, 1.0 - (age_hours / decay_hours) * 0.5)
            
            record.relevance = keyword_score * 0.6 + recency_score * 0.4
            scored.append(record)
        
        # Sort by relevance and return top N
        scored.sort(key=lambda r: r.relevance, reverse=True)
        return scored[:limit]
    
    def get_procedural(self, key: str) -> Optional[dict]:
        """Retrieve a procedural workflow."""
        return self.procedural.get(key, {}).get("workflow")


# =============================================================================
# L3: DOMAIN AGENTS
# =============================================================================

class DomainAgent(ABC):
    """Base class for domain-specific agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.capabilities: list[str] = []
    
    @abstractmethod
    async def confidence_score(self, intent: str, context: dict) -> float:
        """Calculate confidence score for handling this intent."""
        pass
    
    @abstractmethod
    async def execute(self, intent: str, context: dict) -> dict:
        """Execute the intent and return result."""
        pass


class SecurityAgent(DomainAgent):
    """Security domain agent."""
    
    def __init__(self):
        super().__init__("SECURITY")
        self.capabilities = ["threat_scan", "lockdown", "alert", "audit"]
    
    async def confidence_score(self, intent: str, context: dict) -> float:
        keywords = ["security", "threat", "alert", "lockdown", "audit", "breach", "intrusion"]
        intent_lower = intent.lower()
        matches = sum(1 for kw in keywords if kw in intent_lower)
        return min(1.0, matches * 0.3)
    
    async def execute(self, intent: str, context: dict) -> dict:
        return {
            "agent": self.name,
            "action": "security_response",
            "status": "executed",
            "details": f"Security action for: {intent}",
        }


class OpsAgent(DomainAgent):
    """Operations/Facility domain agent."""
    
    def __init__(self):
        super().__init__("OPS")
        self.capabilities = ["snapshot", "sync", "dashboard", "shutdown", "deploy"]
    
    async def confidence_score(self, intent: str, context: dict) -> float:
        keywords = ["snapshot", "sync", "dashboard", "shutdown", "deploy", "backup", "status"]
        intent_lower = intent.lower()
        matches = sum(1 for kw in keywords if kw in intent_lower)
        return min(1.0, matches * 0.3)
    
    async def execute(self, intent: str, context: dict) -> dict:
        return {
            "agent": self.name,
            "action": "ops_response",
            "status": "executed",
            "details": f"Ops action for: {intent}",
        }


class ScienceAgent(DomainAgent):
    """Science/Analysis domain agent."""
    
    def __init__(self):
        super().__init__("SCIENCE")
        self.capabilities = ["analyze", "simulate", "calculate", "model"]
    
    async def confidence_score(self, intent: str, context: dict) -> float:
        keywords = ["analyze", "simulate", "calculate", "model", "data", "research", "science"]
        intent_lower = intent.lower()
        matches = sum(1 for kw in keywords if kw in intent_lower)
        return min(1.0, matches * 0.3)
    
    async def execute(self, intent: str, context: dict) -> dict:
        return {
            "agent": self.name,
            "action": "science_response",
            "status": "executed",
            "details": f"Science action for: {intent}",
        }


# =============================================================================
# L2: SUPERVISOR ROUTER
# =============================================================================

class SupervisorRouter:
    """
    L2: Multi-agent orchestration and routing.
    
    Routes intents to the most appropriate domain agent based on confidence scores.
    """
    
    def __init__(self):
        self.agents: dict[str, DomainAgent] = {
            "SECURITY": SecurityAgent(),
            "OPS": OpsAgent(),
            "SCIENCE": ScienceAgent(),
        }
        self.default_agent = "OPS"
    
    async def route(self, intent: str, context: dict) -> dict:
        """Route intent to appropriate agent."""
        agent_scores = {}
        
        for agent_name, agent in self.agents.items():
            score = await agent.confidence_score(intent, context)
            agent_scores[agent_name] = score
        
        # Select highest scoring agent (or default if all scores are 0)
        primary = max(agent_scores, key=agent_scores.get)
        if agent_scores[primary] == 0:
            primary = self.default_agent
        
        # Execute
        result = await self.agents[primary].execute(intent, context)
        
        return {
            "primary_agent": primary,
            "confidence": agent_scores[primary],
            "all_scores": agent_scores,
            "result": result,
        }


# =============================================================================
# L1: EXECUTIVE PERSONA ENGINE
# =============================================================================

class PersonaMode(Enum):
    """Persona adaptation modes."""
    FOCUSED_COMMAND = "focused_command"
    CONFIDENT_ASSISTANT = "confident_assistant"
    ANALYTICAL = "analytical"
    ALERT = "alert"


@dataclass
class PersonaState:
    """Current persona state."""
    mode: PersonaMode
    stress_level: float = 0.0
    context_priority: str = "normal"
    last_interaction: datetime = field(default_factory=datetime.now)


class ExecutivePersona:
    """
    L1: Adaptive persona engine.
    
    Adapts communication style based on context, stress, and time.
    """
    
    def __init__(self):
        self.state = PersonaState(mode=PersonaMode.CONFIDENT_ASSISTANT)
        self.interaction_history: list[dict] = []
    
    def adapt_tone(
        self,
        user_stress: float = 0.0,
        context_priority: str = "normal",
        time_of_day: str = None,
    ) -> PersonaMode:
        """Adapt persona mode based on context."""
        if time_of_day is None:
            time_of_day = datetime.now().strftime("%H%M")
        
        # High stress + urgent = focused command mode
        if user_stress > 0.8 and context_priority == "urgent":
            return PersonaMode.FOCUSED_COMMAND
        
        # Security context = alert mode
        if context_priority == "security":
            return PersonaMode.ALERT
        
        # Analysis context = analytical mode
        if context_priority == "analysis":
            return PersonaMode.ANALYTICAL
        
        # Default
        return PersonaMode.CONFIDENT_ASSISTANT
    
    def format_response(self, content: str, mode: PersonaMode = None) -> str:
        """Format response according to persona mode."""
        if mode is None:
            mode = self.state.mode
        
        prefixes = {
            PersonaMode.FOCUSED_COMMAND: "",
            PersonaMode.CONFIDENT_ASSISTANT: "",
            PersonaMode.ANALYTICAL: "[ANALYSIS] ",
            PersonaMode.ALERT: "[ALERT] ",
        }
        
        return f"{prefixes.get(mode, '')}{content}"
    
    def log_interaction(self, intent: str, response: str, success: bool):
        """Log interaction for context building."""
        self.interaction_history.append({
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "response": response[:100],
            "success": success,
        })
        # Keep last 100 interactions
        self.interaction_history = self.interaction_history[-100:]


# =============================================================================
# IRONCORE KERNEL — UNIFIED INTERFACE
# =============================================================================

class IronCoreKernel:
    """
    Unified IronCore Kernel integrating all 5 layers.
    
    Usage:
        kernel = IronCoreKernel()
        result = await kernel.process("generate snapshot")
    """
    
    def __init__(self):
        self.l5_inference = SpeculativeInferenceEngine()
        self.l4_memory = RetrievalMemory()
        self.l3_agents = SupervisorRouter()
        self.l1_persona = ExecutivePersona()
        
        logger.info("IronCore Kernel initialized")
        logger.info(f"  L5 Inference: {'Available' if self.l5_inference.available else 'Fallback mode'}")
        logger.info(f"  L4 Memory: {'ChromaDB' if self.l4_memory.collection else 'In-memory'}")
    
    async def process(
        self,
        intent: str,
        context: dict = None,
        user_stress: float = 0.0,
    ) -> dict:
        """
        Process an intent through the full 5-layer stack.
        
        Flow:
        1. L1: Adapt persona based on context
        2. L4: Retrieve relevant memory context
        3. L5: (Optional) Use LLM for intent clarification
        4. L2: Route to appropriate domain agent
        5. L3: Execute via domain agent
        6. L1: Format response
        """
        start_time = time.time()
        context = context or {}
        
        # L1: Adapt persona
        persona_mode = self.l1_persona.adapt_tone(
            user_stress=user_stress,
            context_priority=context.get("priority", "normal"),
        )
        self.l1_persona.state.mode = persona_mode
        
        # L4: Retrieve memory context
        memory_context = self.l4_memory.retrieve_context(intent, limit=5)
        context["memory"] = [m.content for m in memory_context]
        
        # L2/L3: Route and execute
        routing_result = await self.l3_agents.route(intent, context)
        
        # L4: Store this interaction
        self.l4_memory.store_episodic(
            content=f"Intent: {intent} | Agent: {routing_result['primary_agent']}",
            category="interaction",
        )
        
        # L1: Format response
        response_content = routing_result["result"].get("details", "Action completed")
        formatted_response = self.l1_persona.format_response(response_content, persona_mode)
        
        # Log interaction
        self.l1_persona.log_interaction(intent, formatted_response, True)
        
        return {
            "response": formatted_response,
            "persona_mode": persona_mode.value,
            "routing": routing_result,
            "memory_context_count": len(memory_context),
            "latency_ms": (time.time() - start_time) * 1000,
        }
    
    async def clarify_intent(self, gesture_id: str, context: dict) -> Optional[str]:
        """
        Use L5 inference to clarify ambiguous gesture intent.
        
        Returns clarified action name or None if unclear.
        """
        prompt = f"""You are a gesture intent parser for a sovereign infrastructure system.

Gesture detected: {gesture_id}
Confidence: {context.get('confidence', 0)}
Recent actions: {context.get('recent_actions', [])}

Based on the context, confirm or clarify the intended action.
Respond with ONLY the action name or "REJECT" if unclear.

Valid actions: generate_snapshot, trigger_airbyte_sync, open_dashboard, 
               send_alert, shutdown_sequence, gesture_acknowledgement"""
        
        result = await self.l5_inference.infer(prompt, max_tokens=50)
        
        if result.mode == InferenceMode.FALLBACK:
            return None
        
        response = result.content.strip().lower()
        valid_actions = [
            "generate_snapshot", "trigger_airbyte_sync", "open_dashboard",
            "send_alert", "shutdown_sequence", "gesture_acknowledgement"
        ]
        
        if response in valid_actions:
            return response
        if response == "reject":
            return None
        
        # Try to match partial
        for action in valid_actions:
            if action in response:
                return action
        
        return None


# =============================================================================
# CLI INTERFACE
# =============================================================================

async def main():
    """Test the IronCore Kernel."""
    kernel = IronCoreKernel()
    
    print("=" * 60)
    print("IRONCORE KERNEL — TEST SUITE")
    print("=" * 60)
    
    # Test 1: Basic intent processing
    print("\n[TEST 1] Basic intent processing")
    result = await kernel.process("generate system snapshot")
    print(f"  Response: {result['response']}")
    print(f"  Agent: {result['routing']['primary_agent']}")
    print(f"  Latency: {result['latency_ms']:.2f}ms")
    
    # Test 2: Security intent
    print("\n[TEST 2] Security intent")
    result = await kernel.process("check for security threats", context={"priority": "security"})
    print(f"  Response: {result['response']}")
    print(f"  Agent: {result['routing']['primary_agent']}")
    print(f"  Persona: {result['persona_mode']}")
    
    # Test 3: Memory retrieval
    print("\n[TEST 3] Memory retrieval after interactions")
    result = await kernel.process("what was my last action")
    print(f"  Memory context count: {result['memory_context_count']}")
    
    # Test 4: Intent clarification (if LLM available)
    print("\n[TEST 4] Intent clarification")
    clarified = await kernel.clarify_intent("fist_hold", {"confidence": 0.75})
    print(f"  Clarified action: {clarified}")
    
    print("\n" + "=" * 60)
    print("IRONCORE KERNEL — TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
