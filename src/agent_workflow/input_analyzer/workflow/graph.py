from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from src.agent_workflow.input_analyzer.workflow.nodes import analyse_input
from src.agent_workflow.input_analyzer.workflow.state import InputAnalyser


@lru_cache(maxsize=1)
async def build_graph():
    builder = StateGraph(InputAnalyser)
    builder.add_node("input_analyser", analyse_input)
    builder.add_edge(START, "input_analyser")
    builder.add_edge("input_analyser", END)

    graph = builder.compile()

    return graph