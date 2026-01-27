# 🚀 AEGIS Quick Start Guide

## Instant Demo

```bash
# Trust building demonstration (shows security → performance transition)
python run.py demo

# Run a complete example
python run.py example complete_demo

# Interactive mode (each command is separate - press Enter twice)
python run.py interactive
```

## Example Programs

```bash
# Basic arithmetic
python main.py examples/basic_math.aegis

# Complex calculations  
python main.py examples/complex_arithmetic.aegis

# Security violation (division by zero)
python main.py examples/security_violation_demo.aegis

# Error handling
python main.py examples/undefined_variable_demo.aegis
```

## Key Features Demo

### 1. **Trust Building** (Security → Performance)
```bash
# Run the same program multiple times to see:
# Execution 1-7: SANDBOXED mode (secure but slower)
# Execution 8+:  OPTIMIZED mode (2.5x faster)
python run.py demo
```

### 2. **Security Violations**
```bash
# This will fail with detailed error message
python main.py examples/security_violation_demo.aegis
```

### 3. **Interactive Mode**
```bash
python main.py --interactive

# In interactive mode:
aegis> x = 42
# Press Enter twice to execute
aegis> print x  
# Press Enter twice to execute
```

## Understanding the Output

### Trust Progression
```
Trust Score: 0.00 (NONE)     → Starting point
Trust Score: 0.14 (NONE)     → Building trust
Trust Score: 0.56 (LOW)      → Getting closer
Trust Score: 1.08 (MEDIUM)   → OPTIMIZATION UNLOCKED!
```

### Execution Modes
- **SANDBOXED**: Secure interpreter (default for all new code)
- **OPTIMIZED**: Fast execution (earned through trust, ~2.5x speedup)

### Error Categories
- **[LEXICAL]**: Invalid characters
- **[SYNTAX]**: Grammar errors  
- **[SEMANTIC]**: Undefined variables
- **[RUNTIME]**: Division by zero, etc.
- **[SECURITY]**: Policy violations

## AEGIS Language Syntax

```aegis
# Variables and arithmetic
x = 10
y = x + 5
result = x * y / 2

# Print output
print result

# Supported operations: + - * /
# Supported types: integers only
# No comments in the language itself
```

## System Status

```bash
# Check trust scores and system stats
python main.py --status
```

## Running Tests

```bash
# Full test suite (256 tests)
python run.py test

# Or directly:
pytest tests/ -v
```

## Troubleshooting

**Q: Interactive mode needs Enter twice?**  
A: Yes, this detects multi-line input. Single Enter = continue, double Enter = execute.

**Q: Variables not shared between interactive commands?**  
A: Correct! Each command is a separate program with its own trust score.

**Q: How to see trust building?**  
A: Run `python run.py demo` - it shows the complete trust lifecycle.

**Q: Program fails with "Undefined variable"?**  
A: Variables must be defined before use in the same program.

---

**🛡️ AEGIS Core Principle**: Security is default, performance is conditional.  
All code starts secure and earns the right to run fast!