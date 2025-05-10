from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.llms import Ollama
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType

from agents.intent_extraction_agent import intent_extraction_tool
from agents.semantic_search_tool import search_tool
from agents.filter_tool import filter_tool
from agents.response_generator import response_tool

# Load Mistral via Ollama
llm = Ollama(model="mistral", temperature=0.2)

# List of tools for the agent to choose from
tools = [
    intent_extraction_tool,
    search_tool,
    filter_tool,
    response_tool
]

# Create the prompt for structured chat agent with REQUIRED variables
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful shopping assistant that helps users find products matching their criteria.
    
You have access to the following tools:
{tools}

The available tools are: {tool_names}

To use a tool, please use the following format:
```
<userPrompt>
<toolName>
<toolInput>
```

When you have a response to share with the user, use the following format:
```
<userPrompt>
<response>
<responseContent>
```
You must always end your response with "Final Answer: <your answer here>".     
"""),
    ("user", "{input}")
])

agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Run the agent
if __name__ == "__main__":
    user_query = "Find me an Asus laptop under $2000 with at least 16GB RAM and a good battery life."
    inputs = {
        "input": user_query
    }
    result = agent_executor.invoke(inputs)
    print("\n💬 Final Response:\n", result["output"])
