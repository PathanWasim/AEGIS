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

## Usage

### Command Line Execution

```bash
# Execute a program file
python main.py program.aegis

# Interactive mode
python main.py --interactive

# Batch execution mode
python main.py --batch file1.aegis file2.aegis

# Verbose output with detailed logging
python main.py --verbose program.aegis

# Show system status and statistics
python main.py --status

# Show help
python main.py --help
```

### Command Line Options

- `--interactive, -i`: Start interactive REPL mode
- `--batch, -b`: Execute multiple files in sequence
- `--verbose, -v`: Enable detailed execution logging
- `--status, -s`: Display system status and trust statistics
- `--trust-file FILE`: Specify custom trust persistence file
- `--help, -h`: Show help message

### Interactive Mode Example

```
$ python main.py --interactive
[AEGIS] Starting interactive mode
[AEGIS] Trust file: .aegis_trust.json
[AEGIS] Type 'help' for commands, 'exit' to quit

aegis> x = 10
[MODE] Interpreted Execution
[TRUST] Score = 0.1 (10 successful executions needed for optimization)

aegis> y = x + 5  
[MODE] Interpreted Execution
[TRUST] Score = 0.2 (8 successful executions needed for optimization)

aegis> print y
15
[MODE] Interpreted Execution  
[TRUST] Score = 0.3 (7 successful executions needed for optimization)

# After multiple safe executions...
aegis> result = x * y
[MODE] Optimized Execution (2.1x speedup)
[TRUST] Score = 1.2 (trusted code)

aegis> status
=== AEGIS System Status ===
Execution Mode: Optimized
Trust Score: 1.2
Total Executions: 12
Successful Executions: 12
Violations: 0
Cache Entries: 3
Optimization Ratio: 2.1x

aegis> help
Available commands:
  help     - Show this help message
  status   - Display system status
  reset    - Reset trust score to 0
  clear    - Clear execution history
  exit     - Exit interactive mode
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

## Performance Characteristics

### Execution Modes Performance

**Interpreted Mode (Default):**
- Complete safety guarantees
- Full sandboxing and monitoring
- Baseline execution speed
- Zero optimization overhead

**Optimized Mode (Trust-Based):**
- ~2.1x average speedup over interpreted mode
- Cached AST compilation and execution paths
- Constant folding and expression simplification
- Dead code elimination simulation
- Continued security monitoring

### Trust Building Timeline

```
Executions:  1    2    3    4    5    6    7    8    9    10   11+
Trust Score: 0.1  0.2  0.3  0.4  0.5  0.6  0.7  0.8  0.9  1.0  1.1+
Mode:        Interpreted ────────────────────────────────────→ Optimized
```

### Benchmark Results

Example performance comparison for arithmetic-heavy programs:

```
Program: Fibonacci calculation (n=20)
Interpreted Mode:  ~1.2ms execution time
Optimized Mode:    ~0.6ms execution time  
Speedup:           2.0x

Program: Complex arithmetic expressions
Interpreted Mode:  ~0.8ms execution time
Optimized Mode:    ~0.35ms execution time
Speedup:           2.3x

Program: Variable-heavy assignments  
Interpreted Mode:  ~0.5ms execution time
Optimized Mode:    ~0.25ms execution time
Speedup:           2.0x
```

*Note: Performance numbers are simulated for academic demonstration*

## Security Model

### Static Analysis Checks
- **Undefined variable detection** - Prevents use of uninitialized variables
- **Arithmetic overflow prevention** - Warns about potential integer overflow
- **Division by zero detection** - Catches literal division by zero at compile time
- **Expression validation** - Ensures well-formed expressions within depth limits
- **Type safety enforcement** - Validates identifier formats and usage

### Runtime Monitoring
- **Instruction count limits** - Prevents infinite loops and runaway execution
- **Memory usage tracking** - Monitors variable storage and prevents excessive usage
- **Operation validation** - Validates all arithmetic operations at runtime
- **Violation detection** - Real-time detection of security policy violations
- **Execution metrics** - Comprehensive statistics collection

### Error Handling System

AEGIS provides comprehensive error reporting with categorized, descriptive messages:

#### Error Categories
- **[LEXICAL]** - Invalid characters or token formation errors
- **[SYNTAX]** - Grammar violations and parsing errors  
- **[SEMANTIC]** - Undefined variables and type errors
- **[RUNTIME]** - Division by zero and execution errors
- **[SECURITY]** - Policy violations and security breaches

#### Error Message Format
```
[CATEGORY] [ERROR_CODE]
Error description with context
  Location: line X, column Y
  Token: 'problematic_token'
  Variables: {current_state}
  Suggestions:
    - Specific actionable advice
    - Alternative approaches
    - Common fix patterns
