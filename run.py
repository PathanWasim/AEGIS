#!/usr/bin/env python3
"""
Simple runner script for AEGIS - Adaptive Execution Guarded Interpreter System

This script provides an easy way to run AEGIS programs and demonstrates
the key features of the security-first execution model.
"""

import sys
import os
import subprocess

def print_banner():
    """Print AEGIS banner."""
    print("=" * 60)
    print("🛡️  AEGIS - Adaptive Execution Guarded Interpreter System")
    print("   Security-First Academic Compiler Design Project")
    print("=" * 60)
    print()

def run_example(example_name):
    """Run a specific example program."""
    example_file = f"examples/{example_name}.aegis"
    if not os.path.exists(example_file):
        print(f"❌ Example '{example_name}' not found!")
        print("Available examples:")
        for f in os.listdir("examples"):
            if f.endswith(".aegis"):
                print(f"  - {f[:-6]}")
        return
    
    print(f"🚀 Running example: {example_name}")
    print("-" * 40)
    subprocess.run([sys.executable, "main.py", example_file])

def demo_trust_building():
    """Demonstrate trust building and optimization."""
    print("🔒 AEGIS Trust Building Demonstration")
    print("=" * 50)
    print("Running the same program multiple times to show:")
    print("• Trust score progression (0.00 → 1.00+)")
    print("• Execution mode transition (SANDBOXED → OPTIMIZED)")
    print("• Performance improvement (~2.5x speedup)")
    print()
    
    for i in range(1, 13):
        print(f"--- Execution {i:2d} ---")
        result = subprocess.run([
            sys.executable, "main.py", "examples/trust_demo.aegis"
        ], capture_output=True, text=True)
        
        # Extract key information
        lines = result.stdout.split('\n')
        trust_score = "Unknown"
        exec_mode = "Unknown"
        
        for line in lines:
            if "Trust score:" in line:
                trust_score = line.split("Trust score: ")[1].split(" ")[0]
            elif "Execution mode:" in line:
                exec_mode = line.split("Execution mode: ")[1]
        
        print(f"Trust: {trust_score:>6} | Mode: {exec_mode}")
        
        # Show transition point
        if "OPTIMIZED" in exec_mode and i >= 8:
            print("🎉 OPTIMIZATION ACHIEVED! Performance boost unlocked!")
            break
    
    print("\n✅ Trust building demonstration complete!")
    print("The program earned trust and unlocked optimized execution!")

def run_interactive():
    """Run interactive mode with better instructions."""
    print("🎮 AEGIS Interactive Mode")
    print("=" * 30)
    print("Tips for interactive mode:")
    print("• Each command is a separate program (no shared variables)")
    print("• Press Enter twice to execute a command")
    print("• Type 'exit' to quit")
    print("• Try: x = 10, then: print x (in separate commands)")
    print()
    
    subprocess.run([sys.executable, "main.py", "--interactive"])

def show_examples():
    """Show available examples."""
    print("📚 Available AEGIS Examples")
    print("=" * 30)
    
    examples = {
        "basic_math": "Simple arithmetic operations",
        "trust_demo": "Trust building demonstration",
        "complex_arithmetic": "Complex mathematical expressions",
        "security_violation_demo": "Division by zero security violation",
        "undefined_variable_demo": "Static analysis error detection",
        "variable_assignment_patterns": "Various variable usage patterns",
        "optimization_showcase": "Performance optimization benefits",
        "error_handling_showcase": "Comprehensive error handling"
    }
    
    for name, description in examples.items():
        if os.path.exists(f"examples/{name}.aegis"):
            print(f"  {name:25} - {description}")
    
    print("\nTo run an example: python run.py example <name>")

def main():
    """Main runner function."""
    print_banner()
    
    if len(sys.argv) < 2:
        print("🚀 AEGIS Quick Start Options:")
        print()
        print("  python run.py demo          - Trust building demonstration")
        print("  python run.py interactive   - Interactive mode")
        print("  python run.py examples      - List all examples")
        print("  python run.py example <name> - Run specific example")
        print("  python run.py test          - Run test suite")
        print()
        print("📖 Direct usage:")
        print("  python main.py program.aegis     - Run a program file")
        print("  python main.py --help           - Show all options")
        print()
        return
    
    command = sys.argv[1].lower()
    
    if command == "demo":
        demo_trust_building()
    elif command == "interactive":
        run_interactive()
    elif command == "examples":
        show_examples()
    elif command == "example" and len(sys.argv) > 2:
        run_example(sys.argv[2])
    elif command == "test":
        print("🧪 Running AEGIS Test Suite")
        print("-" * 30)
        subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python run.py' to see available options")

if __name__ == "__main__":
    main()