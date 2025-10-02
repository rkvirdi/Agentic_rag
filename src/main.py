from langgraph.graph import StateGraph, END
from agents.orchestrator import orchestrator_agent
from agents.intent_router import intent_router_agent
from agents.planner import planner_agent
from agents.retrieval import hybrid_retrieval_agent
from agents.synthesizer import synthesizer_agent
from agents.validator import validator_agent
from utils.weaviate_client import client

def build_graph():
    workflow = StateGraph(dict)

    workflow.add_node("orchestrator", orchestrator_agent)
    workflow.add_node("router", intent_router_agent)
    workflow.add_node("planner", planner_agent)
    workflow.add_node("retrieval", hybrid_retrieval_agent)
    workflow.add_node("synthesizer", synthesizer_agent)
    workflow.add_node("validator", validator_agent)

    workflow.set_entry_point("orchestrator")

    workflow.add_edge("orchestrator", "router")
    workflow.add_edge("router", "planner")
    workflow.add_edge("planner", "retrieval")
    workflow.add_edge("retrieval", "synthesizer")
    workflow.add_edge("synthesizer", "validator")
    workflow.add_edge("validator", END)

    return workflow.compile()

if __name__ == "__main__":
    graph = build_graph()
    result = graph.invoke({"query": "Compare treatment A with treatment B"})
    print(result)
    client.close()  # cleanup