```

#### Example Error Messages
```bash
# Undefined variable error
[SEMANTIC] [SEM001]
Undefined variable: counter
  Token: 'counter'
  Suggestions:
    - Define variable 'counter' before using it
    - Check for typos in variable names
    - Ensure variable assignments come before usage

# Division by zero error  
[RUNTIME] [RUN001]
Division by zero detected
  Variables: x=10, y=0
  Suggestions:
    - Ensure divisor is not zero
    - Add conditional checks before division
    - Use non-zero values for division
```

### Rollback Triggers
- **Runtime errors** - Division by zero, overflow, invalid operations
- **Security violations** - Policy breaches, resource limit exceeded
- **Static analysis failures** - Undefined variables, invalid expressions
- **System errors** - Internal failures, corruption detection

### Trust Persistence
- Trust scores are automatically saved to `.aegis_trust.json`
- Scores persist across program runs and sessions
- Trust can be manually reset or cleared
- Multiple programs can have independent trust scores

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
- [x] Lexical analysis (Lexer)
- [x] Syntax analysis (Parser + AST)  
- [x] Static security analysis
- [x] Sandboxed interpreter
- [x] Runtime monitoring
- [x] Trust management
- [x] Optimized execution
- [x] Rollback handling
- [x] System integration
- [x] Comprehensive error handling
- [ ] Documentation and examples (in progress)

## Testing Strategy

AEGIS uses a comprehensive testing approach with **237 total tests**:

### Test Categories

**Unit Tests (150+ tests):**
- Component-specific behavior validation
- Edge case handling and error conditions
- API contract verification
- Individual module functionality

**Property-Based Tests (15 properties):**
- Universal correctness properties using Hypothesis
- Randomized input validation across large test spaces
- Round-trip consistency verification
- Semantic equivalence between execution modes

**Integration Tests (8 tests):**
- End-to-end system validation
- Component interaction verification
- Pipeline execution completeness
- Cross-component data flow

**Security Tests:**
- Violation detection and rollback validation
- Trust score lifecycle management
- Error handling and recovery
- Rollback state consistency

### Property-Based Test Coverage

1. **Property 1:** Tokenization Round-Trip Consistency
2. **Property 2:** Parsing Round-Trip Consistency  
3. **Property 3:** Arithmetic Expression Correctness
4. **Property 4:** Variable Assignment Consistency
5. **Property 5:** Print Statement Output Correctness
6. **Property 6:** Static Analysis Undefined Variable Detection
7. **Property 7:** Execution State Isolation
8. **Property 8:** Trust Score Lifecycle Management
9. **Property 9:** Execution Mode Transition Correctness
10. **Property 10:** Semantic Equivalence Between Execution Modes
11. **Property 11:** Runtime Monitoring Completeness
12. **Property 12:** Rollback State Consistency
13. **Property 13:** Error Message Descriptiveness
14. **Property 14:** Pipeline Execution Completeness
15. **Property 15:** Console Output Visibility

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_lexer*.py -v          # Lexer tests
pytest tests/test_parser*.py -v         # Parser tests  
pytest tests/test_interpreter*.py -v    # Interpreter tests
pytest tests/test_*_properties.py -v    # Property-based tests
pytest tests/test_integration*.py -v    # Integration tests

# Run with coverage
pytest tests/ --cov=aegis --cov-report=html

# Run property tests with more examples
pytest tests/test_*_properties.py --hypothesis-max-examples=1000

# Run tests with detailed output
pytest tests/ -v --tb=long
```

