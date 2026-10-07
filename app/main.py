import sys
import os
import subprocess
import pymysql
from anthropic import Anthropic

def log_to_maria_db(prompt, response, tools_used=0):
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password=os.environ.get("MYSQL_ROOT_PASSWORD", ""),
            database="imperial_nexus",
            port=3306,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO agent_logs (prompt, response, tools_used) VALUES (%s, %s, %s)",
                (prompt, response, tools_used),
            )
            connection.commit()
        connection.close()
    except Exception:
        pass

def tool_read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return "Error reading file: %s" % e

def tool_write_file(path, content):
    try:
        with open(path, "w") as f:
            f.write(content)
        return "Successfully wrote to %s" % path
    except Exception as e:
        return "Error writing file: %s" % e

def tool_bash(command):
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return r.stdout if r.returncode == 0 else r.stderr
    except Exception as e:
        return "Execution error: %s" % e

def tool_git_status():
    try:
        r = subprocess.run(["git", "status", "-s"], capture_output=True, text=True, check=True)
        return r.stdout or "Working tree clean."
    except Exception as e:
        return "Git error: %s" % e

def tool_web_search(query, max_results=5):
    try:
        import requests
        import re
        from urllib.parse import quote_plus
        headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 13)"}
        url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return "Search failed: HTTP %s" % r.status_code
        blocks = re.findall(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>'
            r'.*?<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            r.text, re.DOTALL,
        )
        results = []
        for i, (href, title, snip) in enumerate(blocks[:max_results]):
            title = re.sub(r"<[^>]+>", "", title).strip()
            snip = re.sub(r"<[^>]+>", "", snip).strip()
            results.append("[%d] %s\n    URL: %s\n    %s" % (i + 1, title, href, snip))
        return "\n\n".join(results) if results else "No results for: " + query
    except Exception as e:
        return "Web search error: " + str(e)

SYSTEM_PROMPT = (
    "You are the Imperial Network AI Agent, running on Termux (Android) "
    "under a PRoot sandbox. You serve CEO Humbulani Mudau and the Imperial "
    "Network infrastructure.\n\n"
    "Project layout:\n"
    "- Main codebase: ~/imperial_network (symlink to ~/humbu_community_nexus/imperial_network)\n"
    "- Agent repo: ~/Build-your-own-Claude-Code\n"
    "- MariaDB: localhost:3306, database imperial_nexus, socket ~/mysql_run/mysql.sock\n"
    "- Prometheus: http://localhost:9091 (LIVE config: ~/imperial_network/prometheus.yml)\n"
    "- Pushgateway: http://localhost:9092, Grafana: http://localhost:3001\n"
    "- Alertmanager path: http://localhost:8117/api/v2/alerts\n"
    "- 76 active services across ports 1880-11434\n\n"
    "Operational rules:\n"
    "- Never delete or overwrite files without explicit confirmation.\n"
    "- The file prometheus/prometheus.yml is NOT live. "
    "The live config is prometheus.yml at the repo root.\n"
    "- Always run `promtool check config <file>` before reloading Prometheus.\n"
    "- Prefer read_file over bash for reading code.\n"
    "- Never commit .bak files, logs, node_modules, or .gguf models.\n"
    "- When in doubt, ask before acting."
)

TOOLS = [
    {"name": "read_file", "description": "Read a file",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Write or overwrite a file",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "bash", "description": "Execute a bash command",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "git_status", "description": "Check git status",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "web_search", "description": "Search the web for current information",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}}, "required": ["query"]}},
]

def dispatch(name, inp):
    if name == "read_file":    return tool_read_file(inp["path"])
    if name == "write_file":   return tool_write_file(inp["path"], inp["content"])
    if name == "bash":         return tool_bash(inp.get("command") or inp.get("cmd") or inp.get("script") or "")
    if name == "git_status":   return tool_git_status()
    if name == "web_search":   return tool_web_search(inp["query"], inp.get("max_results", 5))
    return "Unknown tool: %s" % name

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--prompt", required=True)
    args = parser.parse_args()

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://openrouter.ai/api")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not token:
        print("Error: ANTHROPIC_AUTH_TOKEN not set.")
        sys.exit(1)

    client = Anthropic(base_url=base_url, api_key="", auth_token=token)
    messages = [{"role": "user", "content": args.prompt}]
    used = 0

    def call_api(msgs):
        import time
        for attempt in range(3):
            try:
                return client.messages.create(
                    model="cohere/north-mini-code:free",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=msgs,
                )
            except Exception as e:
                if attempt < 2 and "onnection" in str(e):
                    time.sleep(2)
                    continue
                raise

    try:
        response = call_api(messages)
        while response.stop_reason == "tool_use":
            tu = next(b for b in response.content if b.type == "tool_use")
            used += 1
            result = dispatch(tu.name, tu.input)
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tu.id, "content": result}
            ]})
            response = client.messages.create(
                model="cohere/north-mini-code:free",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
        output = "".join(b.text for b in response.content if b.type == "text")
        if "</think>" in output:
            output = output.split("</think>")[-1].strip()
    except Exception as e:
        output = "API Error: %s" % e

    for c in output:
        sys.stdout.write(c)
        sys.stdout.flush()
    print()
    log_to_maria_db(args.prompt, output, used)

if __name__ == "__main__":
    main()
