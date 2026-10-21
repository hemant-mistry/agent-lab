import asyncio
from app.experiments.langchain_v1.agent import run_langchain_agent

async def main():
    # A query that forces the agent to look up the schema and perform a SQL JOIN
    query = "Which 3 projects have the highest actual spend, and who are the customers for those projects?"
    
    print(f"User Query: {query}\n")
    print("Executing LangChain Agent...\n")
    
    # Run the LangChain agent
    result = await run_langchain_agent(query)
    
    print("--- EXECUTION TRACE ---")
    
    # LangChain returns the final state dictionary, containing the full conversation history
    messages = result["messages"]
    
    for msg in messages:
        msg_type = msg.__class__.__name__
        
        if msg_type == "HumanMessage":
            print(f"\n[USER]: {msg.content}")
            
        elif msg_type == "AIMessage":
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"\n[AGENT THOUGHT -> TOOL CALL]: Invoking '{tc['name']}' with args: {tc['args']}")
            else:
                # Parse Gemini's content blocks into a clean string
                content = msg.content
                if isinstance(content, list):
                    content = "".join([
                        chunk.get("text", "") 
                        for chunk in content 
                        if isinstance(chunk, dict) and "text" in chunk
                    ])
                
                print(f"\n[FINAL ANSWER]:\n{content}")
                
        elif msg_type == "ToolMessage":
             snippet = str(msg.content).replace('\n', ' ')[:300]
             print(f"\n[OBSERVATION (Tool Result)]: {snippet}... (truncated)")
             
if __name__ == "__main__":
    asyncio.run(main())