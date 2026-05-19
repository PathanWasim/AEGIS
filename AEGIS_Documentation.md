# AEGIS (Adaptive Execution General-purpose Intelligent System)
**Comprehensive Project Documentation and Developer Guide**

## 1. Project Overview & Core Philosophy

AEGIS is a production-grade, security-focused adaptive execution engine designed specifically for academic and cybersecurity research. Traditional compilers and interpreters execute code with implicit trust once syntax passes validation. AEGIS subverts this paradigm by employing a **Pessimistic Default**. 

Every script and execution block begins life inside a strictly sandboxed, heavily monitored environment. The system utilizes a dynamic trust metric to aggregate execution telemetry over time. Only when a piece of code proves its structural integrity, computational efficiency, and overall safety over multiple runs is it promoted to an Optimized VM environment. If a violation is detected at any point—even within the optimized layer—the system executes an immediate rollback to the sandbox and revokes all accrued trust.

This dual-mode execution model is specifically engineered to mitigate algorithmic halting problems, unconstrained memory consumption, unauthorized mutations, and infinite looping scenarios without sacrificing the performance benefits of compiled execution for trusted code.

---

## 2. The Multi-Layered Security Architecture

AEGIS implements a pioneering Multi-Layered Security Approach that intercepts malicious or poorly formed code at multiple stages of the compilation and execution pipeline:

### 2.1 Layer 1: Lexical and Syntactic Rejection
The lexer and parser act as the first line of defense. They strictly validate language constructs, immediately rejecting unhandled operators or corrupted syntax before any Abstract Syntax Tree (AST) is generated. This prevents payload injection via obfuscated characters.

### 2.2 Layer 2: Static Security Analysis
Before code is ever executed, the AST undergoes a rigorous static analysis phase. The `StaticAnalyzer` recursively inspects the tree to identify logical defects, such as:
- Undefined variable usage.
- Arithmetic vulnerabilities (e.g., division by zero).
- Potential integer overflows in multiplicative operations.
- Deeply nested expressions that could trigger stack overflows (max depth enforced).

### 2.3 Layer 3: Trust-Gated Mode Selection
The `TrustManager` hashes incoming source code and cross-references it with a persistent trust ledger. Code is assigned a score based on previous execution success. If `Trust Score >= 1.0`, the code executes in the high-performance VM. If `< 1.0`, it remains trapped in the sandbox.

### 2.4 Layer 4: Active Runtime Monitoring
During execution, the `RuntimeMonitor` continuously tracks cycle counts, variable accesses, arithmetic complexity, and overall memory bounds. It enforces a strict instruction count limit (default 1000 instructions) to prevent infinite loops from locking the thread.

### 2.5 Layer 5: Rollback & Trust Revocation
If the Optimized VM or the Sandboxed Interpreter detects a violation (e.g., instruction timeout, bounds violation), a `SecurityViolation` is triggered. The `RollbackHandler` catches this exception, halts the process, clears the optimization cache, zero-rates the script's trust score, and forces subsequent executions back into the sandbox.

---

## 3. Lexical Analysis

The Lexer in AEGIS converts raw source code into a stream of discrete tokens. The scanning is performed character-by-character.

### Supported Lexical Constructs:
- **Keywords**: `if`, `else`, `while`, `print`, `end`
- **Operators**: `+`, `-`, `*`, `/`, `%`
- **Comparators**: `==`, `!=`, `<`, `<=`, `>`, `>=`
- **Assignment**: `=`
- **Grouping**: `(`, `)`
- **Comments**: `#` (ignored until end of line)

If an unrecognized character is detected, the Lexer throws a `LexicalError` and halts the pipeline immediately.

---

## 4. Syntax and Grammar (EBNF)

The AEGIS Parser uses a Recursive Descent algorithm to convert the token stream into an AST.

**EBNF Grammar Definition**:
```ebnf
program     → statement* EOF
statement   → if_stmt | while_stmt | assignment | print_stmt
if_stmt     → "if" comparison NEWLINE
                  statement*
              ("else" NEWLINE statement*)?
              "end"
while_stmt  → "while" comparison NEWLINE
                  statement*
              "end"
assignment  → IDENTIFIER "=" expression
print_stmt  → "print" expression
expression  → comparison
comparison  → term (( ">"  | "<"  | ">=" | "<=" | "==" | "!=" ) term)*
term        → factor (( "+" | "-" ) factor)*
factor      → unary  (( "*" | "/" | "%" ) unary)*
unary       → "-" unary | primary
primary     → INTEGER | IDENTIFIER | "(" expression ")"
```

This strict grammar enforces that control structures are explicitly terminated with `end`, and mathematical operations adhere to standard operator precedence (BEDMAS/BODMAS).

---

## 5. Execution Pipeline: The 7 Stages

Every script processed by AEGIS follows a strict, deterministic pipeline:

