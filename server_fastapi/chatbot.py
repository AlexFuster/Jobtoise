from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from typing import List

class State(MessagesState):
    summary: str
    jobsContext: List

MAX_RECURSION = 3

def get_unique_id(company, position):
    return company+' | '+position

class Chatbot:
    def __init__(self, model, db , qd):
        tools = [self.search_job]
        # Define a new graph
        workflow = StateGraph(State)
        workflow.add_node("conversation", self.call_model)
        workflow.add_node(self.summarize_conversation)
        workflow.add_node("tools", self.call_tool)
        workflow.add_node(self.clean_prev_tool_calls)

        # Set the entrypoint as conversation
        workflow.add_edge(START, "conversation")
        workflow.add_conditional_edges("conversation", self.should_continue)
        workflow.add_edge("tools", "clean_prev_tool_calls")
        workflow.add_edge("clean_prev_tool_calls", "conversation")
        workflow.add_edge("summarize_conversation", END)

        # Compile
        memory = MongoDBSaver(db.mongodb_client)
        self.model = model.bind_tools(tools, parallel_tool_calls=False)
        self.db =db
        self.qd = qd
        self.graph = workflow.compile(checkpointer=memory)

    def search_job(self, search_query_text: str) -> List:
        """Takes search_query_text and performs a semantic search with it in a Vector store, retrieving the job offers that better match the query

        Args:
            search_query_text: The query text describing the job or criteria the user is searching for. This can include job titles, skills, or other relevant details.
        
        Returns:
            list: A list of job postings that are semantically relevant to the search query. Each entry in the 
                list typically contains structured information about the job, such as the title, description, 
                location, and other details.
        """
        print('Search query', search_query_text)
        results = self.qd.searchVector(search_query_text)
        jobsContext = []
        for result in results:
            print(result.payload['company'],result.payload['position'])
            data_dict = self.db.load(result.payload['company'],result.payload['position'])
            del(data_dict['_id'])
            jobsContext.append(data_dict)
        print('Search results', jobsContext)
        return jobsContext

    def call_tool(self, state: State):
        tool_call = state["messages"][-1].tool_calls[0]
        jobsContext = self.search_job(**tool_call['args'])

        return {"jobsContext": jobsContext, "messages": ToolMessage(content=f'Found {len(jobsContext)} jobs', tool_call_id=tool_call["id"])}

    def clean_prev_tool_calls(self, state: State):
        tool_calls = []
        tool_messages = []
        for m in state["messages"]:
            if hasattr(m, "tool_calls") and len(m.tool_calls) > 0:
                tool_calls.append(m)
            elif type(m)==ToolMessage:
                tool_messages.append(m)

        delete_messages = []
        if len(tool_calls)>1:
            for tool_call, tool_msg in list(zip(tool_calls,tool_messages))[:-1]:
                delete_messages.append(RemoveMessage(id=tool_call.id))
                delete_messages.append(RemoveMessage(id=tool_msg.id))

        return {"messages": delete_messages}

    # Define the logic to call the model
    def call_model(self, state: State):
        
        # Get summary if it exists
        summary = state.get("summary", "")
        jobsContext = state.get("jobsContext", "")

        system_messages=[SystemMessage(content='You are an AI assistant that helps users search for jobs. You return the results in markdown format')]

        if summary:
            system_messages.append(SystemMessage(content=f"Summary of conversation earlier: {summary}"))

        if jobsContext:
            system_messages.append(SystemMessage(content=f"Retrieved jobs: {jobsContext}"))

        last_msg = state["messages"][-1]
        messages = state["messages"]
        if type(last_msg) == ToolMessage:
            messages = messages + [HumanMessage('Return only the company and position names for each job')]
        messages = system_messages + messages

        for m in messages:
            m.pretty_print()
        
        response = self.model.invoke(messages)
        return {"messages": response}

    def summarize_conversation(self, state: State):
        
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
        response = self.model.invoke(messages)
        
        # Delete all but the 2 most recent messages
        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
        return {"summary": response.content, "messages": delete_messages}


    # Determine whether to end or summarize the conversation
    def should_continue(self, state: State):
        
        """Return the next node to execute."""
        
        messages = state["messages"]
        last_message = messages[-1]

        recursion_count = state.get("recursion_count", 0)
        
        if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0 and recursion_count < MAX_RECURSION:
            state["recursion_count"] = recursion_count + 1
            return "tools"

        elif len(messages) > 10:
            return "summarize_conversation"
        
        # Otherwise we can just end
        return END

    def open_conversation(self,company,position):
        self.init_jobsContext = []
        if company and position :
            data_dict = self.db.load(company,position)
            del(data_dict['_id'])
            self.init_jobsContext.append(data_dict)
            thread_id = get_unique_id(company, position)
        else:
            thread_id = 'global'

        self.config = {"configurable": {"thread_id": thread_id}}

        message_history = []
        graph_state = self.graph.get_state(self.config)
        if graph_state.values.get("messages"):
            for msg in graph_state.values["messages"]:
                if type(msg)==HumanMessage:
                    message_history.append({'sender': 'You', 'text': msg.content})
                else:
                    message_history.append({'sender': 'Bot', 'text': msg.content})

        return message_history

    def __call__(self, query):
        input_message = HumanMessage(content=query)
        output = self.graph.invoke({"messages": [input_message], "jobsContext":self.init_jobsContext}, self.config) 
        return {'answer':output['messages'][-1].content}
