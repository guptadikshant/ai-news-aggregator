from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from src.agent_workflow.core.state import NewsAggregatorState
from src.agent_workflow.input_analyzer.nodes import (
    analyse_input_node,
    call_tools_node,
)


@lru_cache(maxsize=1)
def build_graph():
    builder = StateGraph(NewsAggregatorState)

    builder.add_node("analyse_input", analyse_input_node)
    builder.add_node("call_tools", call_tools_node)

    builder.add_edge(START, "analyse_input")
    builder.add_edge("analyse_input", "call_tools")
    builder.add_edge("call_tools", END)

    pipeline = builder.compile()

    return pipeline
