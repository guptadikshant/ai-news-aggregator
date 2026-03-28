from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from src.agent_workflow.input_analyzer.workflow.nodes import (
    analyse_input_node,
    call_tools_node,
)
from src.agent_workflow.input_analyzer.workflow.state import InputAnalyser


@lru_cache(maxsize=1)
async def build_graph():
    builder = StateGraph(InputAnalyser)

    builder.add_node("analyse_input", analyse_input_node)
    builder.add_node("call_tools", call_tools_node)

    builder.add_edge(START, "analyse_input")
    builder.add_edge("analyse_input", "call_tools")
    builder.add_edge("call_tools", END)

    pipeline = builder.compile()

    return pipeline
