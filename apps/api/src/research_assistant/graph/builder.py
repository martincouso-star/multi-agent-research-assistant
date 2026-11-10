from langgraph.graph import END, StateGraph

from research_assistant.graph.nodes import (
    critic_node,
    planner_node,
    researcher_node,
    route_after_critic,
    writer_node,
)
from research_assistant.graph.state import ResearchState


def build_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("writer", writer_node)
    graph.add_node("critic", critic_node)
    graph.set_entry_point("planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", "critic")
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {"writer": "writer", "end": END},
    )
    return graph.compile()