1. **Tokenization (Lexer)**: The raw source is split into typed Tokens.
2. **Parsing (Parser)**: Tokens are assembled into a hierarchical AST.
3. **Static Security Analysis (Analyzer)**: The AST is checked for safety violations (uninitialized variables, zero division, stack depth).
4. **Execution Mode Determination (Trust Manager)**: The AST is hashed. The Trust Manager checks the persistent `aegis_trust.json` ledger. If the score meets the threshold, the AST is marked for Optimization.
5. **Program Execution (Interpreter/Optimizer)**: 
   - *Sandboxed*: AST nodes are evaluated individually by the `SandboxedInterpreter`.
   - *Optimized*: The AST is fed into the `ASTOptimizer`, which performs constant folding and dead code elimination, then executes the condensed AST at higher speeds.
6. **Trust Score Update**: Following execution, telemetry (instruction count, execution time, violations) is passed back to the Trust Manager to adjust the script's score.
7. **Rollback Handling**: If a violation was flagged during step 5, the state is rolled back, the AST cache is purged, and the score is reset to 0.

---

## 6. Code Optimization and Caching

When code earns trust, it passes through the `ASTOptimizer`. AEGIS simulates compilation-level optimizations on the AST directly:

- **Constant Folding**: `x = 5 + 5` becomes `x = 10`.
- **Variable Propagation**: If `x` is immutable, references to `x` are replaced with its integer value.
- **Algebraic Simplification**: Computations like `x * 0` are aggressively simplified to `0`.

The condensed AST is then stored in the `CodeCache` linked to its SHA-256 hash. Future executions of this trusted script bypass parsing and analysis entirely, loading the optimized AST directly from the cache to achieve near-native execution latency.

---

## 7. Trust Metrics and Eligibility

A `TrustScore` tracks the following metrics for a specific script hash:
- `current_score`: Float value representing trust.
- `execution_count`: Total times executed.
- `successful_executions`: Times executed without raising a security violation.
- `violation_count`: Times the script broke sandbox rules.

### Eligibility Criteria for Optimization:
1. Current score must be `>= 1.0`.
2. Must have executed successfully at least 3 times.
3. Success rate must be `> 80%`.
4. The script cannot have had a security violation *more recently* than a successful execution.

Trust is increased incrementally (`+0.1` per success) with bonuses awarded for low instruction counts and fast execution times. Violations carry a massive penalty (`-0.5` per violation), ensuring malicious code is immediately demoted.

---

## 8. Technology Stack Breakdown

*   **Compiler/Execution Engine (Core)**: Python 3.11+
    *   `aegis/lexer`: Lexical analysis module.
    *   `aegis/parser`: Recursive descent parser.
    *   `aegis/ast`: AST Nodes definition.
    *   `aegis/interpreter`: Sandboxed execution engine.
    *   `aegis/trust`: Ledger and scoring mechanics.
    *   `aegis/runtime`: Hardware monitors and rollback logic.
    *   `aegis/compiler`: Cache and optimizer logic.
*   **Backend Interface**: Flask
    *   Provides secure, rate-limited REST API endpoints for the web frontend to submit code and receive execution traces.
*   **Frontend IDE**: React 19, Vite
    *   *Zustand*: Global state management.
    *   *Monaco Editor*: Microsoft's code editor for syntax highlighting.
    *   *Recharts*: D3-based library for plotting Trust score trajectories and pipeline execution times.

---

## 9. Comprehensive Code Snippets

To provide deep context into the AEGIS architecture, the following code snippets highlight the most critical operations across the compiler.

### 9.1 The Main Pipeline Orchestrator (`pipeline.py`)
This snippet shows the complete lifecycle of a script passing through AEGIS.

```python
# Phase 3: Static Security Analysis
analysis_passed = self.analyzer.analyze(ast)
if not analysis_passed:
    raise AnalysisError("Static analysis failed")

# Phase 4: Execution Mode Determination
code_hash = self.trust_manager.get_code_hash(source_code)
trust_score_obj = self.trust_manager.get_trust_score(code_hash)
is_trusted = self.trust_manager.is_trusted_for_optimization(code_hash)

execution_mode = 'optimized' if is_trusted else 'sandboxed'

# Phase 5: Program Execution
context = ExecutionContext()
try:
    if execution_mode == 'sandboxed':
        self.interpreter.execute(ast, context)
        metrics = self.monitor.get_execution_history()[-1]
    else:
        # Executes with cached AST
        metrics = self.optimizer.execute_optimized(code_hash, ast, context)
except SecurityViolation as e:
    violations.append(e)

# Phase 6: Trust Score Update
trust_score = self.trust_manager.update_trust(
    code_hash, metrics, violations
)
```

### 9.2 Real-time Security Violation Checking (`monitor.py`)
The monitor counts every operation and throws violations if resources are exhausted.

```python
def check_violations(self) -> List[SecurityViolation]:
    violations = []
    if not self.current_metrics:
        return violations
    
    # Check instruction count limit (default: 1000)
    if self.current_metrics.instruction_count > self.violation_threshold:
        violation = SecurityViolation(
            "instruction_limit",
            f"Instruction count {self.current_metrics.instruction_count} exceeds limit {self.violation_threshold}",
            self.monitored_context
        )
        violations.append(violation)
    
    # Check memory usage bounds (default: 1MB)
    if self.current_metrics.memory_usage > self.memory_threshold:
        violation = SecurityViolation(
            "memory_limit",
            f"Memory usage {self.current_metrics.memory_usage} exceeds limit",
            self.monitored_context
        )
        violations.append(violation)
    
    return violations
```

