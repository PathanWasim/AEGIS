# AEGIS: Adaptive Execution Guarded Interpreter System
## Comprehensive Technical Documentation

**Document Version:** 2.0  
**System Version:** AEGIS Core 1.0.0, Backend 2.0.0  
**Last Updated:** April 2026  
**Status:** Production Documentation  

---

## Abstract

AEGIS (Adaptive Execution Guarded Interpreter System) is a security-first programming language interpreter that implements a novel trust-based adaptive execution model. The system reverses conventional compiler design philosophy by defaulting to a strictly sandboxed interpreter environment and selectively promoting code to optimized execution paths only after it has demonstrated sufficient trustworthiness through repeated safe execution. This document provides comprehensive technical documentation covering the language specification, compiler pipeline architecture, security model, trust mechanism, execution strategies, runtime monitoring, and the complete REST API and frontend architecture. AEGIS demonstrates that effective security can be achieved without sacrificing runtime performance through intelligent trust management and dynamic execution mode selection. The system serves as both a practical interpreter framework and a research platform for security-first language design.

---

## 1. Introduction

### 1.1 Overview and Motivation

The AEGIS system addresses a fundamental problem in computer security: how can we execute untrusted or unverified code safely while maintaining acceptable performance characteristics? Traditional approaches rely either on:

1. **Strict Sandboxing**: Complete isolation with minimal performance impact but significant overhead
2. **Static Analysis**: Proving safety before execution but with fundamental limitations in expressiveness
3. **Trust Relationships**: Operating under implicit trust assumptions that may be violated

AEGIS proposes a fourth approach: **Adaptive Execution with Dynamic Trust Management**. The core insight is that most code is executed repeatedly, and each successful execution provides evidence of safety. Rather than making binary trust decisions upfront, AEGIS accumulates trust evidence across multiple executions and adaptively adjusts execution strategies.

### 1.2 Design Philosophy

AEGIS is built on three core principles:

1. **Security-First Default**: All code executes in a restrictive sandbox by default, providing maximum security
2. **Evidence-Based Optimization**: Performance optimizations are unlocked gradually as code demonstrates consistent safety
3. **Transparent Monitoring**: All execution is monitored, measured, and reported to enable informed decision-making

### 1.3 Target Applications

AEGIS is designed for:
- Educational compiler and language design courses
- Cybersecurity research and vulnerability analysis
- Code analysis and static program understanding
- Interactive programming environments with security constraints
- Sandboxed execution of untrusted code in multi-tenant systems

---

## 2. System Architecture

### 2.1 Architectural Overview

The AEGIS system is organized into four major subsystems:

```
┌─────────────────────────────────────────────────────────────────┐
│                         AEGIS System                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Frontend   │  │   Backend    │  │   Core AEGIS │           │
│  │   (React)    │  │  (Flask)     │  │ (Python)     │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                   │
│         └─────────────────┴─────────────────┘                   │
│                      REST API                                   │
│                  (JSON Protocol)                                │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Core Module Organization

```
aegis/                          # Core language implementation
├── __init__.py               # Package initialization, version 1.0.0
├── errors.py                 # Comprehensive error hierarchy
├── pipeline.py               # Main AegisExecutionPipeline (7-stage)
├── lexer/                    # Lexical analysis
│   ├── tokens.py            # Token definitions and Token class
│   └── lexer.py             # Lexical analyzer implementation
├── parser/                   # Syntax analysis
│   └── parser.py            # Recursive descent parser
├── ast/                      # Abstract syntax tree
│   ├── nodes.py             # All AST node definitions
│   ├── visitor.py           # Visitor pattern base class
│   ├── pretty_printer.py    # Human-readable AST printing
│   └── serializer.py        # AST to dictionary conversion
├── interpreter/             # Execution engine
│   ├── context.py           # ExecutionContext and ExecutionMode
│   ├── interpreter.py       # SandboxedInterpreter class
│   └── static_analyzer.py   # Static semantic analysis
├── ir/                       # Intermediate representations
│   └── tac.py               # Three-address code generator
├── vm/                       # Virtual machine (bytecode)
│   ├── bytecode.py          # Bytecode instruction definitions
│   ├── compiler.py          # Bytecode compiler
│   └── vm.py                # Stack-based VM implementation
├── compiler/                 # Compilation and optimization
│   ├── cache.py             # Code cache with LRU eviction
│   └── optimizer.py         # AST optimizer and OptimizedExecutor
├── runtime/                  # Execution monitoring and recovery
│   ├── monitor.py           # RuntimeMonitor and metrics
│   └── rollback.py          # RollbackHandler implementation
└── trust/                    # Trust management system
    ├── trust_manager.py     # TrustManager and TrustScore
    └── trust_policy.py      # Trust policy constants

backend/                       # Flask backend server
├── app.py                    # Flask application setup
├── core/                     # Core pipeline and helpers
│   ├── pipeline.py          # Backend pipeline wrapper
│   └── helpers.py           # Utilities and example programs
└── routes/                   # API endpoints
    ├── execute.py           # POST /api/execute
    ├── tokenize.py          # POST /api/tokenize
    ├── analyze.py           # POST /api/analyze
    └── health.py            # GET /api/health, POST /api/trust/reset

frontend/                      # React frontend
├── src/
│   ├── App.jsx              # Main routing and orchestration
│   ├── store/
│   │   └── useStore.js      # Zustand global state
│   ├── services/
│   │   └── api.js           # REST API client
│   ├── components/
│   │   ├── editor/          # Monaco editor integration
│   │   ├── layout/          # Top bar and sidebar
│   │   └── panels/          # Output, pipeline, AST, tokens, trust
│   └── pages/
│       ├── Playground.jsx   # Main IDE interface
│       ├── Docs.jsx         # Language documentation
│       └── About.jsx        # Project information
```

### 2.3 Data Flow Architecture

```
┌──────────────┐
│ Source Code  │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│  Lexical Analysis    │ ─► Token Stream
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Syntax Analysis     │ ─► Abstract Syntax Tree
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Static Analysis      │ ─► Issues List
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Trust Lookup         │ ─► Trust Score, Execution Mode
└──────┬───────────────┘
       │
       ├─────────────────────────┬──────────────────────────┐
       │                         │                          │
       ▼                         ▼                          ▼
┌──────────────────┐  ┌──────────────────┐    ┌──────────────┐
│ SandboxedInterp  │  │ OptimizedExecutor │    │  RuntimeMon  │
│ (Default)        │  │ (Trust >= 1.0)    │    │  (All Modes) │
└──────┬───────────┘  └──────┬───────────┘    └──────┬───────┘
       │                     │                        │
       └─────────────────────┴────────────────────────┘
                        │
                        ▼
                ┌──────────────┐
                │ Execution    │
                │ Results      │
                └──────────────┘
                        │
                        ▼
                ┌──────────────┐
                │ Trust Update │
                └──────────────┘
```

---

## 3. Language Design

### 3.1 Lexical Specification

The AEGIS language is a simplified imperative language designed for teaching and research. The lexical specification defines all valid tokens.

#### 3.1.1 Token Classes

| Token Type | Pattern | Examples | Category |
|-----------|---------|----------|----------|
| IDENTIFIER | `[a-zA-Z_][a-zA-Z0-9_]*` | `x`, `count`, `_temp` | Variable/keyword |
| INTEGER | `[0-9]+` | `0`, `42`, `999999` | Literal |
| ASSIGN | `=` | `=` | Operator |
| PLUS | `+` | `+` | Operator |
| MINUS | `-` | `-` | Operator |
| MULTIPLY | `*` | `*` | Operator |
| DIVIDE | `/` | `/` | Operator |
| MODULO | `%` | `%` | Operator |
| EQ | `==` | `==` | Comparison |
| NEQ | `!=` | `!=` | Comparison |
| LT | `<` | `<` | Comparison |
| LTE | `<=` | `<=` | Comparison |
| GT | `>` | `>` | Comparison |
| GTE | `>=` | `>=` | Comparison |
| LPAREN | `(` | `(` | Delimiter |
| RPAREN | `)` | `)` | Delimiter |
| IF | `if` (keyword) | `if` | Control |
| ELSE | `else` (keyword) | `else` | Control |
| WHILE | `while` (keyword) | `while` | Control |
| END | `end` (keyword) | `end` | Control |
| PRINT | `print` (keyword) | `print` | I/O |
| NEWLINE | Line break | ↵ | Structural |
| EOF | End of input | | Structural |

#### 3.1.2 Comment Syntax

Comments begin with `#` and extend to the end of the line. They are stripped during lexical analysis and do not produce tokens.

```
# This is a comment
x = 5  # Variable assignment
y = x + 1  # x is 5, y becomes 6
```

#### 3.1.3 Lexer Implementation

The `Lexer` class (`aegis/lexer/lexer.py`) performs character-by-character scanning with:

- **Position Tracking**: Line and column numbers (1-indexed) for error reporting
- **Two-Character Lookahead**: Recognizes `==`, `!=`, `<=`, `>=` correctly
- **Comment Stripping**: Removes `#` comments before tokenization
- **Error Handling**: Raises `LexicalError` with position information on invalid input

```python
class Lexer:
    def tokenize(self, source_code: str) -> List[Token]:
        """Convert source code to list of tokens."""
        # Position tracking: line, column
        # Character-by-character scanning
        # Two-character lookahead for operators
        # Comment stripping
        # Comprehensive error reporting
```

### 3.2 Syntax Specification (EBNF)

The AEGIS grammar is specified in Extended Backus-Naur Form. The parser uses recursive descent with precedence climbing for expressions.

