#!/usr/bin/env python3
"""
AEGIS - Adaptive Execution Guarded Interpreter System
Main entry point for the academic compiler design project.

This is the primary interface for running AEGIS programs. The system
demonstrates a security-first execution model where code starts in a
sandboxed interpreter and earns the right to optimized execution through
demonstrated safe behavior.

Usage:
    python main.py <source_file>
    python main.py --interactive
    python main.py --help
"""

import argparse
import sys
import hashlib
from pathlib import Path
from typing import Optional

# Import AEGIS components (will be implemented in subsequent tasks)
# from aegis.lexer import Lexer
# from aegis.parser import Parser
# from aegis.interpreter import SandboxedInterpreter, StaticAnalyzer, ExecutionContext
# from aegis.trust import TrustManager
# from aegis.compiler import OptimizedExecutor
# from aegis.runtime import RuntimeMonitor, RollbackHandler


class AEGISSystem:
    """
    Main AEGIS system coordinator.
    
    This class orchestrates the complete execution pipeline:
    tokenize → parse → analyze → interpret → monitor → trust update
    """
    
    def __init__(self):
        """Initialize the AEGIS system components."""
        print("[AEGIS] Initializing Adaptive Execution Guarded Interpreter System")
        
        # Components will be initialized as they are implemented
        # self.lexer = Lexer()
        # self.parser = Parser()
        # self.static_analyzer = StaticAnalyzer()
        # self.interpreter = SandboxedInterpreter()
        # self.trust_manager = TrustManager()
        # self.optimized_executor = OptimizedExecutor()
        # self.runtime_monitor = RuntimeMonitor()
        # self.rollback_handler = RollbackHandler()
        
        print("[AEGIS] System initialization complete")
    
    def execute_program(self, source_code: str) -> None:
        """
        Execute a complete AEGIS program through the security-adaptive pipeline.
        
        Args:
            source_code: The AEGIS source code to execute
        """
        print(f"[AEGIS] Starting execution pipeline")
        print(f"[SOURCE] {repr(source_code)}")
        
        # Calculate code hash for trust management
        code_hash = hashlib.sha256(source_code.encode()).hexdigest()[:16]
        print(f"[HASH] Code hash: {code_hash}")
        
        try:
            # Step 1: Tokenization (to be implemented)
            print("[PIPELINE] Step 1: Tokenization")
            # tokens = self.lexer.tokenize(source_code)
            
            # Step 2: Parsing (to be implemented)
            print("[PIPELINE] Step 2: Parsing")
            # ast = self.parser.parse(tokens)
            
            # Step 3: Static Analysis (to be implemented)
            print("[PIPELINE] Step 3: Static Security Analysis")
            # analysis_result = self.static_analyzer.analyze(ast)
            
            # Step 4: Execution (to be implemented)
            print("[PIPELINE] Step 4: Execution")
            # context = ExecutionContext(code_hash=code_hash)
            # result = self.interpreter.execute(ast, context)
            
            # Step 5: Trust Management (to be implemented)
            print("[PIPELINE] Step 5: Trust Management")
            # self.trust_manager.update_trust(code_hash, execution_metrics)
            
            print("[AEGIS] Execution pipeline completed successfully")
            
        except Exception as e:
            print(f"[ERROR] Execution failed: {e}")
            sys.exit(1)
    
    def interactive_mode(self) -> None:
        """
        Run AEGIS in interactive mode for testing and demonstration.
        """
        print("[AEGIS] Starting interactive mode")
        print("Enter AEGIS code (type 'exit' to quit, 'help' for commands):")
        
        while True:
            try:
                line = input("aegis> ").strip()
                
                if line == 'exit':
                    print("[AEGIS] Goodbye!")
                    break
                elif line == 'help':
                    self._show_help()
                elif line == '':
                    continue
                else:
                    self.execute_program(line)
                    
            except KeyboardInterrupt:
                print("\n[AEGIS] Interrupted by user")
                break
            except EOFError:
                print("\n[AEGIS] End of input")
                break
    
    def _show_help(self) -> None:
        """Show help information for interactive mode."""
        print("""
AEGIS Interactive Mode Commands:
  help     - Show this help message
  exit     - Exit interactive mode
  
AEGIS Language Syntax:
  x = 10        - Variable assignment
  y = x + 5     - Arithmetic expression
  print y       - Print variable value
  
Supported operators: + - * /
Data types: integers only
        """)


def main():
    """Main entry point for the AEGIS system."""
    parser = argparse.ArgumentParser(
        description="AEGIS - Adaptive Execution Guarded Interpreter System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py program.aegis     # Execute a file
  python main.py --interactive     # Interactive mode
  
The AEGIS system demonstrates security-first execution where code
starts in a sandboxed interpreter and earns optimized execution
through demonstrated safe behavior.
        """
    )
    
    parser.add_argument(
        'source_file',
        nargs='?',
        help='AEGIS source file to execute'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='AEGIS 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Initialize the AEGIS system
    aegis = AEGISSystem()
    
    if args.interactive:
        # Interactive mode
        aegis.interactive_mode()
    elif args.source_file:
        # File execution mode
        source_path = Path(args.source_file)
        if not source_path.exists():
            print(f"[ERROR] Source file not found: {args.source_file}")
            sys.exit(1)
        
        try:
            source_code = source_path.read_text()
            aegis.execute_program(source_code)
        except Exception as e:
            print(f"[ERROR] Failed to read source file: {e}")
            sys.exit(1)
    else:
        # No arguments provided
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()