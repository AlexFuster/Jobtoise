from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langgraph.graph import END
from IPython.display import Image, display
from langgraph.graph import StateGraph, START
from langchain_openai import ChatOpenAI
import os
from mykeys import apiKey
from langgraph.checkpoint.mongodb import MongoDBSaver

os.environ['OPENAI_API_KEY'] = apiKey

model = ChatOpenAI(model="gpt-4o-mini",temperature=0)


class State(MessagesState):
    summary: str

# Define the logic to call the model
def call_model(state: State):
    
    # Get summary if it exists
    summary = state.get("summary", "")

    # If there is summary, then we add it
    if summary:
        
        # Add summary to system message
        system_message = f"Summary of conversation earlier: {summary}"
        print(system_message)

        # Append summary to any newer messages
        messages = [SystemMessage(content=system_message)] + state["messages"]
    
    else:
        messages = state["messages"]
    
    response = model.invoke(messages)
    return {"messages": response}

def summarize_conversation(state: State):
    
    # First, we get any existing summary
    summary = state.get("summary", "")

    # Create our summarization prompt 
    if summary:
        
        # A summary already exists
        summary_message = (
            f"This is summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
        
    else:
        summary_message = "Create a summary of the conversation above:"

    # Add prompt to our history
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)
    
    # Delete all but the 2 most recent messages
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}


# Determine whether to end or summarize the conversation
def should_continue(state: State):
    
    """Return the next node to execute."""
    
    messages = state["messages"]
    
    # If there are more than six messages, then we summarize the conversation
    if len(messages) > 6:
        return "summarize_conversation"
    
    # Otherwise we can just end
    return END


class Chatbot:
    def __init__(self, mongodb_client):
        # Define a new graph
        workflow = StateGraph(State)
        workflow.add_node("conversation", call_model)
        workflow.add_node(summarize_conversation)

        # Set the entrypoint as conversation
        workflow.add_edge(START, "conversation")
        workflow.add_conditional_edges("conversation", should_continue)
        workflow.add_edge("summarize_conversation", END)

        # Compile
        memory = MongoDBSaver(mongodb_client)
        self.graph = workflow.compile(checkpointer=memory)

    def __call__(self, query, thread_id='global'):
        config = {"configurable": {"thread_id": thread_id}}
        input_message = HumanMessage(content=query)
        output = self.graph.invoke({"messages": [input_message]}, config) 
        return {'answer':output['messages'][-1].content}
