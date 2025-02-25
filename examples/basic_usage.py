"""
Basic usage example for AutoGen Toolsmith.

This example shows how to:
1. Create a new tool from a specification
2. Use the tool in an AutoGen conversation
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Import required packages
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_toolsmith import ToolGenerator, get_tool
from autogen_toolsmith.tools import BaseTool


def create_demo_tool():
    """Create a demo date manipulation tool."""
    spec = """
    Create a tool that can perform date and time operations such as:
    - Get the current date and time
    - Convert between different time zones
    - Calculate the difference between two dates
    - Format dates in different ways
    - Add or subtract time periods from a date
    """
    
    # Initialize the tool generator
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required. Please set it in your .env file.")
    
    # 使用环境变量中的模型配置
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    generator = ToolGenerator(openai_api_key=api_key, model=model)
    
    # Create the tool
    tool_path = generator.create_tool(spec)
    print(f"Tool created at: {tool_path}")
    
    # The tool should now be available in the registry
    # Conventionally it will be named 'date_time_tool' or similar
    return tool_path


def use_tool_with_autogen():
    """Use the created tool in an AutoGen conversation."""
    
    # Try to get our date tool from the registry
    date_tool = None
    for tool_name in ["date_time_tool", "date_tool", "date_time_processor", "date_processor"]:
        tool = get_tool(tool_name)
        if tool:
            date_tool = tool
            break
    
    # If not found, use our example text processor tool
    if not date_tool:
        date_tool = get_tool("text_processor")
    
    # Initialize the OpenAI configuration for AutoGen
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required. Please set it in your .env file.")
    
    # 使用环境变量中的模型配置
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Create OpenAI client
    llm = OpenAIChatCompletionClient(
        model=model,
        api_key=openai_api_key
    )
    
    # Create the tool function to use in AutoGen
    def use_tool(tool_name: str, **kwargs):
        """
        A general-purpose function to call any registered AutoGen Toolsmith tool.
        
        Args:
            tool_name: The name of the tool to use.
            **kwargs: Arguments to pass to the tool.
            
        Returns:
            The result of the tool execution.
        """
        tool = get_tool(tool_name)
        if not tool:
            return {"error": f"Tool {tool_name} not found."}
        
        result = tool.run(**kwargs)
        return json.dumps(result, indent=2, default=str)
    
    # Use the general tool function
    def use_text_processor(**kwargs):
        """Use the text processor tool."""
        return use_tool("text_processor", **kwargs)
    
    # Or create a dedicated function for the date tool
    if date_tool:
        def use_date_tool(**kwargs):
            """Use the date tool."""
            return use_tool(date_tool.metadata.name, **kwargs)
        
        functions = [use_text_processor, use_date_tool]
    else:
        functions = [use_text_processor]
    
    # Create the agents
    assistant = AssistantAgent(
        name="assistant",
        llm=llm,
        tools=[
            {
                "name": f.__name__,
                "description": f.__doc__,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True,
                },
            }
            for f in functions
        ]
    )
    
    user_proxy = UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER", 
        code_execution_config={"work_dir": "coding"},
        tools={f.__name__: f for f in functions}
    )
    
    # Start the conversation
    cancellation_token = CancellationToken()
    console = Console()
    
    user_proxy.send_message(
        TextMessage(
            """
            Please demonstrate the capabilities of the text processing tool. 
            Specifically:
            1. Count the words and characters in this message
            2. Extract all unique words from the text: "To be or not to be, that is the question."
            3. Generate a summary of the following text:
               "Machine learning is a subfield of artificial intelligence that focuses on developing systems that can learn from data. 
               It has applications in many areas including computer vision, natural language processing, and recommendation systems. 
               Recent advances in deep learning have dramatically improved the performance of machine learning systems."
            """
        ),
        assistant,
        cancellation_token=cancellation_token,
        ui=console
    )


if __name__ == "__main__":
    # Uncomment to create a new tool
    # create_demo_tool()
    
    # Use the tool with AutoGen
    use_tool_with_autogen() 