```ebnf
program         → statement* EOF
statement       → if_stmt
                | while_stmt
                | assignment
                | print_stmt

if_stmt         → "if" comparison NEWLINE statement* 
                  ( "else" NEWLINE statement* )? 
                  "end"

while_stmt      → "while" comparison NEWLINE statement* "end"

assignment      → IDENTIFIER "=" expression

print_stmt      → "print" expression

expression      → comparison

comparison      → term ( ( ">" | "<" | ">=" | "<=" 
                | "==" | "!=" ) term )*

term            → factor ( ( "+" | "-" ) factor )*

factor          → unary ( ( "*" | "/" | "%" ) unary )*

unary           → "-" unary
                | primary

primary         → INTEGER
                | IDENTIFIER
                | "(" expression ")"
```

### 3.3 Operator Precedence and Associativity

Operators are ordered by precedence (highest to lowest):

| Precedence | Operator(s) | Associativity | Notes |
|-----------|----------|--------------|-------|
| 5 (highest) | `-` (unary) | Right | Unary minus |
| 4 | `*`, `/`, `%` | Left | Multiplicative |
| 3 | `+`, `-` | Left | Additive |
| 2 | `==`, `!=`, `<`, `<=`, `>`, `>=` | Left | Comparison |
| 1 (lowest) | `=` | Right | Assignment (statement level) |

### 3.4 Semantic Rules

1. **Type System**: AEGIS uses a single integer type. All values are 32-bit signed integers.
2. **Variable Scope**: Program-wide scope; all variables are global
3. **Division**: Integer division using `//` semantics in Python (floor division)
4. **Comparison Results**: Comparison operators return 1 for true, 0 for false
5. **Unary Minus**: Implemented as `BinaryOpNode(IntegerNode(0), '-', operand)`

---

## 4. Compiler Pipeline

### 4.1 Pipeline Architecture

The AEGIS system implements a 7-stage execution pipeline orchestrated by the `AegisExecutionPipeline` class in `aegis/pipeline.py`.

```
┌─────────┐
│ Stage 1 │  Lexical Analysis
└────┬────┘  └─► Tokenization with error reporting
     │
┌────▼────┐
│ Stage 2 │  Syntax Analysis
└────┬────┘  └─► AST construction, grammar validation
     │
┌────▼────┐
│ Stage 3 │  Static Security Analysis
└────┬────┘  └─► Undefined variables, division by zero, etc.
     │
┌────▼────┐
│ Stage 4 │  Execution Mode Determination
└────┬────┘  └─► Trust lookup and mode selection
     │
     ├─────────────────────────┬─────────────────────┐
     │                         │                     │
┌────▼────┐           ┌────────▼─────┐   ┌──────────▼─┐
│ Stage 5a│           │ Stage 5b      │   │ Stage 5c   │
│Interpret│           │ Optimize      │   │ RunTime    │
│         │           │               │   │ Monitor    │
└────┬────┘           └────────┬─────┘   │            │
     │                         │         └──────┬─────┘
     └─────────────────────────┴────────────────┘
                        │
                ┌───────▼─────────┐
                │ Stage 6: Trust   │
                │ Score Update     │
                └───────┬──────────┘
                        │
                ┌───────▼──────────┐
                │ Stage 7: Rollback│
                │ Handling (if req)│
                └──────────────────┘
```

### 4.2 Stage 1: Lexical Analysis

**Input**: Raw source code string  
**Output**: List of `Token` objects  
**Error**: `LexicalError` on invalid characters

The `Lexer.tokenize()` method:
1. Scans characters sequentially
2. Maintains position (line, column) for error reporting
3. Groups characters into tokens
4. Strips comments (`#` to EOL)
5. Validates all characters

**Example**:
```
Source:  "x = 5  # assign\nprint x"
Tokens:  [
  Token(IDENTIFIER, 'x', 1, 1),
  Token(ASSIGN, '=', 1, 3),
  Token(INTEGER, '5', 1, 6),
  Token(NEWLINE, '\n', 1, 8),
  Token(PRINT, 'print', 2, 1),
  Token(IDENTIFIER, 'x', 2, 7),
  Token(EOF, '', 2, 9)
]
```

### 4.3 Stage 2: Syntax Analysis

**Input**: List of tokens  
**Output**: Abstract Syntax Tree (AST)  
**Error**: `AegisSyntaxError` on grammar violation

The `Parser` class implements recursive descent parsing:

```python
class Parser:
    def parse(self, tokens: List[Token]) -> List[ASTNode]:
        """Parse token stream into AST nodes."""
        # Recursive descent with precedence climbing
        # Single-pass, backtracking-free
        # Comprehensive error reporting with position info
```

**Key techniques**:
- Recursive descent for statements and control flow
- Precedence climbing for expression parsing
- No backtracking (single-pass)
- Immediate error reporting with token context

**Example AST Structure**:
```
Input:  "x = 5\nprint x + 1"

AST:
  AssignmentNode(
    identifier='x',
    expression=IntegerNode(5)
  )
  PrintNode(
    expression=BinaryOpNode(
      left=IdentifierNode('x'),
      operator='+',
      right=IntegerNode(1)
    )
  )
```

### 4.4 Stage 3: Static Security Analysis

**Input**: Abstract Syntax Tree  
**Output**: List of semantic issues or pass status  
**Error**: `SemanticError` if critical issues found

The `StaticAnalyzer` class (`aegis/interpreter/static_analyzer.py`) performs pre-execution semantic checks:

| Check | Severity | Description |
|-------|----------|-------------|
| Undefined Variables | HIGH | Variable used before assignment |
| Literal Division by Zero | HIGH | `expr / 0` where 0 is a constant |
| Infinite Loops | HIGH | While condition is always true (literal check) |
| Expression Depth | MEDIUM | Nesting exceeds maximum depth (max: 10) |
| Integer Overflow | MEDIUM | Large operands in `*` or `+` (>1,000,000) |

**Key Properties**:
- Conservative branch analysis: Variables defined in BOTH if/else branches are guaranteed; loop-body variables NOT added to outer scope
- Multi-error reporting: Collects all errors before raising
- No side effects: Pure analysis, does not modify the AST

**Example**:
```
Input:  "if x > 0\n  y = x + 1\nelse\n  y = 0\nend\nprint y"

Analysis: 
  ✓ Undefined variable 'x' detected (HIGH)
  ✓ Variable 'y' defined in both branches → safe to use after if/else
```

### 4.5 Stage 4: Execution Mode Determination

**Input**: Code hash, trust score, static analysis results  
**Output**: Execution mode (INTERPRETED or OPTIMIZED)  
**Logic**: Trust-based mode selection

```python
def determine_execution_mode(code_hash: str, trust_score: float) -> ExecutionMode:
    if trust_score >= 1.0 and execution_count >= 3:
        return ExecutionMode.OPTIMIZED  # Fast path
    else:
        return ExecutionMode.INTERPRETED  # Safe default
```

**Trust Thresholds**:
- Score >= 1.0: Code eligible for optimization
- Execution count >= 3: Sufficient history
- Success rate >= 80%: Consistent safety record

### 4.6 Stage 5: Program Execution

#### 5.6a: Sandboxed Interpretation

**Class**: `SandboxedInterpreter` (`aegis/interpreter/interpreter.py`)

The default execution mode with maximum safety guarantees:

**Safety Features**:
- **Integer Bounds**: Enforces 32-bit signed range [-2,147,483,648, 2,147,483,647]
- **Operation Limit**: Maximum 50,000 operations per execution
- **Loop Iteration Limit**: Maximum 10,000 iterations per loop
- **Division-by-Zero Detection**: Runtime check with detailed error
- **Memory Isolation**: Separate variable scope per execution

**Visitor Methods**:
```python
class SandboxedInterpreter(ASTVisitor):
    def visit_integer_node(self, node: IntegerNode) -> int
    def visit_identifier_node(self, node: IdentifierNode) -> int
    def visit_binary_op_node(self, node: BinaryOpNode) -> int
    def visit_assignment_node(self, node: AssignmentNode) -> None
    def visit_print_node(self, node: PrintNode) -> None
    def visit_if_node(self, node: IfNode) -> None
    def visit_while_node(self, node: WhileNode) -> None
```

**Execution Monitoring**: Hooks into `RuntimeMonitor` for every operation, tracking:
- Instruction counts
- Memory usage
- Variable accesses
- Arithmetic operations
- Execution timing

#### 5.6b: Optimized Execution

**Class**: `OptimizedExecutor` (`aegis/compiler/optimizer.py`)

Used when code has earned sufficient trust (score >= 1.0):

**Optimizations Applied**:
1. **Constant Folding**: `3 + 4` → `7` at compile time
2. **Dead Code Elimination**: Removes unused variable assignments
3. **Variable Propagation**: `x = 5; y = x + 1` → `y = 6`
4. **Expression Simplification**: `x + 0` → `x`, `x * 1` → `x`, etc.

**Performance Simulation**:
- Base speedup: 2.0x
- Constant folding bonus: +0.3x
- Dead code elimination bonus: +0.2x
- Variable propagation bonus: +0.25x
- Expression simplification bonus: +0.15x

**Maximum theoretical speedup**: ~3.0x

### 4.7 Stage 6: Trust Score Update

**Input**: Execution success, violations, metrics  
**Output**: Updated trust score for code hash  
**Component**: `TrustManager` (`aegis/trust/trust_manager.py`)

#### Trust Score Mechanics

Each code is assigned a `TrustScore` object tracking:
- `current_score`: Numerical trust value [0.0, 10.0]
- `execution_count`: Total executions
- `successful_executions`: Violation-free runs
- `violation_count`: Total security violations
- `trust_history`: Last 50 execution records

#### Trust Increment Rules

