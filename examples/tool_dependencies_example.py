"""
Example demonstrating how to create tools with dependencies.

This example shows how to:
1. Use the existing text_formatter tool
2. Use the text_analyzer tool that depends on text_formatter
3. Create a new tool that depends on both
"""

import os
from autogen_toolsmith.tools import get_tool, list_tools
from autogen_toolsmith.generator.code_generator import ToolGenerator


def main():
    # Check if the OpenAI API key is set
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("Please set it to your OpenAI API key.")
        return
    
    # List all available tools
    print("Available tools:")
    tools = list_tools()
    for tool in tools:
        print(f"- {tool['name']}: {tool['description']}")
        if tool.get('dependencies'):
            print(f"  Dependencies: {', '.join(tool['dependencies'])}")
    print()
    
    # Use the text_formatter tool
    formatter = get_tool("text_formatter")
    if formatter:
        result = formatter.run("Hello World", to_upper=True)
        print(f"Formatter result: {result}")
    else:
        print("Text formatter tool not found.")
        return
    
    # Use the text_analyzer tool (depends on text_formatter)
    analyzer = get_tool("text_analyzer")
    if analyzer:
        basic_result = analyzer.run("Hello World")
        detailed_result = analyzer.run("Hello World. This is a test.", detailed=True)
        print(f"Analyzer basic result: {basic_result}")
        print(f"Analyzer detailed result: {detailed_result}")
    else:
        print("Text analyzer tool not found.")
        return
    
    # Create a new tool that depends on both the formatter and analyzer
    print("\nCreating a new tool that depends on existing tools...")
    generator = ToolGenerator()
    
    # Tool specification with dependencies
    tool_spec = """
    Create a 'TextSummarizer' tool that:
    1. Takes a text input and produces a summary
    2. First uses the text_formatter tool to normalize the text (convert to lowercase)
    3. Uses the text_analyzer tool to get basic text metrics
    4. Produces a summary consisting of:
       - The first sentence (or up to 10 words if no sentence end is found)
       - Basic text metrics (character count, word count)
       - A note if the text is especially long or short based on word count
    """
    
    # Generate the tool
    result = generator.create_tool(tool_spec)
    
    if result:
        print(f"New tool created at: {result}")
        
        # Use the new tool
        summarizer = get_tool("text_summarizer")
        if summarizer:
            test_text = "This is a sample text for summarization. It has multiple sentences and should demonstrate the capabilities of our newly created tool. The summarizer should extract the first sentence and provide some basic metrics."
            summary = summarizer.run(test_text)
            print(f"\nSummary result: {summary}")
        else:
            print("Summarizer tool not created properly.")
    else:
        print("Failed to create the new tool.")


if __name__ == "__main__":
    main() 