### Test Results
```
================================ test session starts =================================
platform win32 -- Python 3.10.0, pytest-8.4.2, pluggy-1.6.0
collected 237 items

tests/test_ast.py ........................                              [ 10%]
tests/test_error_message_properties.py ......                           [ 12%]
tests/test_foundation.py ...........                                    [ 17%]
tests/test_integration_checkpoint.py ........                           [ 20%]
tests/test_interpreter_properties.py ...........                        [ 25%]
tests/test_lexer.py ......................                              [ 34%]
tests/test_lexer_properties.py .......                                  [ 37%]
tests/test_optimized_executor.py ....................                   [ 45%]
tests/test_optimized_executor_properties.py ......                      [ 48%]
tests/test_parser.py .............................                      [ 60%]
tests/test_parser_properties.py ........                                [ 64%]
tests/test_pipeline_properties.py .....                                 [ 66%]
tests/test_rollback_properties.py ...                                   [ 67%]
tests/test_rollback_unit.py ......                                      [ 70%]
tests/test_runtime_monitor_properties.py .....                          [ 72%]
tests/test_static_analyzer.py ...........................               [ 83%]
tests/test_static_analyzer_properties.py ........                       [ 86%]
tests/test_trust_manager.py .........................                   [ 97%]
tests/test_trust_manager_properties.py ......                           [100%]

============================ 237 passed in 18.60s ============================
```

## Academic Context

This project is designed for **Compiler Design coursework** and demonstrates:

- **Lexical and Syntax Analysis:** Traditional compiler front-end
- **Security-First Design:** Novel execution model prioritizing safety
- **Runtime Systems:** Monitoring, trust management, and adaptive execution
- **System Architecture:** Component interaction and data flow

**Important Note:** Native compilation is simulated for academic demonstration. This is not a production compiler but an educational tool for understanding compiler concepts and security-adaptive execution models.

## Troubleshooting

### Common Issues

**Q: Program fails with "Undefined variable" error**
```
[SEMANTIC] [SEM001]
Undefined variable: x
```
**A:** Variables must be defined before use. Check for typos and ensure assignments come before usage.

**Q: Trust score not increasing**
```
[TRUST] Score = 0.1 (no change)
```
**A:** Trust only increases with successful executions. Fix any errors first, then run the program multiple times.

**Q: Division by zero in optimized mode**
```
[SECURITY] Rollback triggered: Division by zero
[MODE] Switched to Interpreted Execution
[TRUST] Score reset to 0.0
```
**A:** This is expected behavior. The system detected a violation and rolled back to safe mode. Fix the division by zero and rebuild trust.

**Q: "Expression too deeply nested" error**
```
[SEMANTIC] Expression too deeply nested (max depth: 10)
```
**A:** Simplify complex expressions by breaking them into multiple assignment statements.

### Debug Mode

Enable verbose logging for detailed execution information:

```bash
python main.py --verbose program.aegis
```

This provides:
- Detailed tokenization output
- AST structure visualization  
- Static analysis reports
- Runtime monitoring data
- Trust score calculations
- Optimization decisions

## Limitations

### Language Limitations
- **Toy Language:** Limited to basic arithmetic and variables for academic demonstration
- **Integer-Only:** No support for strings, floats, arrays, or complex data types
- **No Control Flow:** No if/else statements, loops, or functions
- **No I/O Operations:** Restricted to prevent security issues (only print output)
- **No User Input:** No ability to read from stdin or files

### System Limitations  
- **Simulated Compilation:** No actual machine code generation - optimizations are simulated
- **Academic Scope:** Designed for learning compiler concepts, not production use
- **Single-Threaded:** No concurrency or parallel execution support
- **Memory Model:** Simplified variable storage without advanced memory management
- **No Modules:** No import/export system or code organization features

### Security Limitations
- **Simplified Threat Model:** Focuses on basic arithmetic safety, not comprehensive security
- **No Network Security:** No consideration of network-based attacks
- **Limited Resource Control:** Basic monitoring without advanced resource management
- **Trust Model Simplicity:** Basic score-based system without sophisticated analysis

### Performance Limitations
- **Interpreter Overhead:** Significant performance cost in interpreted mode
- **Simulated Optimizations:** Performance improvements are simulated, not real
- **No Advanced Optimizations:** Missing loop unrolling, vectorization, etc.
- **Cache Limitations:** Simple AST caching without advanced compilation techniques

These limitations are intentional design choices to keep the project focused on demonstrating core compiler and security concepts within an academic context.

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