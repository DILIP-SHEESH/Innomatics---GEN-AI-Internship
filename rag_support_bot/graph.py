"""
graph.py
--------
LangGraph Workflow Orchestration

This is the BRAIN of the system. It defines the stateful graph that
controls how every user query flows through the system.

Graph Architecture:
─────────────────────────────────────────────────────
                    [START]
                       │
                       ▼
              ┌─────────────────┐
              │  input_node     │  ← Receive query, detect intent
              └────────┬────────┘
                       │
           ┌───────────▼───────────┐
           │  conditional_router   │  ← Route based on intent + confidence
           └───┬───────────────┬───┘
               │               │
    (normal)   │               │   (escalate)
               ▼               ▼
     ┌──────────────┐  ┌──────────────┐
     │  rag_node    │  │  hitl_node   │
     │  (retrieve + │  │  (escalate   │
     │   generate)  │  │   to human)  │
     └──────┬───────┘  └──────┬───────┘
            │                  │
            └────────┬─────────┘
                     ▼
            ┌─────────────────┐
            │  output_node    │  ← Format final response
            └────────┬────────┘
                     │
                   [END]
─────────────────────────────────────────────────────

State flows between nodes as a typed dict (GraphState).
"""

import os
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

from retriever import get_retriever
from config import CONFIDENCE_THRESHOLD, ESCALATION_KEYWORDS, GROQ_API_KEY


# ── State Definition ───────────────────────────────────────────────────────────

class GraphState(TypedDict):
    """
    The state object that flows between every node in the graph.
    Each node reads from and writes to this shared state.

    Fields:
    - query        : Original user question
    - intent       : Detected intent category
    - chunks       : Retrieved knowledge base chunks
    - confidence   : "HIGH" | "MEDIUM" | "LOW"
    - route        : "rag" | "escalate"
    - llm_response : Generated answer from LLM
    - final_answer : What gets shown to the user
    - escalated    : Whether HITL was triggered
    - escalation_reason : Why it was escalated
    - human_response : Human agent's reply (if provided)
    - sources      : List of page references for transparency
    """
    query            : str
    intent           : str
    chunks           : list
    confidence       : str
    route            : str
    llm_response     : str
    final_answer     : str
    escalated        : bool
    escalation_reason: str
    human_response   : str
    sources          : list


# ── LLM Setup ─────────────────────────────────────────────────────────────────

def get_llm_response(prompt: str) -> str:
    """
    Call Groq LLM API. Falls back to a template response if no API key.
    This makes the system runnable without an API key for demo purposes.
    """
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        # Demo mode: simulate LLM using retrieved context
        return _demo_llm_response(prompt)

    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[LLM Error: {str(e)}] Based on our knowledge base: {_extract_key_info(prompt)}"


def _extract_key_info(prompt: str) -> str:
    """Extract the context section from the prompt for demo fallback."""
    if "KNOWLEDGE BASE CONTEXT:" in prompt and "CUSTOMER QUERY:" in prompt:
        start = prompt.find("KNOWLEDGE BASE CONTEXT:") + len("KNOWLEDGE BASE CONTEXT:")
        end   = prompt.find("CUSTOMER QUERY:")
        context = prompt[start:end].strip()
        # Return first 300 chars of context as the "answer"
        return context[:300] + "..." if len(context) > 300 else context
    return "Please refer to our support documentation."


def _demo_llm_response(prompt: str) -> str:
    """
    Simulated LLM: extracts the most relevant sentence from context.
    Used when no Groq API key is set.
    """
    context = _extract_key_info(prompt)
    query_line = ""
    if "CUSTOMER QUERY:" in prompt:
        query_line = prompt.split("CUSTOMER QUERY:")[-1].strip()

    return (
        f"Based on our ShopEasy support documentation:\n\n"
        f"{context}\n\n"
        f"[Note: This is a demo response. Add your GROQ_API_KEY in .env for full AI responses.]"
    )


def build_prompt(query: str, context: str) -> str:
    """
    Construct the RAG prompt.

    Prompt design principles:
    - Give the LLM a clear role (customer support agent)
    - Provide context BEFORE the question (priming)
    - Instruct it to stay grounded in context (reduces hallucination)
    - Ask for concise, actionable answers
    """
    return f"""You are a helpful and professional customer support agent for ShopEasy, an e-commerce platform.
Answer the customer's question using ONLY the information provided in the knowledge base context below.
If the context doesn't contain enough information, say so honestly and suggest contacting support.
Be concise, friendly, and actionable. Use bullet points where helpful.

KNOWLEDGE BASE CONTEXT:
{context}

CUSTOMER QUERY:
{query}

YOUR RESPONSE:"""


# ── Graph Nodes ────────────────────────────────────────────────────────────────

