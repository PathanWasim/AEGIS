# 🛡️ How to Run AEGIS

## 🚀 Super Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the trust building demo
python run.py demo

# 3. Try an example program
python run.py example basic_math

# 4. Interactive mode (press Enter twice for each command)
python run.py interactive
```

## 📋 All Available Commands

### **Easy Runner Script**
```bash
python run.py                    # Show all options
python run.py demo              # Trust building demonstration  
python run.py examples          # List all example programs
python run.py example <name>    # Run specific example
python run.py interactive       # Interactive mode with tips
python run.py test              # Run full test suite
```

### **Direct Main Script**
```bash
python main.py program.aegis           # Run a program file
python main.py --interactive           # Interactive mode
python main.py --verbose program.aegis # Detailed logging
python main.py --status               # System status
python main.py --help                 # All options
```

## 🎮 Interactive Mode Guide

**Important**: Each command in interactive mode is a **separate program**!

```bash
python run.py interactive

# In interactive mode:
aegis> x = 42
# Press Enter twice to execute ⏎⏎

aegis> print x  
# Press Enter twice to execute ⏎⏎
# Output: 42

aegis> y = x + 8
# This will FAIL because x is not defined in this new program!
# Each command is independent

aegis> exit
# Quit interactive mode
```

### **Why Press Enter Twice?**
- Single Enter = continue typing (multi-line support)
- Double Enter = execute the program
- This allows for complex multi-line programs in interactive mode

### **Why No Shared Variables?**
- Each command is a separate program with its own trust score
- This demonstrates AEGIS's per-program trust management
- Real interactive interpreters would share state, but AEGIS shows security isolation

## 📚 Example Programs

### **Basic Examples**
```bash
python run.py example basic_math           # Simple arithmetic
python run.py example trust_demo           # Trust building
python run.py example complete_demo        # Comprehensive demo
```

### **Advanced Examples**
```bash
python run.py example complex_arithmetic   # Complex calculations
python run.py example optimization_showcase # Performance benefits
python run.py example variable_assignment_patterns # Variable usage
```

### **Error Demonstrations**
```bash
python run.py example security_violation_demo  # Division by zero
python run.py example undefined_variable_demo  # Static analysis error
python run.py example error_handling_showcase  # Error types
```

## 🔍 Understanding AEGIS Output

### **Trust Progression**
```
Trust Score: 0.00 (NONE)     ← All programs start here
Trust Score: 0.14 (NONE)     ← Building trust (+0.14 per success)
Trust Score: 0.56 (LOW)      ← Getting closer to optimization
Trust Score: 1.08 (MEDIUM)   ← OPTIMIZATION UNLOCKED! 🎉
Trust Score: 2.41 (HIGH)     ← Continued trust building
```

### **Execution Modes**
- **SANDBOXED**: Secure interpreter (default, slower)
- **OPTIMIZED**: Fast execution (earned, ~2.5x speedup)
- **FAILED**: Error occurred during execution

### **Error Categories**
- **[LEXICAL] [LEX001]**: Invalid characters (e.g., `x = 10 @`)
- **[SYNTAX] [SYN001]**: Grammar errors (e.g., `x = `)
- **[SEMANTIC] [SEM001]**: Logic errors (e.g., `print undefined_var`)
- **[RUNTIME] [RUN001]**: Execution errors (e.g., `x = 5 / 0`)
- **[SECURITY]**: Policy violations and rollbacks

## 🎯 Key Features Demonstration

### **1. Trust Building & Optimization**
```bash
# Clear trust data first (optional)
rm .aegis_trust.json

# Run trust demo to see progression
python run.py demo
```

You'll see:
1. **Executions 1-7**: SANDBOXED mode, trust building (0.00 → 0.89)
2. **Execution 8**: Trust reaches 1.08, switches to OPTIMIZED mode
3. **Executions 9+**: Continues in OPTIMIZED mode with 2.5x speedup

### **2. Security Violation & Rollback**
```bash
# This program will fail with detailed error
python run.py example security_violation_demo
```

Shows:
- Partial execution (prints 15)
- Division by zero detection
- Detailed error message with variable state
- Actionable suggestions for fixing

### **3. Static Analysis**
```bash
# This will fail before execution
python run.py example undefined_variable_demo
```

Shows:
- Static analysis catches undefined variables
- Prevents unsafe code from running
- Detailed error with suggestions

### **4. System Status**
```bash
python main.py --status
```

Shows:
- All program trust scores
- System performance metrics
- Cache statistics
- Execution history

## 🧪 Testing

```bash
# Run all tests (256 tests)
python run.py test

# Or specific test categories
pytest tests/test_lexer*.py -v          # Lexer tests
pytest tests/test_*_properties.py -v    # Property-based tests
pytest tests/test_integration*.py -v    # Integration tests
pytest tests/test_performance*.py -v    # Performance tests
```

## 🔧 Advanced Usage

### **Custom Configuration**
```bash
# Custom trust file
python main.py --trust-file my_trust.json program.aegis

# Different trust threshold
python main.py --trust-threshold 0.5 program.aegis

# Larger cache size
python main.py --cache-size 500 program.aegis

# Verbose logging (shows all internal operations)
python main.py --verbose program.aegis
```

### **Batch Execution**
```bash
# Run multiple programs
python main.py --batch file1.aegis file2.aegis file3.aegis
```

## 🚨 Common Issues & Solutions

### **Q: "Undefined variable" in interactive mode**
```
aegis> x = 10
# Success

aegis> print x
# ERROR: Undefined variable: x
```
**A**: Each interactive command is a separate program. Use complete programs:
```
aegis> x = 10
print x
# Press Enter twice - this works!
```

### **Q: Trust not building**
```
Trust Score: 0.14 (no change)
```
**A**: Trust only increases with successful executions. Fix errors first, then run multiple times.

### **Q: Need to press Enter twice**
```
aegis> x = 10
# Waiting...
```
**A**: This is intentional for multi-line support. Press Enter twice to execute.

### **Q: Want to see trust building from scratch**
```bash
# Remove existing trust data
rm .aegis_trust.json

# Run demo to see full progression
python run.py demo
```

## 🎓 Learning Path

1. **Start here**: `python run.py demo` (trust building)
2. **Try examples**: `python run.py examples` (list all)
3. **Run basic math**: `python run.py example basic_math`
4. **See errors**: `python run.py example security_violation_demo`
5. **Interactive mode**: `python run.py interactive`
6. **System status**: `python main.py --status`
7. **Verbose mode**: `python main.py --verbose examples/basic_math.aegis`

## 🏆 AEGIS Core Concept

**"Security is Default, Performance is Conditional"**

- ✅ All code starts in secure SANDBOXED mode
- ✅ Trust builds through successful executions (+0.14 per success)
- ✅ Optimization unlocks at trust ≥ 1.0 (~2.5x speedup)
- ✅ Security violations trigger rollback to safe mode
- ✅ Each program has independent trust tracking

This creates a system where code must **earn the right to run fast** by proving it's safe!