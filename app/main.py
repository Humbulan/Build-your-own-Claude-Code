import sys
import os
import subprocess
import pymysql
from anthropic import Anthropic

# --- 1. MariaDB Logging (Imperial Nexus) ---
def log_to_maria_db(prompt: str, response: str, tools_used: int = 0):
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="imperial_nexus",
            port=3306
        )
        with connection.cursor() as cursor:
            sql = "INSERT INTO agent_logs (prompt, response, tools_used) VALUES (%s, %s, %s)"
            cursor.execute(sql, (prompt, response, tools_used))
            connection.commit()
        connection.close()
    except Exception:
        pass

# --- 2. Tool Implementations ---
def tool_read_file(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def tool_write_file(path: str, content: str) -> str:
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def tool_bash(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Execution error: {e}"

def tool_git_status() -> str:
    try:
        result = subprocess.run(["git", "status", "-s"], capture_output=True, text=True, check=True)
        return result.stdout or "Working tree clean."
    except Exception as e:
        return f"Git error: {e}"

# --- 3. Main Agent Loop ---
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Imperial Network Claude Code Agent")
    parser.add_argument("-p", "--prompt", required=True, help="Prompt for the agent")
    args = parser.parse_args()

    prompt = args.prompt
    tools_used_count = 0

    # Explicitly pull from environment variables
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://openrouter.ai/api")
    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    
    if not auth_token:
        print("Error: Please set the ANTHROPIC_AUTH_TOKEN environment variable.")
        sys.exit(1)

    # Initialize the client with explicit parameters for OpenRouter
    client = Anthropic(
        base_url=base_url,
        api_key="",  
        auth_token=auth_token
    )

    # Define available tools
    tools = [
        {
            "name": "read_file",
            "description": "Read the contents of a file",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "The path to the file"}},
                "required": ["path"]
            }
        },
        {
            "name": "write_file",
            "description": "Create or overwrite a file with specific content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the file"},
                    "content": {"type": "string", "description": "The content to write"}
                },
                "required": ["path", "content"]
            }
        },
        {
            "name": "bash",
            "description": "Execute a bash command",
            "input_schema": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "The command to execute"}},
                "required": ["command"]
            }
        },
        {
            "name": "git_status",
            "description": "Check the current git status",
            "input_schema": {"type": "object", "properties": {}}
        }
    ]

    messages = [{"role": "user", "content": prompt}]
    
    try:
        response = client.messages.create(
            model="qwen/qwen3.5-flash-02-23",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

        while response.stop_reason == "tool_use":
            tool_use = next(block for block in response.content if block.type == "tool_use")
            tool_name = tool_use.name
            tool_input = tool_use.input
            tools_used_count += 1

            if tool_name == "read_file":
                tool_result = tool_read_file(tool_input["path"])
            elif tool_name == "write_file":
                tool_result = tool_write_file(tool_input["path"], tool_input["content"])
            elif tool_name == "bash":
                tool_result = tool_bash(tool_input["command"])
            elif tool_name == "git_status":
                tool_result = tool_git_status()
            else:
                tool_result = f"Unknown tool: {tool_name}"

            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": tool_result
                }]
            })

            response = client.messages.create(
                model="qwen/qwen3.5-flash-02-23",
                max_tokens=1024,
                tools=tools,
                messages=messages
            )

        output = ""
        for block in response.content:
            if block.type == "text":
                output += block.text
        
        # --- FIX: STRIP THE THINKING PROCESS ---
        if "</think>" in output:
            output = output.split("</think>")[-1].strip()
        elif "Thinking Process:" in output:
            output = output.split("Thinking Process:")[-1].strip()

    except Exception as e:
        output = f"API Error: {e}"

    # Stream output live to stdout
    for char in output:
        sys.stdout.write(char)
        sys.stdout.flush()
    print()

    # Log execution to MariaDB
    log_to_maria_db(prompt, output, tools_used_count)

if __name__ == "__main__":
    main()
