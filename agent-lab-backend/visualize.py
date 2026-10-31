from app.experiments.langgraph_v1.agent import builder
from langgraph.checkpoint.memory import MemorySaver

def generate_diagram():
    graph = builder.compile(checkpointer=MemorySaver(), interrupt_before=["write_tools"])
    
    # Extract LangGraph's internal Mermaid visualization code
    mermaid_code = graph.get_graph().draw_mermaid()
    
    print("\n--- COPY THE CODE BELOW ---")
    print(mermaid_code)
    print("---------------------------\n")
    print("Paste this code at: https://mermaid.live/")

if __name__ == "__main__":
    generate_diagram()