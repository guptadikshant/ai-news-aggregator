from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from src.agent_workflow.core.state import NewsAggregatorState
from src.agent_workflow.input_analyzer.nodes import call_tools_node
from src.agent_workflow.output_validator.nodes import (
    should_retry,
    validate_output_node,
)


@lru_cache(maxsize=1) 
def build_graph():
    builder = StateGraph(NewsAggregatorState)

    builder.add_node("validate_output", validate_output_node)
    builder.add_node("call_tools", call_tools_node)

    builder.add_edge(START, "validate_output")
    builder.add_conditional_edges(
        "validate_output",
        should_retry,
        {"call_tools": "call_tools", "end": END},
    )
    builder.add_edge("call_tools", "validate_output")

    pipeline = builder.compile()
    return pipeline
