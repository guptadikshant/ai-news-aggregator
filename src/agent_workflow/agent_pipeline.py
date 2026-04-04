from langgraph.graph import StateGraph, START, END
from .core.state import NewsAggregatorState
from .output_validator.nodes import validate_output_node, should_retry
from .input_analyzer.nodes import analyse_input_node, call_tools_node
from functools import lru_cache


@lru_cache(maxsize=1)
def create_agent_pipeline():
    graph = StateGraph(NewsAggregatorState)

    graph.add_node("input_analyser", analyse_input_node)
    graph.add_node("call_tools", call_tools_node)
    graph.add_node("validate_output", validate_output_node)

    graph.add_edge(START, "input_analyser")
    graph.add_edge("input_analyser", "call_tools")
    graph.add_edge("call_tools", "validate_output")
    graph.add_conditional_edges(
        "validate_output",
        should_retry,
        {"call_tools": "call_tools", "end": END},
    )

    return graph.compile()