def input_node(state: GraphState) -> GraphState:
    """
    Node 1: Input Processing
    - Receives the raw user query
    - Detects query intent category
    - Returns updated state
    """
    query  = state["query"].strip()
    intent = detect_intent(query)

    print(f"\n📥 [INPUT NODE]")
    print(f"   Query : {query}")
    print(f"   Intent: {intent}")

    return {**state, "query": query, "intent": intent}


def detect_intent(query: str) -> str:
    """
    Rule-based intent classifier.

    Categories:
    - order_tracking   : asking about order status
    - payment_issue    : billing, charges, refunds
    - returns          : returns, exchanges
    - account          : login, password, security
    - product          : product info, authenticity
    - shipping         : delivery, address
    - escalation       : fraud, legal, complex disputes
    - general          : anything else
    """
    q = query.lower()

    # Check escalation keywords first
    if any(kw in q for kw in [k.lower() for k in ESCALATION_KEYWORDS]):
        return "escalation"

    if any(w in q for w in ["track", "order", "delivered", "shipment", "dispatch"]):
        return "order_tracking"
    if any(w in q for w in ["charged", "payment", "refund", "invoice", "bill", "emi", "money"]):
        return "payment_issue"
    if any(w in q for w in ["return", "exchange", "replace", "wrong product"]):
        return "returns"
    if any(w in q for w in ["account", "password", "login", "email", "phone", "delete"]):
        return "account"
    if any(w in q for w in ["product", "review", "authentic", "seller", "fake"]):
        return "product"
    if any(w in q for w in ["deliver", "shipping", "address", "pin code", "international"]):
        return "shipping"

    return "general"


def rag_node(state: GraphState) -> GraphState:
    """
    Node 2: RAG Processing
    - Embeds the query
    - Retrieves top-K relevant chunks from ChromaDB
    - Builds prompt with retrieved context
    - Calls LLM to generate answer
    """
    print(f"\n🔍 [RAG NODE]")

    retriever = get_retriever()
    chunks, confidence = retriever.retrieve_with_confidence(state["query"])

    print(f"   Retrieved {len(chunks)} chunks | Confidence: {confidence}")
    if chunks:
        print(f"   Top score: {chunks[0]['score']:.3f}")

    context  = retriever.format_context(chunks)
    prompt   = build_prompt(state["query"], context)
    response = get_llm_response(prompt)

    sources = [f"Page {c['page']} (relevance: {c['score']:.2f})" for c in chunks]

    print(f"   ✅ Response generated ({len(response)} chars)")

    return {
        **state,
        "chunks"      : chunks,
        "confidence"  : confidence,
        "llm_response": response,
        "sources"     : sources,
        "escalated"   : False
    }


def hitl_node(state: GraphState) -> GraphState:
    """
    Node 3: Human-in-the-Loop Escalation
    - Triggered when: low confidence OR escalation intent
    - Logs the query to the escalation queue
    - Returns a holding response to the user
    - In production: creates a ticket, notifies human agent

    HITL Design:
    - The bot acknowledges the issue immediately
    - Human reviews asynchronously
    - Human response is injected back when available
    """
    print(f"\n🚨 [HITL NODE] — Escalating to human agent")
    print(f"   Reason: {state.get('escalation_reason', 'unspecified')}")

    # Log the escalation (in production: write to DB, send Slack alert, etc.)
    _log_escalation(state)

    holding_response = (
        f"Thank you for reaching out to ShopEasy Support. 🙏\n\n"
        f"I've reviewed your query and it requires attention from one of our "
        f"specialist agents to ensure you get the best resolution.\n\n"
        f"**What happens next:**\n"
        f"• Your case has been escalated (Ticket #{_generate_ticket_id(state['query'])})\n"
        f"• A senior support agent will contact you within **2–4 hours**\n"
        f"• You'll receive updates via email and SMS\n\n"
        f"For urgent issues, you can also call us at **1800-XXX-XXXX** "
        f"(Mon–Sat, 9AM–6PM).\n\n"
        f"We apologize for any inconvenience and appreciate your patience."
    )

    return {
        **state,
        "llm_response"     : holding_response,
        "escalated"        : True,
        "human_response"   : "",   # Filled later by human agent
        "chunks"           : [],
        "sources"          : []
    }


def output_node(state: GraphState) -> GraphState:
    """
    Node 4: Output Formatting
    - Takes the LLM/HITL response
    - Formats it with metadata (sources, escalation status)
    - Produces the final_answer shown to the user
    """
    print(f"\n📤 [OUTPUT NODE]")

    answer = state["llm_response"]

    # Append source attribution if we have retrieved chunks
    if state.get("sources") and not state.get("escalated"):
        sources_str = "\n".join(f"  • {s}" for s in state["sources"][:3])
        answer += f"\n\n📚 *Sources: {sources_str}*"

    print(f"   ✅ Final answer ready")

    return {**state, "final_answer": answer}


# ── Routing Logic ─────────────────────────────────────────────────────────────