On successful execution (no violations):
- Base increment: +0.1
- Bonus for 5+ successful runs: +0.05
- Bonus for <100 instructions: +0.02
- Bonus for <0.1 second execution: +0.02

**Maximum single-run increment**: +0.19
**Maximum score**: 10.0

#### Trust Decrement Rules

On security violation:
- Primary penalty: -0.5
- Additional penalty for repeated violations: -0.2

**Minimum score**: 0.0

#### Trust Persistence

Trust data is persisted to `.aegis_trust.json` in JSON format:
```json
{
  "code_hash_1": {
    "current_score": 1.5,
    "execution_count": 10,
    "successful_executions": 10,
    "violation_count": 0,
    "trust_history": [...]
  }
}
```

### 4.8 Stage 7: Rollback Handling

**Input**: Execution result, violations  
**Output**: Rollback event (if violation in optimized mode)  
**Component**: `RollbackHandler` (`aegis/runtime/rollback.py`)

#### Rollback Trigger Conditions

Rollback occurs when:
1. Execution mode is OPTIMIZED
2. One or more security violations are detected
3. Violations are severe enough to warrant mode switch

#### Rollback Actions

1. Clear optimization cache for this code
2. Reset trust score to 0.0 for this code
3. Create `RollbackEvent` record
4. Log event for audit trail

#### Rollback Event Structure

```python
@dataclass
class RollbackEvent:
    timestamp: datetime
    violation_type: str
    code_hash: str
    details: str
    execution_mode: str
    rollback_time: float
    context_state: Dict[str, Any]
    violation_count: int
    trust_score_before: float
    trust_score_after: float
```

#### Rollback History

The rollback handler maintains history of last 100 rollback events with statistics:
- Total rollbacks count
- Rollbacks grouped by violation type
- Rollbacks grouped by code hash
- Average rollback time

---

## 5. Security Model

### 5.1 Security Layers

AEGIS implements security through multiple defense layers, each addressing different threat vectors:

```
┌────────────────────────────────────────────────────────┐
│ Layer 5: Trust Gate                                    │
│ ┌──────────────────────────────────────────────────────┤
│ │ Prevents premature optimization (score < 1.0)        │
│ └──────────────────────────────────────────────────────┤
│ Layer 4: Runtime Enforcement                          │
│ ┌──────────────────────────────────────────────────────┤
│ │ Integer bounds, operation limits, loop guards        │
│ └──────────────────────────────────────────────────────┤
│ Layer 3: Static Pre-Execution                         │
│ ┌──────────────────────────────────────────────────────┤
│ │ Undefined variables, division by zero, overflow      │
│ └──────────────────────────────────────────────────────┤
│ Layer 2: Syntactic                                    │
│ ┌──────────────────────────────────────────────────────┤
│ │ Grammar validation, malformed program rejection      │
│ └──────────────────────────────────────────────────────┤
│ Layer 1: Lexical                                      │
│ ┌──────────────────────────────────────────────────────┤
│ │ Invalid character rejection, immediate feedback      │
│ └──────────────────────────────────────────────────────┘
```

### 5.2 Threat Model

AEGIS addresses these specific threats:

#### 5.2.1 Infinite Loops

**Threat**: Code that never terminates, consuming CPU indefinitely

**Defenses**:
1. **Static Detection**: While loops with always-true literal conditions detected during analysis
2. **Runtime Counter**: Maximum 10,000 iterations per loop enforced
3. **Global Operation Limit**: Maximum 50,000 operations total per execution
4. **Timeout Detection**: Backend can terminate long-running processes

**Example Attack**:
```
# Statically caught
while 1
  x = x + 1
end

# Runtime caught
while x < 1000000
  x = x + 1
end
```

#### 5.2.2 Integer Overflow

**Threat**: Arithmetic operations exceeding 32-bit bounds, leading to wraparound and security issues

**Defenses**:
1. **Static Detection**: Large literal operands (>1,000,000) in multiplication/addition flagged
2. **Runtime Enforcement**: Every arithmetic operation checks result against [-2,147,483,648, 2,147,483,647]
3. **Immediate Error**: `RuntimeError` raised on overflow attempt

**Example Attack**:
```
x = 1000000
y = 1000000
z = x * y  # Runtime error: result overflows
```

#### 5.2.3 Undefined Variable Access

**Threat**: Reading uninitialized variables that might leak sensitive state or cause logic errors

**Defenses**:
1. **Static Detection**: Variable dataflow analysis identifies all uninitialized uses
2. **Runtime Detection**: NameError raised immediately on undefined access
3. **Scope Analysis**: Conservative branch analysis ensures variables are definitely defined

**Example Attack**:
```
# Statically caught
if x > 0
  y = 5
end
print y  # y might be undefined

# Runtime caught
print undefined_var
```

#### 5.2.4 Division by Zero

**Threat**: Illegal operation causing exception or incorrect behavior

**Defenses**:
1. **Static Detection**: Literal `expr / 0` patterns detected and flagged as HIGH severity
2. **Runtime Detection**: Variable division by zero checked at execution time
3. **Error Reporting**: Clear error message with context

**Example Attack**:
```
# Statically caught
z = x / 0

# Runtime caught
divisor = 0
z = x / divisor
```

#### 5.2.5 Resource Exhaustion

**Threat**: Consuming excessive system resources (memory, CPU, time)

**Defenses**:
1. **Instruction Counting**: Every operation increments counter
2. **Hard Limit**: 50,000 operations per execution
3. **Memory Limits**: Backend enforces 1MB memory limit
4. **Rollback on Violation**: Optimized mode reverts to sandbox on detection

---

## 6. Trust Model

### 6.1 Trust Fundamentals

The trust model is the core innovation of AEGIS. Rather than static trust decisions, trust is dynamic and evidence-based.

#### 6.1.1 Trust Principles

1. **Zero Trust by Default**: New code starts at score 0.0 (untrusted)
2. **Evidence Accumulation**: Each safe execution increases trust
3. **Violation Consequences**: Security violations significantly decrease trust
4. **Adaptive Thresholds**: Different operations require different trust levels
5. **Persistent Memory**: Trust decisions are recorded across sessions

#### 6.1.2 Trust Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                  Code First Encountered                │
│                    Trust: 0.0                          │
│                    Mode: INTERPRETED                   │
└──────────┬──────────────────────────────────────────────┘
           │
           ├─ Static Analysis: FAIL (HIGH issues)
           │  └─→ Trust: 0.2  │  Mode: INTERPRETED
           │
           ├─ Static Analysis: PASS (no HIGH issues)
           │  └─→ Trust: 0.6  │  Mode: INTERPRETED
           │
           ▼
    ┌─────────────────┐
    │ Execution Run 1 │
    └────────┬────────┘
             │
             ├─ Violation
             │  └─→ Trust: 0.0  │  Mode: INTERPRETED
             │
             ├─ Success
             │  └─→ Trust: 0.6+0.3=0.9  │  Mode: INTERPRETED
             │
             ▼
    ┌─────────────────┐
    │ Execution Run 2 │
    └────────┬────────┘
             │
             ├─ Success
             │  └─→ Trust: 0.9+0.3=1.2  │  Mode: OPTIMIZED
             │
             ▼
    ┌──────────────────────────┐
    │ Execution Run 3+ (Optimized)
    └────────┬─────────────────┘
             │
             ├─ Violation in Optimized Mode
             │  └─→ ROLLBACK
             │      Trust: 0.0  │  Mode: INTERPRETED (revert)
             │
             ├─ Success
             │  └─→ Trust: 1.2+0.3=1.5  │  Mode: OPTIMIZED
```

### 6.2 Trust Score Calculation

#### 6.2.1 Initial Trust Assignment

Upon first encounter with code:

```python
def initial_trust(static_analysis_has_high_issues: bool) -> float:
    if static_analysis_has_high_issues:
        return 0.2  # Code with HIGH severity issues
    else:
        return 0.6  # Statically clean code
```

#### 6.2.2 Trust Increment Rules

On each successful execution (no violations):

```
Base Increment:                      +0.10
├─ 5+ successful executions:        +0.05
├─ <100 instructions:               +0.02
├─ <0.1 seconds execution:          +0.02
└─ Total Possible Single Increment: +0.19

Maximum Score:                       10.0
```

#### 6.2.3 Trust Decrement Rules

On security violation:

```
Primary Violation Penalty:           -0.50
├─ Additional Penalty (repeated):   -0.20
├─ Total Possible Single Decrement: -0.70
└─ Minimum Score:                   0.0
```

#### 6.2.4 Optimization Eligibility

Code becomes eligible for optimized execution when:

```python
def is_optimizable(trust_score: TrustScore) -> bool:
    return (
        trust_score.current_score >= 1.0 AND
        trust_score.execution_count >= 3 AND
        trust_score.successful_executions / trust_score.execution_count >= 0.8
    )
```

### 6.3 Trust Persistence

Trust data is persisted to ensure continuity across server restarts.

#### 6.3.1 Storage Format

File: `.aegis_trust.json`

```json
{
  "abc123def456": {
    "current_score": 1.5,
    "execution_count": 15,
    "successful_executions": 14,
    "violation_count": 1,
    "first_execution": "2026-04-24T10:30:00.000000",
    "last_execution": "2026-04-24T11:45:00.000000",
    "last_violation": "2026-04-24T10:45:00.000000",
    "trust_history": [
      {
        "timestamp": "2026-04-24T10:30:00.000000",
        "score_before": 0.0,
        "score_after": 0.6,
        "execution_count": 1,
        "had_violations": false,
        "instruction_count": 45,
        "execution_time": 0.002,
        "increment": 0.6,
        "reason": "initial_safe"
      },
      ...
    ]
  }
}
```

#### 6.3.2 Code Hashing

Code identity is determined by SHA-256 hash of source code:

```python
def code_hash(source: str) -> str:
    hash_full = hashlib.sha256(source.encode()).hexdigest()
    return hash_full[:16]  # First 16 hex characters for brevity
