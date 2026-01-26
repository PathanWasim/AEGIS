# AEGIS Example Programs

This directory contains example programs that demonstrate various features and capabilities of the AEGIS system. Each example is designed to showcase specific aspects of the security-first execution model.

## Running Examples

```bash
# Run any example program
python main.py examples/basic_math.aegis

# Run with verbose output to see detailed execution information
python main.py --verbose examples/trust_demo.aegis

# Run in interactive mode to experiment
python main.py --interactive
```

## Example Programs

### 1. `basic_math.aegis` - Basic Arithmetic Operations
**Purpose:** Introduction to AEGIS syntax and basic operations
**Features Demonstrated:**
- Variable assignment
- Arithmetic operations (+, -, *, /)
- Print statements
- Simple program structure

**Expected Output:**
```
30
200
```

### 2. `trust_demo.aegis` - Trust Building Demonstration
**Purpose:** Show how trust scores increase with successful executions
**Features Demonstrated:**
- Trust score progression
- Transition from interpreted to optimized execution
- Safe operation patterns

**Usage:** Run this program multiple times to see trust building:
```bash
# First run - interpreted mode
python main.py examples/trust_demo.aegis

# After 10+ successful runs - optimized mode
python main.py examples/trust_demo.aegis
```

### 3. `security_violation_demo.aegis` - Security Violation and Rollback
**Purpose:** Demonstrate rollback behavior when security violations occur
**Features Demonstrated:**
- Runtime security violation detection
- Automatic rollback to interpreted mode
- Trust score reset after violations
- Division by zero handling

**Expected Behavior:**
- If run in optimized mode, triggers rollback
- Trust score resets to 0.0
- System switches to interpreted mode

### 4. `undefined_variable_demo.aegis` - Static Analysis Error Detection
**Purpose:** Show static analysis catching undefined variables
**Features Demonstrated:**
- Static analysis phase error detection
- Comprehensive error messages with suggestions
- Prevention of unsafe code execution

**Expected Output:**
```
[SEMANTIC] [SEM001]
Undefined variable: undefined_var
  Token: 'undefined_var'
  Suggestions:
    - Define variable 'undefined_var' before using it
    - Check for typos in variable names
    - Ensure variable assignments come before usage
```

### 5. `complex_arithmetic.aegis` - Complex Expression Handling
**Purpose:** Demonstrate AEGIS handling of complex arithmetic expressions
**Features Demonstrated:**
- Multiple arithmetic operations
- Expression evaluation order
- Variable reuse in calculations
- Optimization benefits for computation-heavy code

**Expected Output:**
```
38
67
18
12
135
```

### 6. `trust_building_progression.aegis` - Complete Trust Lifecycle
**Purpose:** Show the complete trust building process from start to optimization
**Features Demonstrated:**
- Gradual trust score increase
- Multiple safe operations
- Trust persistence across runs
- Performance improvement tracking

**Usage:** Run multiple times and observe trust progression:
```bash
# Monitor trust building
for i in {1..12}; do
  echo "Run $i:"
  python main.py examples/trust_building_progression.aegis
  echo "---"
done
```

### 7. `variable_assignment_patterns.aegis` - Variable Usage Patterns
**Purpose:** Demonstrate various variable assignment and usage patterns
**Features Demonstrated:**
- Basic variable assignment
- Variable reuse and reassignment
- Chained assignments
- Complex variable interactions

**Expected Output:**
```
42
52
94
188
5
10
15
5
25
60
```

### 8. `optimization_showcase.aegis` - Performance Optimization Benefits
**Purpose:** Show the performance benefits of optimized execution
**Features Demonstrated:**
- Computation-heavy operations
- Caching benefits
- Performance measurement
- Optimization effectiveness

**Usage:** Build trust first, then observe performance improvements:
```bash
# Build trust with simpler programs first
python main.py examples/trust_demo.aegis  # Run 10+ times

# Then run the optimization showcase
python main.py --verbose examples/optimization_showcase.aegis
```

### 9. `error_handling_showcase.aegis` - Comprehensive Error Handling
**Purpose:** Demonstrate various error types and handling mechanisms
**Features Demonstrated:**
- Multiple error categories
- Error message quality
- Recovery mechanisms
- Debugging information

**Usage:** Uncomment different sections to test different error types:
```bash
# Edit the file to uncomment error sections
# Then run to see different error messages
python main.py examples/error_handling_showcase.aegis
```

## Learning Path

For new users, we recommend following this progression:

1. **Start with `basic_math.aegis`** - Learn basic syntax and operations
2. **Run `trust_demo.aegis` multiple times** - Understand trust building
3. **Try `complex_arithmetic.aegis`** - See more advanced expressions
4. **Experiment with `variable_assignment_patterns.aegis`** - Master variable usage
5. **Test `undefined_variable_demo.aegis`** - Understand error handling
6. **Run `security_violation_demo.aegis`** - See security features
7. **Use `trust_building_progression.aegis`** - Complete trust lifecycle
8. **Finish with `optimization_showcase.aegis`** - Performance benefits

## Interactive Experimentation

Use interactive mode to experiment with AEGIS features:

```bash
python main.py --interactive
```

Try these interactive examples:
```
# Basic operations
aegis> x = 10
aegis> y = 20
aegis> result = x + y
aegis> print result

# Trust building
aegis> status  # Check current trust score
aegis> # Run more operations...
aegis> status  # See trust increase

# Error testing
aegis> bad_result = x + undefined_var  # See error message
```

## Customizing Examples

Feel free to modify these examples to experiment with:
- Different arithmetic operations
- Various variable names and values
- Complex expression structures
- Error conditions and recovery

Remember that AEGIS prioritizes security over performance, so all code starts in the safe interpreted mode and must earn trust to access optimized execution.