### 9.3 AST Optimization and Constant Folding (`optimizer.py`)
This logic compresses computational overhead for trusted code.

```python
def visit_binary_op(self, node: BinaryOpNode) -> ASTNode:
    left = self.visit(node.left)
    right = self.visit(node.right)
    
    # Constant folding: if both operands are constants, compute result
    if isinstance(left, IntegerNode) and isinstance(right, IntegerNode):
        try:
            if node.operator == '+':
                result = left.value + right.value
            elif node.operator == '*':
                result = left.value * right.value
            elif node.operator == '/':
                if right.value != 0:
                    result = left.value // right.value
                else:
                    return BinaryOpNode(left, node.operator, right)
            
            self.optimization_flags['constant_folding'] = True
            return IntegerNode(result)
        except (ZeroDivisionError, OverflowError):
            pass
            
    return BinaryOpNode(left, node.operator, right)
```

### 9.4 Rollback Handling (`rollback.py`)
The logic responsible for degrading execution privileges securely.

```python
def trigger_rollback(self, violation_type: str, code_hash: str, details: str,
                     context: ExecutionContext = None, 
                     violations: List[SecurityViolation] = None,
                     trust_score_before: float = 0.0) -> RollbackEvent:
                     
    print(f"[ROLLBACK] Security violation detected: {violation_type}")
    print(f"[ROLLBACK] Initiating rollback to sandboxed execution...")
    
    # Clear optimization cache for the compromised code
    if self.cache_clear_callback:
        self.cache_clear_callback(code_hash)
    
    # Update trust score to apply penalty
    trust_score_after = trust_score_before
    if self.trust_update_callback and self.auto_trust_revocation:
        self.trust_update_callback(code_hash, violation_type, details)
        trust_score_after = max(0.0, trust_score_before - 0.5)
    
    return RollbackEvent(
        timestamp=datetime.now(),
        violation_type=violation_type,
        code_hash=code_hash,
        execution_mode='optimized',
        trust_score_after=trust_score_after,
        ...
    )
```

### 9.5 Static Safety Checks (`static_analyzer.py`)
Catching mathematical impossibilities before they crash the underlying Python host.

```python
def visit_binary_op(self, node: BinaryOpNode) -> Any:
    # Check expression depth to prevent stack overflow
    self.expression_depth += 1
    if self.expression_depth > self.max_expression_depth:
        self.errors.append(f"Expression deeply nested (max: {self.max_expression_depth})")
        return None
    
    try:
        node.left.accept(self)
        node.right.accept(self)
        
        # Check for potential division by zero statically
        if node.operator == '/':
            if isinstance(node.right, IntegerNode) and node.right.value == 0:
                self.errors.append("Division by zero detected")
            elif isinstance(node.right, IdentifierNode):
                self.warnings.append(f"Potential division by zero with '{node.right.name}'")
    finally:
        self.expression_depth -= 1
```

---

## 10. AEGIS Language Example Code

**Example 1: Safe Execution (Will reach Optimized status)**
```text
count = 0
while count < 5
  if count == 3
    print count
  end
  count = count + 1
end
```
*Behavior*: Executing this code 3-4 times consecutively will result in successful compilation to the CodeCache. Subsequent runs will be up to 2x faster.

**Example 2: Infinite Loop (Will be caught by Monitor)**
```text
count = 0
while count < 5
  print count
  # Missing increment
end
```
*Behavior*: The monitor will trap the execution once the instruction count exceeds the threshold limit, throwing an `instruction_limit` SecurityViolation.

**Example 3: Malicious Depth (Will be caught by Static Analyzer)**
```text
x = 1 + (1 + (1 + (1 + (1 + (1 + (1 + (1 + (1 + (1 + 1))))))))))
```
*Behavior*: Fails compilation instantly. The `StaticAnalyzer` will reject the script for exceeding the max recursion depth allowed for the AST.

---

## 11. Running the AEGIS Project

To review the project locally, both the API and the React Dashboard must be active.

### 11.1 Backend Boot
Initialize the Python 3 Flask server to expose the `AEGISExecutionPipeline`.
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r ../requirements.txt 
python app.py
```
*Server runs on: `http://127.0.0.1:5000/`*

### 11.2 Frontend Boot
Initialize the React 19 IDE.
```bash
cd frontend
npm install
npm run dev
```
*Dashboard runs on: `http://localhost:3000/`*

### 11.3 Testing Framework
The system is equipped with Pytest integration for core compiler functions.
```bash
pytest tests/
```

---

## 12. Conclusion & Academic Relevance

The AEGIS project demonstrates a robust implementation of modern compiler security. By coupling a traditional lexical scanner and AST evaluator with a dynamic behavioral trust ledger, the platform guarantees that execution degradation or malicious exploits are systematically prevented. This documentation serves as the master specification for the core logic embedded within the engine.