```

Example:
- Source: `"x = 5\nprint x"`
- SHA-256: `e3b0c44298fc1c149afbf4c8996fb924...` (truncated)
- Used hash: `e3b0c44298fc1c14`

### 6.4 Trust Levels

Trust scores are categorized into levels for user communication:

| Level | Score Range | Characteristics | Optimization |
|-------|------------|-----------------|--------------|
| NONE | 0.0 - 0.5 | Untrusted, new code | INTERPRETED only |
| LOW | 0.5 - 1.0 | Some evidence of safety | INTERPRETED only |
| MEDIUM | 1.0 - 2.0 | Moderate track record | OPTIMIZED eligible |
| HIGH | 2.0+ | Consistent safe execution | OPTIMIZED, cache ready |

---

## 7. Execution Modes

### 7.1 Mode Overview

AEGIS supports two distinct execution modes, selected based on trust scores:

#### 7.1.1 Interpreted Mode (Default)

```
┌─────────────────────────────────────┐
│      Interpreted Execution          │
├─────────────────────────────────────┤
│ AST Visitor Pattern Interpretation  │
│ Runtime Monitoring: ENABLED         │
│ Safety Limits: ENFORCED             │
│ Performance: Baseline               │
└─────────────────────────────────────┘
```

**Characteristics**:
- Default for all untrusted code
- Uses `SandboxedInterpreter` visitor pattern
- Full runtime monitoring active
- All safety limits enforced
- Baseline performance (1.0x reference)

**Use Cases**:
- First execution of new code
- Code with undefined variables or runtime errors
- Code that failed static analysis
- Code with trust score < 1.0

#### 7.1.2 Optimized Mode

```
┌─────────────────────────────────────┐
│      Optimized Execution            │
├─────────────────────────────────────┤
│ AST Optimization Applied            │
│ Runtime Monitoring: ENABLED         │
│ Safety Limits: ENFORCED             │
│ Performance: Baseline + Bonuses     │
│ Cache: Enabled                      │
└─────────────────────────────────────┘
```

**Characteristics**:
- Enabled only for code with trust >= 1.0
- Uses `OptimizedExecutor` with `ASTOptimizer`
- Full runtime monitoring still active
- Safety limits still enforced
- Optimized performance (2.0x - 3.0x)

**Use Cases**:
- Code that has executed successfully 3+ times
- Code with high trust history
- Code demonstrating consistent safety

### 7.2 Mode Transition Rules

#### 7.2.1 INTERPRETED → OPTIMIZED

Code transitions to optimized mode when:

```python
current_mode == INTERPRETED AND
trust_score >= 1.0 AND
execution_count >= 3 AND
success_rate >= 0.8
```

**Example**:
```
Run 1: Trust 0.6 → INTERPRETED → Success → Trust 0.9
Run 2: Trust 0.9 → INTERPRETED → Success → Trust 1.2 ✓
Run 3: Trust 1.2 → OPTIMIZED (now eligible)
```

#### 7.2.2 OPTIMIZED → INTERPRETED (Rollback)

Code reverts to interpreted mode when security violation detected:

```python
if mode == OPTIMIZED AND violation_detected:
    trigger_rollback()
    trust_score = 0.0
    clear_cache()
    next_mode = INTERPRETED
```

**Implications**:
- Significant regression in trust
- Cache invalidated
- Requires rebuilding trust from scratch
- Valuable signal that optimization was premature

### 7.3 Mode Performance Characteristics

#### 7.3.1 Interpreted Mode Performance

Baseline performance metrics (varies by system):

| Metric | Typical Value | Notes |
|--------|--------------|-------|
| Speedup Factor | 1.0x | Baseline reference |
| Instructions/sec | 100-500k | System dependent |
| Memory Overhead | ~2MB baseline | Visitor pattern overhead |
| Startup Latency | <1ms | Negligible |

#### 7.3.2 Optimized Mode Performance

With optimizations applied:

| Metric | Typical Value | Components |
|--------|--------------|-----------|
| Speedup Factor | 2.0-3.0x | See breakdown below |
| Base Optimization | 2.0x | Compilation speedup |
| + Constant Folding | +0.3x | Compile-time evaluation |
| + Dead Code Elim | +0.2x | Reduced instructions |
| + Variable Prop | +0.25x | Fewer variable lookups |
| + Expression Simplify | +0.15x | Simpler operations |
| Maximum Theoretical | 3.0x | Sum of all bonuses |

**Actual speedup depends on code characteristics and optimization applicability.**

---

## 8. Runtime Monitoring

### 8.1 Monitor Architecture

The `RuntimeMonitor` class tracks all execution behavior in real-time, providing metrics and violation detection.

```
┌──────────────────────────────┐
│   Execution Activity          │
└──────────┬───────────────────┘
           │ Every Operation
           ▼
┌──────────────────────────────┐
│   RuntimeMonitor             │
├──────────────────────────────┤
│  - Instruction Counting      │
│  - Limit Enforcement         │
│  - Metrics Collection        │
│  - Violation Detection       │
└──────────┬───────────────────┘
           │
           ├─→ Metrics (cumulative)
           │
           └─→ Violations (triggered)
```

### 8.2 Metrics Collection

The `ExecutionMetrics` dataclass tracks comprehensive execution statistics:

```python
@dataclass
class ExecutionMetrics:
    instruction_count: int              # Total operations
    memory_usage: int                   # Bytes consumed
    execution_time: float               # Wall-clock seconds
    operations_performed: List[str]     # Detailed operation log
    violations_detected: List[SecurityViolation]  # Any violations
    variables_accessed: List[str]       # Variable names used
    arithmetic_operations: int          # Count of +, -, *, /, %
    assignment_operations: int          # Count of x = ...
    print_operations: int               # Count of print statements
```

#### 8.2.1 Instruction Counting

Each operation increments the counter:

| Operation | Cost |
|-----------|------|
| Arithmetic (+, -, *, /, %) | 1 instruction |
| Assignment (=) | 1 instruction |
| Comparison (==, !=, <, etc.) | 1 instruction |
| Variable Access | 1 instruction |
| Print statement | 1 instruction |
| Loop Iteration | 1 instruction |
| If/Else Branch | 1 instruction |

**Total per execution limited to 50,000 instructions.**

#### 8.2.2 Operation Logging

All operations are logged with details for audit trail:

```
[Arithmetic]  addition:          5 + 3 = 8
[Assignment]  variable:          x = 8
[Variable]    access:            load y
[Arithmetic]  multiplication:    8 * 2 = 16
[Comparison]  greater_than:      16 > 10 → 1 (true)
[Loop]        iteration:         1 of 10
[Print]       output:            16
```

### 8.3 Violation Detection

Violations are detected when limits are exceeded:

#### 8.3.1 Violation Types

| Violation | Trigger | Severity | Rollback |
|-----------|---------|----------|----------|
| InstructionLimitExceeded | >50,000 operations | CRITICAL | Yes if OPTIMIZED |
| LoopIterationLimitExceeded | >10,000 per loop | CRITICAL | Yes if OPTIMIZED |
| IntegerOverflow | Arithmetic out of range | CRITICAL | Yes if OPTIMIZED |
| DivisionByZero | Division by 0 at runtime | CRITICAL | Yes if OPTIMIZED |
| MemoryExceeded | >1MB allocated | HIGH | Yes if OPTIMIZED |

#### 8.3.2 SecurityViolation Dataclass

```python
@dataclass
class SecurityViolation:
    violation_type: str          # Type name
    message: str                 # Human-readable message
    severity: str                # CRITICAL, HIGH, MEDIUM, LOW
    instruction_count: int       # When violation occurred
    context: ExecutionContext    # State at violation time
    timestamp: datetime          # When detected
    code_hash: str              # Which code violated
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON response."""
```

### 8.4 Monitoring Integration

The monitor integrates with all execution paths:

```python
# In SandboxedInterpreter
def visit_binary_op_node(self, node: BinaryOpNode):
    ...
    self.runtime_monitor.add_operation("arithmetic", f"{l} {op} {r}")
    ...
    
# In RollbackHandler
def trigger_rollback(self, ...):
    event.rollback_time = time.time() - start
    self.monitor.record_rollback(event)
```

---

## 9. Rollback Mechanism

### 9.1 Rollback Overview

Rollback is the automatic recovery mechanism triggered when optimized code violates security constraints.

```
┌──────────────────────┐
│   Optimized Code     │
│   Executing...       │
└────────┬─────────────┘
         │
         ├─ Success
         │  └─→ Trust Update, Continue
         │
         ├─ Violation Detected!
         │  └─→ ROLLBACK
         │
         ▼
┌──────────────────────────────────┐
│     Rollback Handler             │
├──────────────────────────────────┤
│ 1. Clear Optimization Cache      │
│ 2. Reset Trust Score to 0.0      │
│ 3. Create RollbackEvent Record   │
│ 4. Revert to Sandboxed Mode      │
│ 5. Restart Execution?            │
└──────────────────────────────────┘
```

### 9.2 Rollback Trigger Conditions

Rollback occurs when ALL of the following are true:

1. Execution mode is OPTIMIZED
2. A `SecurityViolation` is detected during execution
3. The violation is of type CRITICAL or HIGH severity

**Rollback does NOT occur if**:
- Execution mode is INTERPRETED (already sandboxed)
- Violation is LOW or MEDIUM severity
- Violation is caught by runtime monitor but handled gracefully

### 9.3 Rollback Actions

#### 9.3.1 Cache Invalidation

```python
def trigger_rollback(self, code_hash: str, ...):
    # Clear the optimization cache for this code
    self.cache.invalidate(code_hash)
    # Future runs will not use cached optimized AST
```

#### 9.3.2 Trust Revocation

```python
    # Reset trust to 0.0 (untrusted)
    self.trust_manager.revoke_trust_for_violation(code_hash)
    # Code must rebuild trust from beginning
```

#### 9.3.3 Event Recording

```python
    # Create detailed rollback event
    event = RollbackEvent(
        timestamp=datetime.now(),
        violation_type=violation.violation_type,
        code_hash=code_hash,
        details=violation.message,
        execution_mode='optimized',
        rollback_time=elapsed,
        context_state=violation.context.to_dict(),
        violation_count=len(violations),
        trust_score_before=trust_before,
        trust_score_after=0.0
    )
    self.history.append(event)
```

### 9.4 RollbackEvent Structure

```python
@dataclass
class RollbackEvent:
    timestamp: datetime
    violation_type: str             # e.g., "InstructionLimitExceeded"
    code_hash: str                  # Affected code identifier
    details: str                    # Detailed violation message
    execution_mode: str             # "optimized" (was in this mode)
    rollback_time: float            # Time to perform rollback
    context_state: Dict[str, Any]   # Program state at violation
    violation_count: int            # Number of violations
    trust_score_before: float       # Trust before rollback
    trust_score_after: float        # Trust after (0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON."""
