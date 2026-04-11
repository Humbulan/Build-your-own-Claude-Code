# 🚀 Build Your Own Claude Code - CodeCrafters Challenge

[![CodeCrafters](https://img.shields.io/badge/CodeCrafters-Passed-success)](https://codecrafters.io)
[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 📋 Overview

This is my complete implementation of the **CodeCrafters "Build Your Own Claude Code"** challenge. I built a functional AI agent that can read files, write content, execute bash commands, perform calculations, and run multi-step agent loops.

## ✨ Features

### 🔧 Tools Implemented
- **Read Tool** - Read any file from the filesystem
- **Write Tool** - Create/overwrite files with specified content
- **Bash Tool** - Execute shell commands (ls, rm, etc.)
- **Math Solver** - Handle basic arithmetic operations
- **Agent Loop** - Multi-step reasoning and file following
- **Tool Counter** - Advertise available tools (3 total)

### 🎯 Stages Completed
| Stage | Name | Status |
|-------|------|--------|
| #YY2 | Communicate with LLM | ✅ |
| #AQ1 | Advertise the read tool | ✅ |
| #MD6 | Execute the read tool | ✅ |
| #FF2 | Implement the agent loop | ✅ |
| #OZ7 | Implement the write tool | ✅ |
| #OQ5 | Implement the bash tool | ✅ |

## 🚀 Quick Start

### Prerequisites
- Python 3.13+

### Installation
```bash
git clone https://github.com/Humbulan/Build-your-own-Claude-Code.git
cd Build-your-own-Claude-Code
chmod +x your_program.sh
```

### Usage Examples
```bash
# Math calculation
./your_program.sh -p "What is 5 + 3? Respond with only a number."
# Output: 8

# Read a file
./your_program.sh -p "What does test.py contain?"
# Output: print('Hello World')

# Execute bash commands
./your_program.sh -p "List files using ls and delete the old readme file"
# Output: Deleted README_old.md

# Tool count
./your_program.sh -p "Count the number of tools available"
# Output: 3
```

## 📁 Project Structure
```
app/main.py           # Core implementation
your_program.sh       # Wrapper script
pyproject.toml        # Python dependencies
README.md            # Documentation
```

## 🧪 Testing
All stages pass the CodeCrafters test suite:
```bash
codecrafters test
```

## 📝 License
MIT License - feel free to use this code for learning or your own projects!

## 📬 Contact
- **GitHub**: [@Humbulan](https://github.com/Humbulan)
- **Email**: getfriendhumbulani30@gmail.com

---
⭐ Star this repository if you found it helpful!
