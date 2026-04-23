"""
main.py
-------
CLI Entry Point for ShopEasy RAG Support Bot

Run: python main.py

Features:
- Interactive chat loop
- Shows routing decisions and confidence
- Displays escalation status
- Maintains conversation history display
"""

import os
import sys
from datetime import datetime
from ingest import run_ingestion
from graph import run_query


BANNER = """
╔══════════════════════════════════════════════════════╗
║         ShopEasy AI Customer Support Bot             ║
║         Powered by RAG + LangGraph + HITL            ║
╚══════════════════════════════════════════════════════╝

Type your question and press Enter.
Commands:
  /quit  → Exit
  /reset → Clear conversation display
  /help  → Show example queries
"""

EXAMPLE_QUERIES = """
Example queries to try:
  • How do I track my order?
  • What is the return policy for electronics?
  • I was charged twice — what do I do?
  • Do you deliver internationally?
  • How do I reset my password?
  • My account was hacked! (← triggers HITL escalation)
  • I want to file a fraud complaint (← triggers HITL escalation)
"""


def format_response(result: dict) -> str:
    """Format the graph result for clean CLI display."""
    lines = []
    lines.append("\n" + "─" * 58)

    # Metadata line
    route_label = "🚨 ESCALATED TO HUMAN" if result["escalated"] else "🤖 AI RESPONSE"
    conf_label  = f"[{result.get('confidence', 'N/A')} confidence]" if not result["escalated"] else ""
    intent      = result.get("intent", "general")

    lines.append(f"{route_label}  |  Intent: {intent}  {conf_label}")
    lines.append("─" * 58)

    # Main answer
    lines.append(result["final_answer"])

    # Ticket ID if escalated
    if result["escalated"] and result.get("escalation_reason"):
        lines.append(f"\n⚠️  Escalation reason: {result['escalation_reason']}")

    lines.append("─" * 58 + "\n")
    return "\n".join(lines)


def main():
    """Main interactive loop."""
    print(BANNER)

    # Step 1: Ensure knowledge base is ingested
    print("🔧 Initializing knowledge base...")
    try:
        run_ingestion()
    except Exception as e:
        print(f"❌ Failed to initialize knowledge base: {e}")
        sys.exit(1)

    print("\n✅ System ready! Ask your question below.\n")

    conversation_count = 0

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! 👋")
            break

        # Handle commands
        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
            print("\nGoodbye! 👋")
            break

        if user_input.lower() == "/reset":
            os.system("clear" if os.name == "posix" else "cls")
            print(BANNER)
            continue

        if user_input.lower() == "/help":
            print(EXAMPLE_QUERIES)
            continue

        # Process the query
        conversation_count += 1
        print(f"\n⏳ Processing...")

        try:
            result   = run_query(user_input)
            response = format_response(result)
            print(response)

        except Exception as e:
            print(f"\n❌ Error processing query: {e}")
            print("Please try again or type /quit to exit.\n")


if __name__ == "__main__":
    main()