```

### 9.5 Rollback History

The rollback handler maintains complete history:

```python
class RollbackHandler:
    def __init__(self):
        self.history: List[RollbackEvent] = []
        self.statistics = {
            'total_rollbacks': 0,
            'rollbacks_by_type': {},
            'rollbacks_by_code': {},
            'avg_rollback_time': 0.0
        }
```

**Statistics tracked**:
- Total rollback count
- Rollbacks per violation type
- Rollbacks per code hash
- Average time to perform rollback

**History retention**: Last 100 rollback events

### 9.6 User-Facing Rollback Reporting

In the frontend, rollback events are reported as:

```json
{
  "rollback": true,
  "rollback_event": {
    "timestamp": "2026-04-24T10:45:00.000000",
    "violation_type": "InstructionLimitExceeded",
    "details": "Program exceeded 50,000 instruction limit",
    "trust_score_before": 1.5,
    "trust_score_after": 0.0,
    "message": "Security violation detected in optimized mode. Code reverted to sandbox. Trust reset."
  },
  "execution_mode": "optimized (rolled back)",
  "trust_level": "NONE"
}
```

---

## 10. Optimization System

### 10.1 Optimization Overview

The optimization system applies compile-time transformations to increase execution performance for trusted code.

```
┌──────────────┐
│ Trusted AST  │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│   ASTOptimizer       │
├──────────────────────┤
│ 1. Constant Folding  │
│ 2. Dead Code Elim    │
│ 3. Variable Prop     │
│ 4. Expr Simplify     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────┐
│ Optimized AST    │ ─→ Cache
│ + Metrics        │
└──────────────────┘
```

### 10.2 Code Cache

The `CodeCache` class implements LRU (Least Recently Used) eviction:

#### 10.2.1 Cache Configuration

```python
class CodeCache:
    max_size: int = 100              # Maximum entries
    max_age: timedelta = 24 hours    # Expiration time
    eviction_policy: str = 'LRU'     # Eviction strategy
```

#### 10.2.2 CachedCode Entry

```python
@dataclass
class CachedCode:
    code_hash: str
    original_ast: List[ASTNode]
    optimized_ast: List[ASTNode]
    compilation_time: float
    created_at: datetime
    last_accessed: datetime
    access_count: int
    optimization_flags: Dict[str, bool]
    performance_stats: Dict[str, float]
```

#### 10.2.3 Cache Operations

```python
class CodeCache:
    def get(self, code_hash: str) -> Optional[CachedCode]:
        # Retrieve cached entry, update access time
        # Returns None if not found or expired
        
    def put(self, code: CachedCode) -> None:
        # Store code in cache
        # Evict oldest if at max_size
        
    def invalidate(self, code_hash: str) -> None:
        # Remove specific entry (used on rollback)
        
    def clear(self) -> None:
        # Remove all entries
```

#### 10.2.4 Cache Metrics

```python
@dataclass
class CacheMetrics:
    cache_hits: int              # Successful retrievals
    cache_misses: int            # Not found or expired
    hit_rate: float              # hits / (hits + misses)
    evictions: int               # Number of evicted entries
    compilations: int            # Number of optimizations
    avg_compilation_time: float  # Average optimization duration
```

### 10.3 AST Optimizer

The `ASTOptimizer` applies transformations while preserving semantics.

#### 10.3.1 Constant Folding

**Goal**: Evaluate constant expressions at compile time

**Examples**:
```
3 + 4                 → 7
10 - 5                → 5
2 * 3                 → 6
8 / 2                 → 4
100 % 7               → 2
(2 + 3) * (4 - 1)    → 15
```

**Implementation**:
```python
def visit_binary_op_node(self, node: BinaryOpNode):
    left = self.visit(node.left)
    right = self.visit(node.right)
    
    if isinstance(left, IntegerNode) and isinstance(right, IntegerNode):
        # Both operands are constants
        result = self._evaluate(left.value, node.operator, right.value)
        self.optimization_flags['constant_folding'] = True
        return IntegerNode(result)
    
    return BinaryOpNode(left, node.operator, right)
```

#### 10.3.2 Dead Code Elimination

**Goal**: Remove assignments to variables that are never used

**Algorithm**:
1. First pass: Collect all variable uses
2. Second pass: Remove assignments to unused variables

**Examples**:
```
Input:
  x = 5
  y = 10
  z = x + 1
  print z

Output:
  y = 10  # REMOVED (y never used)
  x = 5
  z = x + 1
  print z
```

**Implementation**:
```python
def optimize(self, ast):
    # First pass: collect used variables
    for node in ast:
        node.accept(self)  # Populates self.used_variables
    
    # Second pass: filter dead assignments
    optimized = [node for node in ast 
                 if not self._is_dead_assignment(node)]
    
    self.optimization_flags['dead_code_elimination'] = True
    return optimized
```

#### 10.3.3 Variable Propagation

**Goal**: Replace variable uses with constant values when possible

**Examples**:
```
Input:
  x = 5
  y = x + 1
  z = y * 2

Output:
  x = 5
  y = 6          # Constant folded: 5 + 1
  z = 12         # Constant folded: 6 * 2
```

**Implementation**:
```python
def optimize(self, ast):
    self.constants = {}  # Track constant assignments
    
    for node in ast:
        if isinstance(node, AssignmentNode):
            # If RHS is constant, record it
            if is_constant(node.expression):
                self.constants[node.identifier] = evaluate(node.expression)
    
    # Replace variable uses with constants
    for node in ast:
        if isinstance(node, IdentifierNode):
            if node.name in self.constants:
                return IntegerNode(self.constants[node.name])
    
    self.optimization_flags['variable_propagation'] = True
    return optimized_ast
```

#### 10.3.4 Expression Simplification

**Goal**: Apply algebraic identities to reduce operations

**Rules**:
- `x + 0` → `x`
- `0 + x` → `x`
- `x * 0` → `0`
- `0 * x` → `0`
- `x * 1` → `x`
- `1 * x` → `x`
- `x / 1` → `x`
- `x - 0` → `x`

**Examples**:
```
Input:
  x = 5
  y = x + 0
  z = 1 * x
  w = x * 1

Output:
  x = 5
  y = x         # Simplified: x + 0
  z = x         # Simplified: 1 * x
  w = x         # Simplified: x * 1
```

**Implementation**:
```python
def visit_binary_op_node(self, node: BinaryOpNode):
    left = self.visit(node.left)
    right = self.visit(node.right)
    
    # Apply simplification rules
    if node.operator == '+':
        if is_zero(right):
            self.optimization_flags['expression_simplification'] = True
            return left
        if is_zero(left):
            self.optimization_flags['expression_simplification'] = True
            return right
    
    # ... similar for other operators
    
    return BinaryOpNode(left, node.operator, right)
```

### 10.4 OptimizedExecutor

The `OptimizedExecutor` executes optimized code with performance simulation:

```python
class OptimizedExecutor:
    def execute(self, ast: List[ASTNode], context: ExecutionContext) -> None:
        # 1. Check cache
        cached = self.cache.get(context.code_hash)
        
        if cached:
            # Use cached optimized AST
            optimized_ast = cached.optimized_ast
            context.metrics.cache_hit = True
        else:
            # Optimize and cache
            optimizer = ASTOptimizer()
            result = optimizer.optimize(ast)
            optimized_ast = result.optimized_ast
            self.cache.put(cached_code)
        
        # 2. Execute with monitoring
        self.interpreter.execute(optimized_ast, context)
        
        # 3. Simulate performance improvement
        context.metrics.speedup_factor = self._calculate_speedup(
            result.optimization_flags
        )
        context.metrics.optimization_applied = True
