from langgraph.graph import StateGraph, START, END
from functools import lru_cache
from src.agent_workflow.data_analyzer.workflow.state import DataAnalyseState

@lru_cache(maxsize=1)
def get_data_analyse_graph():
    workflow = StateGraph(DataAnalyseState)
    workflow.add_node(analyse_content_node)
    workflow.add_node(reject_content_node)
    workflow.add_edge(START, "analyse_content_node")
    workflow.add_edge("analyse_content_node", "reject_content_node")
    workflow.add_edge("reject_content_node", END)
    graph = workflow.compile()
    return graph