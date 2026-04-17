# AEGIS - Adaptive Execution Guarded Interpreter System

**A Security-First Academic Compiler Design Project.**

AEGIS is an academic project demonstrating a novel *security-first execution model*. Unlike traditional compilers that optimize for speed by default, AEGIS starts all code in a sandboxed interpreter and promotes it to optimized bytecode execution only after it demonstrates safe behavior through runtime monitoring and trust-building.

## Core Concept
**Security is Default. Performance is Conditional.**
1. **Sandboxed start** - No code runs optimized initially.
2. **Runtime monitoring** - Code builds "trust" through safe execution.
3. **Execution privileges** - Trust unlocks the high-performance compiled bytecode VM.
4. **Instant rollback** - Security violations immediately revert execution to the sandbox.

## System Architecture

```text
Source → Lexer → Parser → AST → Static Analyzer
                                       ↓
                        Sandboxed Interpreter ⟷ Runtime Monitor
                                       ↓               ↓
                        Trust Manager ⟷ IR/VM (Optimized Execution)
```

**New Additions:** AEGIS now features a full **React-based Web Dashboard** with real-time interactive visualizations, a step-by-step debugger, and advanced compiler components (IR/TAC generation + Bytecode VM).

## Language Features
AEGIS implements a custom structured language aimed at demonstrating secure execution:
```aegis
# Core Types & Math
x = 10
y = 20
result = (x + y) * 2 % 3

# Control Flow
if result == 0
  print x
else
  while y > 0
    y = y - 1
  end
end

# Secure Output
print result
```
* **Supported operations**: `+`, `-`, `*`, `/`, `%`
* **Comparisons**: `==`, `!=`, `<`, `<=`, `>`, `>=`
* **Control flow**: `if`/`else` blocks and `while` loops. 
* *Note: The language intentionally lacks file I/O, user input, and arbitrary memory pointers for absolute security.*

## Quick Start (Web Dashboard)

The recommended way to experience AEGIS is through the visual dashboard.

1. **Start the API Backend**:
   ```bash
   pip install -r requirements.txt
   python webapp/server.py
   ```
2. **Start the React Frontend** (in a new terminal):
   ```bash
   cd ui
   npm install
   npm start
   ```
3. Open `http://localhost:3000` to access the IDE, visualize ASTs, step through bytecode, and observe trust scores accumulating in real-time.

## Project Structure
* `aegis/lexer/` & `parser/` - Grammar and Syntax parsing.
* `aegis/interpreter/` - Secure Sandboxed evaluator.
* `aegis/runtime/` & `trust/` - Security monitors and score keepers.
* `aegis/ir/` & `vm/` - Three Address Code (TAC) and Bytecode virtual machine.
* `webapp/` & `ui/` - React interface and Flask REST backend.

> For comprehensive design details, theoretical frameworks, and academic specifics, refer to [AEGIS_Documentation.md](AEGIS_Documentation.md).