```

---

## 11. API Design

### 11.1 REST API Overview

The backend Flask application exposes a RESTful API for the frontend:

```
┌────────────────────────────────────────────────────────┐
│  AEGIS Backend API (Port 5000)                        │
├────────────────────────────────────────────────────────┤
│ POST   /api/execute      - Full pipeline execution    │
│ POST   /api/tokenize     - Lexical analysis only     │
│ POST   /api/analyze      - Static analysis only      │
│ GET    /api/health       - Server status             │
│ POST   /api/trust/reset  - Clear all trust scores    │
│ GET    /api/examples     - Built-in example programs │
└────────────────────────────────────────────────────────┘
```

### 11.2 Request/Response Protocol

#### 11.2.1 Execute Endpoint

**Endpoint**: `POST /api/execute`

**Request**:
```json
{
  "source_code": "x = 5\ny = x + 3\nprint y"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "output": ["8"],
  "execution_time": 0.002,
  "execution_mode": "interpreted",
  "trust_score": 0.9,
  "trust_level": "MEDIUM",
  "metrics": {
    "instruction_count": 4,
    "memory_usage": 128,
    "execution_time": 0.002,
    "operations_performed": 4,
    "violations_detected": 0,
    "variables_accessed": 2,
    "arithmetic_operations": 1,
    "assignment_operations": 2,
    "print_operations": 1,
    "operations_per_second": 2000,
    "optimization_applied": false,
    "cache_hit": false,
    "speedup_factor": 1.0
  },
  "violations": [],
  "rollback_events": [],
  "error_message": null,
  "tokens": [...],
  "ast": {...},
  "pipeline_stages": [...]
}
```

**Response (Error)**:
```json
{
  "success": false,
  "error": "Undefined variable: z at line 3, column 7",
  "error_type": "SemanticError",
  "error_code": "SEM001",
  "suggestions": ["Define z before using it", "Check variable name for typos"]
}
```

#### 11.2.2 Tokenize Endpoint

**Endpoint**: `POST /api/tokenize`

**Request**:
```json
{
  "source_code": "x = 5"
}
```

**Response**:
```json
{
  "success": true,
  "tokens": [
    {
      "type": "IDENTIFIER",
      "value": "x",
      "line": 1,
      "column": 1,
      "category": "variable"
    },
    {
      "type": "ASSIGN",
      "value": "=",
      "line": 1,
      "column": 3,
      "category": "operator"
    },
    {
      "type": "INTEGER",
      "value": "5",
      "line": 1,
      "column": 5,
      "category": "literal"
    },
    {
      "type": "EOF",
      "value": "",
      "line": 1,
      "column": 6,
      "category": "structural"
    }
  ],
  "token_count": 4,
  "categories": {
    "variable": 1,
    "operator": 1,
    "literal": 1,
    "structural": 1
  }
}
```

#### 11.2.3 Analyze Endpoint

**Endpoint**: `POST /api/analyze`

**Request**:
```json
{
  "source_code": "if x > 0\n  y = 5\nend\nprint y"
}
```

**Response**:
```json
{
  "success": true,
  "issues": [
    {
      "type": "UNDEFINED_VAR",
      "severity": "HIGH",
      "message": "Variable 'x' used before assignment",
      "line": 1,
      "column": 4,
      "variable": "x"
    },
    {
      "type": "UNDEFINED_VAR",
      "severity": "HIGH",
      "message": "Variable 'y' may not be defined (depends on if condition)",
      "line": 4,
      "column": 7,
      "variable": "y"
    }
  ],
  "issue_count": 2,
  "has_high_severity": true,
  "trusted": false
}
```

#### 11.2.4 Health Endpoint

**Endpoint**: `GET /api/health`

**Response**:
```json
{
  "status": "online",
  "version": "2.0.0",
  "uptime_seconds": 3600,
  "trust_entries": 42,
  "cache_size": 15,
  "cache_hits": 128,
  "cache_misses": 234,
  "active_executions": 0,
  "timestamp": "2026-04-24T11:00:00.000000"
}
```

#### 11.2.5 Trust Reset Endpoint

**Endpoint**: `POST /api/trust/reset`

**Response**:
```json
{
  "success": true,
  "message": "All trust scores cleared",
  "cleared_entries": 42
}
```

#### 11.2.6 Examples Endpoint

**Endpoint**: `GET /api/examples`

**Response**:
```json
{
  "examples": [
    {
      "id": "hello_world",
      "name": "Hello World",
      "description": "Classic introductory program",
      "code": "print 42",
      "difficulty": "beginner"
    },
    {
      "id": "fibonacci",
      "name": "Fibonacci Sequence",
      "description": "Calculate Fibonacci numbers up to 10 iterations",
      "code": "x = 0\ny = 1\ni = 0\nwhile i < 10\n  print x\n  z = x + y\n  x = y\n  y = z\n  i = i + 1\nend",
      "difficulty": "intermediate"
    },
    ...
  ],
  "total_examples": 12
}
```

### 11.3 Error Handling

All API endpoints follow consistent error response format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_type": "ErrorCategory",
  "error_code": "CAT001",
  "details": {
    "line": 5,
    "column": 10,
    "context": "Additional context if available"
  },
  "suggestions": [
    "Suggestion 1",
    "Suggestion 2"
  ]
}
```

**HTTP Status Codes**:
- `200 OK`: Successful execution (including code errors)
- `400 Bad Request`: Invalid JSON, missing fields
- `500 Internal Server Error`: Backend crash/exception

---

## 12. Frontend Architecture

### 12.1 Frontend Stack

- **Framework**: React 19
- **Build Tool**: Vite
- **State Management**: Zustand
- **Editor**: Monaco Editor
- **Charts**: Recharts
- **Styling**: CSS Modules

### 12.2 State Management

The Zustand store (`frontend/src/store/useStore.js`) manages global application state:

```javascript
const useStore = create((set) => ({
  // Editor state
  code: "",
  setCode: (code) => set({ code }),
  
  // Server status
  serverOnline: true,
  setServerOnline: (status) => set({ serverOnline: status }),
  
  // Execution state
  running: false,
  setRunning: (running) => set({ running }),
  
  // Results from last execution
  result: null,
  setResult: (result) => set({ result }),
  
  // Trust history (last 20 runs)
  trustHistory: [],
  addTrustEntry: (entry) => set((state) => ({
    trustHistory: [...state.trustHistory.slice(-19), entry]
  })),
  
  // Session statistics
  runCount: 0,
  incrementRunCount: () => set((state) => ({
    runCount: state.runCount + 1
  })),
  
  // UI state
  bottomTab: 'terminal',  // 'terminal'|'pipeline'|'ast'|'trust'|'tokens'
  setBottomTab: (tab) => set({ bottomTab: tab }),
  
  // Terminal output
  terminalLines: [],
  addTerminalLine: (line) => set((state) => ({
    terminalLines: [...state.terminalLines, line]
  })),
  clearTerminal: () => set({ terminalLines: [] }),
  
  // Loaded examples
  examples: [],
  setExamples: (examples) => set({ examples })
}));
```

### 12.3 Key Components

#### 12.3.1 Editor Component

```javascript
function Editor() {
  const { code, setCode } = useStore();
  
  return (
    <MonacoEditor
      language="aegis"
      value={code}
      onChange={setCode}
      theme="vs-dark"
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: 'on',
        wordWrap: 'on'
      }}
      onKeyDown={(e) => {
        if (e.ctrlKey && e.key === 'Enter') {
          // Trigger execution
        }
      }}
    />
  );
}
```

**Syntax Highlighting**: Custom AEGIS language definition with:
- Keywords: if, else, while, end, print
- Operators: +, -, *, /, %, ==, !=, <, >, <=, >=
- Comments: # style

#### 12.3.2 PipelineView Component

```javascript
function PipelineView({ result }) {
  if (!result) return <div>No execution yet</div>;
  
  const stages = [
    { name: 'Lexical', status: result.lexical_status },
    { name: 'Syntax', status: result.syntax_status },
    { name: 'Analysis', status: result.analysis_status },
    { name: 'Trust', status: result.trust_status },
    { name: 'Execute (mode 1)', status: result.execute1_status },
    { name: 'Execute (mode 2)', status: result.execute2_status },
    { name: 'Trust Update', status: result.trust_update_status }
  ];
  
  return (
    <div className="pipeline">
      {stages.map((stage, i) => (
        <div key={i} className={`stage ${stage.status}`}>
          <div className="stage-name">{stage.name}</div>
          <div className="stage-icon">
            {stage.status === 'success' && '✓'}
            {stage.status === 'failure' && '✗'}
            {stage.status === 'skipped' && '⊘'}
            {stage.status === 'pending' && '–'}
            {stage.status === 'current' && '○'}
          </div>
        </div>
      ))}
    </div>
  );
}
```

**Stage Status Icons**:
- `✓`: Completed successfully
- `✗`: Failed/error
- `⊘`: Skipped
- `–`: Not yet started
- `○`: Currently executing

#### 12.3.3 ASTViewer Component

```javascript
function ASTViewer({ ast }) {
  if (!ast) return <div>No AST available</div>;
  
  function TreeNode({ node, depth = 0 }) {
    const isLeaf = !node.children || node.children.length === 0;
    const isExpanded = depth < 3;  // Auto-expand first 3 levels
    
    return (
      <div className="tree-node" style={{ marginLeft: `${depth * 20}px` }}>
        <span>{isLeaf ? '└──' : '├──'} </span>
        <span className="node-type">{node.type}</span>
        {node.value && <span className="node-value">({node.value})</span>}
        
        {!isLeaf && (
          <div className="children">
            {node.children?.map((child, i) => (
              <TreeNode key={i} node={child} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    );
  }
  
  return <div className="ast-viewer">
    <TreeNode node={ast} />
  </div>;
}
```

#### 12.3.4 TrustPanel Component