def route_query(state: GraphState) -> Literal["rag_node", "hitl_node"]:
    """
    Conditional edge: decides whether to answer via RAG or escalate to human.

    Escalation triggers:
    1. Intent is explicitly "escalation" (fraud, hacked, legal, etc.)
    2. Confidence is LOW (retrieval score < CONFIDENCE_THRESHOLD)

    This is THE key decision point in the workflow.
    """
    intent     = state.get("intent", "general")
    query      = state.get("query", "").lower()

    # Hard escalation: security/fraud/legal intent
    if intent == "escalation":
        state["escalation_reason"] = f"High-risk intent detected: {intent}"
        state["route"] = "escalate"
        print(f"\n🔀 [ROUTER] → HITL (reason: escalation intent)")
        return "hitl_node"

    # Soft escalation: check retrieval confidence
    # We do a quick retrieval here just for routing (no extra cost — cached)
    retriever = get_retriever()
    _, confidence = retriever.retrieve_with_confidence(query)

    if confidence == "LOW":
        state["escalation_reason"] = f"Low retrieval confidence for query"
        state["route"] = "escalate"
        print(f"\n🔀 [ROUTER] → HITL (reason: low confidence)")
        return "hitl_node"

    state["route"] = "rag"
    print(f"\n🔀 [ROUTER] → RAG (confidence: {confidence})")
    return "rag_node"


# ── Helper Functions ───────────────────────────────────────────────────────────

def _generate_ticket_id(query: str) -> str:
    """Generate a deterministic ticket ID from query hash."""
    import hashlib
    h = hashlib.md5(query.encode()).hexdigest()[:6].upper()
    return f"SE-{h}"


def _log_escalation(state: GraphState):
    """Log escalated query to file (simulates writing to ticket system)."""
    import json
    from datetime import datetime

    os.makedirs("logs", exist_ok=True)
    log_entry = {
        "timestamp"         : datetime.now().isoformat(),
        "ticket_id"         : _generate_ticket_id(state["query"]),
        "query"             : state["query"],
        "intent"            : state.get("intent", ""),
        "escalation_reason" : state.get("escalation_reason", ""),
        "confidence"        : state.get("confidence", "")
    }
    with open("logs/escalations.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    print(f"   📝 Escalation logged: logs/escalations.jsonl")


# ── Build the Graph ────────────────────────────────────────────────────────────

def build_graph():
    """
    Assembles the LangGraph StateGraph.

    Graph structure:
    - 4 nodes: input_node, rag_node, hitl_node, output_node
    - 1 conditional edge: input_node → [rag_node OR hitl_node]
    - 2 regular edges: rag_node → output_node, hitl_node → output_node
    - entry point: input_node
    - finish point: output_node → END
    """
    graph = StateGraph(GraphState)

    # Register nodes
    graph.add_node("input_node",  input_node)
    graph.add_node("rag_node",    rag_node)
    graph.add_node("hitl_node",   hitl_node)
    graph.add_node("output_node", output_node)

    # Entry point
    graph.set_entry_point("input_node")

    # Conditional routing: input → rag OR hitl
    graph.add_conditional_edges(
        "input_node",
        route_query,
        {
            "rag_node" : "rag_node",
            "hitl_node": "hitl_node"
        }
    )

    # Both paths converge at output_node
    graph.add_edge("rag_node",  "output_node")
    graph.add_edge("hitl_node", "output_node")

    # Output → END
    graph.add_edge("output_node", END)

    return graph.compile()


# ── Singleton ─────────────────────────────────────────────────────────────────
_graph = None

def get_graph():
    """Returns the compiled graph (lazy init, reused)."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_query(query: str) -> dict:
    """
    Main entry point for processing a single user query through the graph.

    Returns the final GraphState with answer, metadata, and escalation info.
    """
    graph = get_graph()

    initial_state: GraphState = {
        "query"            : query,
        "intent"           : "",
        "chunks"           : [],
        "confidence"       : "",
        "route"            : "",
        "llm_response"     : "",
        "final_answer"     : "",
        "escalated"        : False,
        "escalation_reason": "",
        "human_response"   : "",
        "sources"          : []
    }

    result = graph.invoke(initial_state)
    return result


if __name__ == "__main__":
    test_queries = [
        "How do I track my order?",
        "I was charged twice for my order, what should I do?",
        "My account was hacked and I see unauthorized orders!",
        "What is your return policy for electronics?",
        "Do you deliver to international locations?",
    ]

    print("\n" + "="*60)
    print("  LANGGRAPH RAG SYSTEM — TEST RUN")
    print("="*60)

    for q in test_queries:
        print(f"\n{'─'*60}")
        result = run_query(q)
        print(f"\n💬 QUERY    : {result['query']}")
        print(f"🎯 INTENT   : {result['intent']}")
        print(f"📊 ROUTE    : {result['route']}")
        print(f"🚨 ESCALATED: {result['escalated']}")
        print(f"\n✅ ANSWER:\n{result['final_answer'][:300]}...")