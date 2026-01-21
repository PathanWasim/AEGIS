# AEGIS - Adaptive Execution Guarded Interpreter System

**A Security-First Academic Compiler Design Project**

AEGIS (Adaptive Execution Guarded Interpreter System) is an academic project that demonstrates a novel security-first execution model. Unlike traditional compilers that prioritize performance, AEGIS starts all code execution in a sandboxed interpreter and only promotes code to optimized execution after it has demonstrated safe behavior through runtime monitoring and trust building.

## Core Concept

**Security is Default. Performance is Conditional.**

1. **All code starts in a sandboxed interpreter** - No code runs optimized initially
2. **Runtime monitoring builds trust** - Safe execution increases trust scores  
3. **Trust enables optimization** - Only trusted code gets compiled execution
4. **Violations trigger rollback** - Any security issue reverts to interpreter
5. **Trust is revocable** - System can always return to safe mode

## Architecture Overview

```
Source Code → Lexer → Parser → AST → Static Analyzer
                                          ↓
                                   Sandboxed Interpreter ←→ Runtime Monitor
                                          ↓                        ↓
                                   Trust Manager ←→ Optimized Executor
                                          ↓                        ↓
                                   Rollback Handler ←←←←←←←←←←←←←←←←
```

## Language Specification

AEGIS implements a simple toy language for demonstration:

```
# Variable assignment
x = 10
y = 20

# Arithmetic expressions  
result = x + y * 2

# Print statements
print result
```

**Supported Features:**
- Integer variables and literals
- Arithmetic operators: `+`, `-`, `*`, `/`
- Variable assignment with `=`
- Print statements with `print`

**Security Constraints:**
- No user input operations
- No file system access
- No system calls
- Integer-only data types
- Sandboxed execution environment

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd aegis
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run tests:**
   ```bash
   pytest tests/
   ```

## Usage

### Command Line Execution

```bash
# Execute a program file
python main.py program.aegis

# Interactive mode
python main.py --interactive

# Show help
python main.py --help
```

### Interactive Mode Example

```
$ python main.py --interactive
[AEGIS] Starting interactive mode
Enter AEGIS code (type 'exit' to quit, 'help' for commands):

aegis> x = 10
[MODE] Interpreted Execution
[TRUST] Score = 0.1

aegis> y = x + 5  
[MODE] Interpreted Execution
[TRUST] Score = 0.2

aegis> print y
15
[MODE] Interpreted Execution  
[TRUST] Score = 0.3

# After multiple safe executions...
aegis> result = x * y
[MODE] Trusted Execution
[TRUST] Score = 1.2
```

## System Components

### 1. Lexer (`aegis/lexer/`)
Converts source code into tokens for parsing.

### 2. Parser (`aegis/parser/`)  
Builds Abstract Syntax Trees using recursive descent parsing.

### 3. AST (`aegis/ast/`)
Defines AST node types and provides tree manipulation utilities.

### 4. Static Analyzer (`aegis/interpreter/static_analyzer.py`)
Performs compile-time security checks before execution.

### 5. Sandboxed Interpreter (`aegis/interpreter/`)
Default secure execution environment with complete isolation.

### 6. Runtime Monitor (`aegis/runtime/monitor.py`)
Tracks execution behavior and detects security violations.

### 7. Trust Manager (`aegis/trust/`)
Maintains trust scores and makes optimization decisions.

### 8. Optimized Executor (`aegis/compiler/`)
Simulated compiled execution for trusted code.

### 9. Rollback Handler (`aegis/runtime/rollback.py`)
Manages transitions back to interpreter on violations.

## Trust Model

### Trust Score Lifecycle

- **Initial Score:** 0.0 (untrusted)
- **Safe Execution:** +0.1 per successful run
- **Optimization Threshold:** 1.0
- **Violation Penalty:** Reset to 0.0
- **Persistence:** Scores saved across sessions

### Execution Modes

**Interpreted Mode (Default):**
- All code starts here
- Complete sandboxing
- Full safety guarantees
- Slower execution

**Optimized Mode (Earned):**
- Requires trust score ≥ 1.0
- Cached execution paths
- Simulated compilation optimizations
- ~2x performance improvement
- Continued monitoring

## Security Model

### Static Analysis Checks
- Undefined variable detection
- Arithmetic overflow prevention
- Expression validation
- Type safety enforcement

### Runtime Monitoring
- Instruction count limits
- Memory usage tracking
- Operation validation
- Violation detection

### Rollback Triggers
- Runtime errors
- Security violations  
- Resource limit exceeded
- Undefined behavior

## Example Programs

### Basic Arithmetic
```
# basic_math.aegis
x = 10
y = 20
sum = x + y
product = x * y
print sum
print product
```

### Trust Building Demo
```
# trust_demo.aegis  
# Run this multiple times to see trust building
counter = 1
result = counter * 2
print result
```

### Security Violation Demo
```
# violation_demo.aegis
# This will trigger rollback if run in optimized mode
x = 10
y = 0
result = x / y  # Division by zero
print result
```

## Development Status

**Current Implementation Status:**
- [x] Project structure and foundations
- [ ] Lexical analysis (Lexer)
- [ ] Syntax analysis (Parser + AST)  
- [ ] Static security analysis
- [ ] Sandboxed interpreter
- [ ] Runtime monitoring
- [ ] Trust management
- [ ] Optimized execution
- [ ] Rollback handling
- [ ] System integration

## Testing Strategy

AEGIS uses a comprehensive testing approach:

- **Unit Tests:** Component-specific behavior validation
- **Property-Based Tests:** Universal correctness properties using Hypothesis
- **Integration Tests:** End-to-end system validation
- **Security Tests:** Violation detection and rollback validation

Run the test suite:
```bash
pytest tests/ -v
```

## Academic Context

This project is designed for **Compiler Design coursework** and demonstrates:

- **Lexical and Syntax Analysis:** Traditional compiler front-end
- **Security-First Design:** Novel execution model prioritizing safety
- **Runtime Systems:** Monitoring, trust management, and adaptive execution
- **System Architecture:** Component interaction and data flow

**Important Note:** Native compilation is simulated for academic demonstration. This is not a production compiler but an educational tool for understanding compiler concepts and security-adaptive execution models.

## Limitations

- **Toy Language:** Limited to basic arithmetic and variables
- **Simulated Compilation:** No actual machine code generation
- **Academic Scope:** Designed for learning, not production use
- **Integer-Only:** No support for other data types
- **No I/O:** Restricted to prevent security issues

## Contributing

This is an academic project. For educational purposes:

1. Fork the repository
2. Create a feature branch
3. Implement components following the design
4. Add comprehensive tests
5. Submit a pull request

## License

This project is created for academic purposes. Please respect educational integrity guidelines when using this code for coursework.

---

**AEGIS - Where Security Comes First, Performance Comes Second**