from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from .core.cache import check_cache_node, save_to_cache_node
from .core.state import NewsAggregatorState
from .input_analyzer.nodes import analyse_input_node, call_tools_node
from .output_formatter.nodes import output_formatter_node
from .output_validator.nodes import should_retry, validate_output_node


def _route_after_cache(state) -> str:
    """Conditional edge: skip the pipeline when a cache hit is found."""
    if state.cache_hit:
        return "end"
    return "input_analyser"


@lru_cache(maxsize=1)
def create_agent_pipeline():
    graph = StateGraph(NewsAggregatorState)

    graph.add_node("check_cache", check_cache_node)
    graph.add_node("input_analyser", analyse_input_node)
    graph.add_node("call_tools", call_tools_node)
    graph.add_node("validate_output", validate_output_node)
    graph.add_node("format_response", output_formatter_node)
    graph.add_node("save_to_cache", save_to_cache_node)

    graph.add_edge(START, "check_cache")
    graph.add_conditional_edges(
        "check_cache",
        _route_after_cache,
        {"end": END, "input_analyser": "input_analyser"},
    )
    graph.add_edge("input_analyser", "call_tools")
    graph.add_edge("call_tools", "validate_output")
    graph.add_conditional_edges(
        "validate_output",
        should_retry,
        {"call_tools": "call_tools", "format_response": "format_response"},
    )
    graph.add_edge("format_response", "save_to_cache")
    graph.add_edge("save_to_cache", END)
    return graph.compile()