```javascript
function TrustPanel({ history }) {
  return (
    <div className="trust-panel">
      <LineChart
        data={history.slice(-10)}  // Last 10 runs
        margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="run" />
        <YAxis domain={[0, 3]} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="score" stroke="#8884d8" />
        <ReferenceLine
          y={1.0}
          stroke="#ff7300"
          label="Optimization Threshold"
          strokeDasharray="5 5"
        />
      </LineChart>
      
      <table className="trust-history">
        <thead>
          <tr>
            <th>Run</th>
            <th>Score</th>
            <th>Mode</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {history.map((entry, i) => (
            <tr key={i}>
              <td>{entry.run}</td>
              <td>{entry.score.toFixed(2)}</td>
              <td>{entry.mode}</td>
              <td>{entry.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

#### 12.3.5 OutputPanel Component

```javascript
function OutputPanel({ lines }) {
  const terminalRef = useRef(null);
  
  // Auto-scroll to bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [lines]);
  
  return (
    <div className="output-panel" ref={terminalRef}>
      {lines.map((line, i) => (
        <div key={i} className={`line ${line.type}`}>
          <span className="timestamp">[{formatTime(line.ts)}]</span>
          <span className="icon">
            {line.type === 'out' && '›'}
            {line.type === 'err' && '✗'}
            {line.type === 'secerr' && '⚠'}
            {line.type === 'meta' && '─'}
            {line.type === 'info' && '#'}
            {line.type === 'metric' && '≡'}
          </span>
          <span className="text">{line.text}</span>
        </div>
      ))}
    </div>
  );
}
```

**Line Types**:
- `out`: Program output
- `err`: Runtime error
- `secerr`: Security error / rollback
- `meta`: Run separator / summary
- `info`: Informational message
- `metric`: Metrics block

### 12.4 Page Structure

#### 12.4.1 Playground Page (Main IDE)

```
┌─────────────────────────────────────────────────────────┐
│                       Top Bar                          │
│  [Run] [Status: Online] [Menu] [About] [Docs]          │
├─────────────────────┬─────────────────────────────────┤
│      Editor         │      Live Preview / Info        │
│                     │                                 │
│  x = 5              │  ┌─────────────────────────┐   │
│  y = x + 1          │  │ Pipeline                │   │
│  print y            │  │ ✓ Lexical               │   │
│                     │  │ ✓ Syntax                │   │
│                     │  │ ✓ Analysis              │   │
│                     │  │ ○ Trust                 │   │
│                     │  │ – Execution             │   │
│                     │  └─────────────────────────┘   │
├─────────────────────┴─────────────────────────────────┤
│ [Terminal] [Pipeline] [AST] [Tokens] [Trust]          │
├─────────────────────────────────────────────────────────┤
│                  Bottom Panel (resizable)              │
│                  Shows selected tab content            │
└─────────────────────────────────────────────────────────┘
```

#### 12.4.2 Docs Page

Lists the language specification and API documentation.

#### 12.4.3 About Page

Shows project information and contributors.

---

## 13. Testing Methodology

### 13.1 Test Suite Organization

The AEGIS test suite uses pytest with Hypothesis for property-based testing:

```
tests/
├── conftest.py                           # Pytest config, Hypothesis profiles
├── test_foundation.py                    # Basic structure and imports
├── test_lexer.py                         # Lexer unit tests
├── test_lexer_properties.py              # Hypothesis: tokenization properties
├── test_parser.py                        # Parser unit tests
├── test_parser_properties.py             # Hypothesis: parse correctness
├── test_ast.py                           # AST node tests
├── test_interpreter_properties.py        # Hypothesis: execution correctness
├── test_static_analyzer.py               # Static analyzer unit tests
├── test_static_analyzer_properties.py    # Hypothesis: analysis correctness
├── test_trust_manager.py                 # Trust system unit tests
├── test_trust_manager_properties.py      # Hypothesis: trust lifecycle
├── test_runtime_monitor_properties.py    # Hypothesis: monitoring properties
├── test_rollback_unit.py                 # Rollback unit tests
├── test_rollback_properties.py           # Hypothesis: rollback correctness
├── test_optimized_executor.py            # Optimizer unit tests
├── test_optimized_executor_properties.py # Hypothesis: optimization properties
├── test_pipeline_properties.py           # Hypothesis: pipeline behavior
├── test_error_message_properties.py      # Hypothesis: error reporting
├── test_performance_validation.py        # Performance benchmarks
├── test_integration_checkpoint.py        # Integration tests
└── test_final_integration.py             # End-to-end tests
```

### 13.2 Unit Testing Approach

Unit tests validate individual component behavior with known inputs/outputs:

```python
def test_lexer_simple_identifier():
    lexer = Lexer()
    tokens = lexer.tokenize("x")
    assert len(tokens) == 2
    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[0].value == "x"
    assert tokens[1].type == TokenType.EOF

def test_parser_assignment():
    parser = Parser()
    tokens = [
        Token(TokenType.IDENTIFIER, 'x', 1, 1),
        Token(TokenType.ASSIGN, '=', 1, 3),
        Token(TokenType.INTEGER, '5', 1, 5),
        Token(TokenType.EOF, '', 1, 6)
    ]
    ast = parser.parse(tokens)
    assert len(ast) == 1
    assert isinstance(ast[0], AssignmentNode)
    assert ast[0].identifier == 'x'

def test_interpreter_arithmetic():
    interpreter = SandboxedInterpreter()
    context = ExecutionContext()
    ast = [AssignmentNode('x', BinaryOpNode(
        IntegerNode(3), '+', IntegerNode(4)
    ))]
    interpreter.execute(ast, context)
    assert context.variables['x'] == 7
```

### 13.3 Property-Based Testing with Hypothesis

Property-based tests verify that certain properties hold for ALL valid inputs:

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=-2**31, max_value=2**31-1))
def test_lexer_integer_round_trip(n):
    """Tokenizing and parsing any integer produces same value."""
    lexer = Lexer()
    tokens = lexer.tokenize(str(n))
    assert len(tokens) == 2
    assert tokens[0].type == TokenType.INTEGER
    assert tokens[0].value == str(n)

@given(st.lists(st.one_of(
    st.integers(min_value=0, max_value=100),
    st.just('+'),
    st.just('-'),
    st.just('*'),
    st.just('/')
)))
def test_interpreter_semantic_correctness(operations):
    """All valid programs produce deterministic results."""
    # Build AST from operations
    # Execute multiple times
    # Verify outputs are identical
    pass

@given(
    initial_score=st.floats(min_value=0.0, max_value=10.0),
    num_successes=st.integers(min_value=0, max_value=100),
    num_violations=st.integers(min_value=0, max_value=10)
)
def test_trust_score_monotonicity(initial_score, num_successes, num_violations):
    """Trust score increases with successes, decreases with violations."""
    score = TrustScore("test_code", current_score=initial_score)
    
    for _ in range(num_successes):
        metrics = ExecutionMetrics()
        score.add_execution_result(metrics, had_violations=False)
    
    score_after_successes = score.current_score
    assert score_after_successes >= initial_score
    
    for _ in range(num_violations):
        metrics = ExecutionMetrics()
        score.add_execution_result(metrics, had_violations=True)
    
    score_after_violations = score.current_score
    assert score_after_violations < score_after_successes
```

### 13.4 Integration Testing

Integration tests verify components work together correctly:

```python
def test_end_to_end_execution():
    """Complete pipeline from source to output."""
    pipeline = AegisExecutionPipeline()
    
    result = pipeline.execute("""
        x = 5
        y = x + 3
        print y
    """)
    
    assert result.success
    assert '8' in result.output
    assert result.execution_mode == 'interpreted'
    assert result.trust_score == 0.6

def test_trust_progression():
    """Trust increases across multiple executions."""
    pipeline = AegisExecutionPipeline()
    code = "print 42"
    
    # Run 1: Initial trust
    result1 = pipeline.execute(code)
    score1 = result1.trust_score
    
    # Run 2: Trust increases
    result2 = pipeline.execute(code)
    score2 = result2.trust_score
    assert score2 > score1
    
    # Run 3: Reaches optimization threshold
    result3 = pipeline.execute(code)
    score3 = result3.trust_score
    assert score3 > score2
    if score3 >= 1.0:
        assert result3.execution_mode == 'optimized'

def test_rollback_on_violation():
    """Violations in optimized mode trigger rollback."""
    pipeline = AegisExecutionPipeline()
    
    # Build trust with safe code
    safe_code = "x = 5\nprint x"
    for _ in range(3):
        pipeline.execute(safe_code)
    
    # Now execute code that violates
    unsafe_code = "while 1\n  x = x + 1\nend"  # Infinite loop
    result = pipeline.execute(unsafe_code)
    
    # Expect rollback
    assert len(result.rollback_events) > 0
    assert result.trust_score == 0.0
    assert result.execution_mode == 'interpreted'
```

### 13.5 Hypothesis Configuration

```python
# conftest.py
from hypothesis import settings, Verbosity

settings.register_profile("default", max_examples=100)
settings.register_profile("ci", max_examples=1000)
settings.load_profile("default")

# Run with: pytest --hypothesis-profile=ci
```

---

## 14. Performance Characteristics

### 14.1 Benchmarking Methodology

AEGIS performance is measured across three dimensions:

1. **Execution Speed**: Operations per second in both modes
2. **Memory Efficiency**: Bytes allocated during execution
3. **Latency**: Time from program start to output ready

### 14.2 Interpreted Mode Performance

**Baseline measurements** (system-dependent):

```
Program             Instructions  Time (ms)  Ops/sec   Memory
─────────────────────────────────────────────────────────────
x = 5               2            0.05      40,000    64 KB
x = 5; print x      3            0.08      37,500    64 KB
fibonacci(10)       1,245        3.2       389,000   256 KB
nested loops(100)   5,000        12        417,000   512 KB
```

**Performance characteristics**:
- Tree walking interpreter: 100K - 500K ops/sec typical
- Python overhead: ~2-3x slower than native compiled code
- Memory baseline: ~64 KB per execution context
- Startup latency: <1ms (negligible)

### 14.3 Optimized Mode Performance

**With optimizations applied**:

```
Optimization              Base      With Opt   Speedup   Conditions
────────────────────────────────────────────────────────────────────
Constant Folding          100%      70%        1.43x     Literal expressions
Dead Code Elim            100%      85%        1.18x     Unused variables
Variable Propagation      100%      75%        1.33x     Constant assignments
Expression Simplify       100%      90%        1.11x     Algebraic identities
All Combined              100%      40%        2.50x     Typical case
```

**Maximum theoretical speedup**: 3.0x (sum of individual bonuses)  
**Typical real-world speedup**: 2.0x - 2.5x

### 14.4 Cache Impact

Code cache LRU eviction metrics:

```
Configuration    Cache Size  Hit Rate  Time Saved
──────────────────────────────────────────────────
Cold Start       100         0%        0 ms
After 10 runs    100         95%       15-20 ms per hit
High Activity    100         87%       10-15 ms per hit
Cache Full       100         78%       Eviction overhead
```

**Cache Performance**:
- Hit latency: <1ms (direct retrieval)
- Miss latency: 5-10ms (reoptimization)
- Eviction cost: 0.5-1.0ms per entry
- Age-based expiration: 24 hours

### 14.5 Scaling Characteristics

#### 14.5.1 By Program Size

```
Lines of Code  Instructions  Time (interp)  Time (opt)  Speedup
──────────────────────────────────────────────────────────────
5              10            0.02 ms        0.01 ms     2.0x
50             100           0.25 ms        0.10 ms     2.5x
500            1,000         2.5 ms         1.0 ms      2.5x
5,000          10,000        25 ms          10 ms       2.5x
50,000         50,000 (limit) 500 ms       200 ms      2.5x
```

#### 14.5.2 By Complexity

```
Complexity      Characteristic           Performance
──────────────────────────────────────────────────────
O(n)            Linear iterations        Linear scaling
O(n²)           Nested loops             Quadratic scaling
Cyclomatic Cmplx Higher branching        More cache-sensitive
Expression Depth Deeper nesting          Slower evaluation
```

---

## 15. Implementation Details

### 15.1 File Structure and LOC Estimates

| Module | File | LOC | Primary Purpose |
|--------|------|-----|-----------------|
| Lexer | lexer.py | 150 | Tokenization |
| | tokens.py | 80 | Token definitions |
| Parser | parser.py | 250 | Syntax analysis |
| AST | nodes.py | 200 | Node definitions |
| | visitor.py | 50 | Visitor pattern |
| | serializer.py | 100 | AST to dict |
| | pretty_printer.py | 80 | Human-readable output |
| Interpreter | interpreter.py | 300 | Execution engine |
| | static_analyzer.py | 250 | Pre-execution checks |
| | context.py | 100 | Execution state |
| Runtime | monitor.py | 200 | Metrics and violations |
| | rollback.py | 150 | Recovery mechanism |
| Trust | trust_manager.py | 200 | Trust lifecycle |
| | trust_policy.py | 50 | Policy constants |
| Compiler | optimizer.py | 300 | AST optimization |
| | cache.py | 150 | Code cache |
| VM | bytecode.py | 100 | Bytecode definitions |
| | compiler.py | 200 | Bytecode generation |
| | vm.py | 250 | Stack-based execution |
| IR | tac.py | 150 | Three-address code |
| Errors | errors.py | 150 | Error system |
| Pipeline | pipeline.py | 400 | Main orchestration |
| | | | |
| **Core Total** | | **3,900** | |
| | | | |
| Backend | app.py | 100 | Flask setup |
| | pipeline.py | 250 | Backend wrapper |
| | helpers.py | 100 | Utilities |
| | execute.py | 80 | Execute endpoint |
| | analyze.py | 60 | Analyze endpoint |
| | tokenize.py | 60 | Tokenize endpoint |
| | health.py | 60 | Health endpoint |
| | | | |
| **Backend Total** | | **710** | |
| | | | |
| Frontend | App.jsx | 200 | Main component |
| | Editor.jsx | 150 | Editor integration |
| | PipelineView.jsx | 200 | Pipeline visualization |
| | ASTViewer.jsx | 180 | AST display |
| | OutputPanel.jsx | 150 | Terminal output |
| | TrustPanel.jsx | 180 | Trust visualization |
| | TokenPanel.jsx | 120 | Token display |
| | useStore.js | 150 | State management |
| | api.js | 100 | API client |
| | | | |
| **Frontend Total** | | **1,330** | |
| | | | |
| Tests | test_*.py | 3,500 | Test coverage |
| | | | |
| **Total Project** | | **~9,000** | |

### 15.2 Key Data Structures

#### 15.2.1 Token

```python
@dataclass
class Token:
    type: TokenType      # Enum: IDENTIFIER, INTEGER, PLUS, ...
    value: str          # Actual text: "x", "5", "+", ...
    line: int           # 1-based line number
    column: int         # 1-based column number
```

#### 15.2.2 AST Nodes

```python
class ASTNode(ABC):
    @abstractmethod
    def accept(self, visitor):
        pass
    
    @abstractmethod
    def get_children(self):
        pass

@dataclass
class IntegerNode(ASTNode):
    value: int

@dataclass
class IdentifierNode(ASTNode):
    name: str

@dataclass
class BinaryOpNode(ASTNode):
    left: ASTNode
    operator: str           # '+', '-', '*', '/', '%', '==', '!=', ...
    right: ASTNode

@dataclass
class AssignmentNode(ASTNode):
    identifier: str
    expression: ASTNode

@dataclass
class PrintNode(ASTNode):
    expression: ASTNode

@dataclass
class IfNode(ASTNode):
    condition: ASTNode
    then_body: List[ASTNode]
    else_body: Optional[List[ASTNode]]

@dataclass
class WhileNode(ASTNode):
    condition: ASTNode
    body: List[ASTNode]
```

#### 15.2.3 ExecutionContext

```python
@dataclass
class ExecutionContext:
    variables: Dict[str, int]           # Variable storage
    execution_mode: ExecutionMode       # INTERPRETED or OPTIMIZED
    code_hash: str                      # SHA-256[:16]
    output_buffer: List[str]            # Program output
```

#### 15.2.4 ExecutionMetrics

```python
@dataclass
class ExecutionMetrics:
    instruction_count: int
    memory_usage: int
    execution_time: float
    operations_performed: List[str]
    violations_detected: List[SecurityViolation]
    variables_accessed: List[str]
    arithmetic_operations: int
    assignment_operations: int
    print_operations: int
```

#### 15.2.5 TrustScore

```python
@dataclass
class TrustScore:
    code_hash: str
    current_score: float                # [0.0, 10.0]
    execution_count: int
    successful_executions: int
    violation_count: int
    last_execution: Optional[datetime]
    last_violation: Optional[datetime]
    first_execution: Optional[datetime]
    trust_history: List[Dict]           # Last 50 entries
```

### 15.3 Algorithm Complexity

#### 15.3.1 Lexical Analysis

- **Time**: O(n) where n = source code length
- **Space**: O(m) where m = token count
- **Approach**: Single-pass character scanning

#### 15.3.2 Syntax Analysis

- **Time**: O(m) where m = token count
- **Space**: O(d) where d = maximum expression depth
- **Approach**: Recursive descent parsing

#### 15.3.3 Static Analysis

- **Time**: O(n) where n = AST node count
- **Space**: O(n) for symbol table
- **Approach**: Visitor pattern tree walk

#### 15.3.4 Interpretation

- **Time**: O(i) where i = instruction count (≤50,000)
- **Space**: O(v) where v = variable count
- **Approach**: Tree-walking interpreter with visitor pattern

#### 15.3.5 AST Optimization

- **Time**: O(n log n) for dead code elimination sorting
- **Space**: O(n) for transformed AST
- **Approach**: Multiple passes with caching

#### 15.3.6 Trust Lookup

- **Time**: O(1) hash table lookup
- **Space**: O(m) where m = code hashes seen
- **Persistence**: O(m) JSON file I/O

---

## 16. Security Considerations and Limitations

### 16.1 Achieved Security Guarantees

1. **Memory Safety**: No buffer overflows, no arbitrary memory access
2. **Resource Bounds**: Instruction and iteration limits prevent infinite loops
3. **Type Safety**: All values are 32-bit integers, no type confusion
4. **Namespace Isolation**: Each execution has separate variable scope
5. **No System Access**: No file I/O, network, or process spawning

### 16.2 Security Limitations

1. **Timing Attacks**: Execution time can leak information (not addressed)
2. **Floating Point**: Not supported; no precision attacks possible
3. **Large Integer Sets**: Trust model doesn't differentiate code types
4. **Replay Attacks**: Trust scores persist without freshness checks
5. **Distributed Systems**: No distributed trust coordination

### 16.3 Threat Assumptions

AEGIS assumes:
- Backend server is trusted
- Network between frontend and backend is secure (HTTPS in production)
- User doesn't have admin access to server
- Code origin is untrusted but not malicious beyond defined threats

---

## Conclusion

AEGIS represents a novel approach to secure code execution through adaptive trust-based execution modes. By reversing conventional compiler design and defaulting to maximum safety while selectively optimizing proven-safe code, the system achieves both strong security guarantees and practical performance.

The seven-stage execution pipeline provides transparency and control at every step. The trust model demonstrates that security and performance need not be in conflict—rather, they can be complementary through evidence-based decision making.

This documentation serves both as a technical reference for implementers and researchers and as a blueprint for security-first language design in the modern era of code evaluation and automated systems.

---

**Document metadata:**
- Repository: https://github.com/AEGIS-Team/AEGIS
- Status: Stable (v2.0.0 Backend, v1.0.0 Core)
- Last revision: April 24, 2026
- Maintainers: AEGIS Development Team

---

**End of Technical Documentation**
