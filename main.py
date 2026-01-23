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
import json
from pathlib import Path
from typing import Optional

from aegis.pipeline import AegisExecutionPipeline


class AEGISSystem:
    """
    Main AEGIS system coordinator.
    
    This class provides a user-friendly interface to the AegisExecutionPipeline
    with enhanced console output, logging, and interactive features.
    """
    
    def __init__(self, verbose: bool = True, trust_file: str = ".aegis_trust.json"):
        """Initialize the AEGIS system with the execution pipeline."""
        if verbose:
            print("[AEGIS] Initializing Adaptive Execution Guarded Interpreter System")
        
        # Initialize the main execution pipeline
        self.pipeline = AegisExecutionPipeline(trust_file=trust_file)
        self.verbose = verbose
        
        if verbose:
            print("[AEGIS] System initialization complete")
            self._show_system_info()
    
    def _show_system_info(self) -> None:
        """Display system configuration and status."""
        status = self.pipeline.get_system_status()
        config = status['configuration']
        
        print(f"[AEGIS] Configuration:")
        print(f"  Trust threshold: {config['trust_threshold']}")
        print(f"  Violation threshold: {config['violation_threshold']} instructions")
        print(f"  Cache size: {config['cache_size']} entries")
        print(f"  Trust file: {config['trust_file']}")
    
    def execute_program(self, source_code: str, show_details: bool = True) -> None:
        """
        Execute a complete AEGIS program with enhanced console output.
        
        Args:
            source_code: The AEGIS source code to execute
            show_details: Whether to show detailed execution information
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"[AEGIS] PROGRAM EXECUTION")
            print(f"{'='*60}")
            print(f"[SOURCE] {repr(source_code)}")
        
        # Execute through the pipeline
        result = self.pipeline.execute(source_code, verbose=self.verbose)
        
        # Display results with enhanced formatting
        self._display_execution_result(result, show_details)
    
    def _display_execution_result(self, result, show_details: bool = True) -> None:
        """Display execution result with formatted output."""
        print(f"\n{'='*60}")
        print(f"[AEGIS] EXECUTION RESULT")
        print(f"{'='*60}")
        
        # Basic result information
        status_symbol = "✓" if result.success else "✗"
        print(f"Status: {status_symbol} {'SUCCESS' if result.success else 'FAILED'}")
        print(f"Execution Time: {result.execution_time:.3f}s")
        print(f"Execution Mode: {result.execution_mode.upper()}")
        
        if result.success:
            print(f"Trust Score: {result.trust_score:.2f} ({result.trust_level})")
            
            # Program output
            if result.output:
                print(f"\nProgram Output:")
                for line in result.output:
                    print(f"  {line}")
            else:
                print(f"\nProgram Output: (no output)")
            
            # Execution metrics
            if show_details:
                metrics = result.metrics
                print(f"\nExecution Metrics:")
                print(f"  Instructions executed: {metrics.instruction_count}")
                print(f"  Variables accessed: {len(metrics.variables_accessed)}")
                print(f"  Arithmetic operations: {metrics.arithmetic_operations}")
                print(f"  Print statements: {metrics.print_operations}")
                
                if metrics.violations_detected:
                    print(f"  Security violations: {len(metrics.violations_detected)}")
                    for violation in metrics.violations_detected:
                        print(f"    - {violation.violation_type}: {violation.message}")
            
            # Trust score changes
            if show_details and hasattr(result, 'trust_changes'):
                print(f"\nTrust Score Changes:")
                for change in result.trust_changes:
                    print(f"  {change}")
            
            # Rollback events
            if result.rollback_events:
                print(f"\nRollback Events:")
                for event in result.rollback_events:
                    print(f"  {event.timestamp}: {event.violation_type} -> {event.action}")
                    if event.details:
                        print(f"    Details: {event.details}")
        
        else:
            # Error information
            print(f"Error: {result.error_message}")
        
        print(f"{'='*60}")
    
    def execute_file(self, file_path: str, show_details: bool = True) -> None:
        """Execute a program from a file."""
        source_path = Path(file_path)
        if not source_path.exists():
            print(f"[ERROR] Source file not found: {file_path}")
            sys.exit(1)
        
        try:
            source_code = source_path.read_text()
            if self.verbose:
                print(f"[AEGIS] Loading program from: {file_path}")
            self.execute_program(source_code, show_details)
        except Exception as e:
            print(f"[ERROR] Failed to read source file: {e}")
            sys.exit(1)
    
    def execute_batch(self, file_paths: list, show_summary: bool = True) -> None:
        """Execute multiple programs in batch mode."""
        programs = []
        
        for file_path in file_paths:
            source_path = Path(file_path)
            if not source_path.exists():
                print(f"[ERROR] Source file not found: {file_path}")
                continue
            
            try:
                source_code = source_path.read_text()
                programs.append(source_code)
            except Exception as e:
                print(f"[ERROR] Failed to read {file_path}: {e}")
                continue
        
        if not programs:
            print("[ERROR] No valid programs to execute")
            return
        
        # Execute batch
        results = self.pipeline.execute_batch(programs, verbose=False)
        
        # Show detailed summary
        if show_summary:
            self._display_batch_summary(results, file_paths)
    
    def _display_batch_summary(self, results, file_paths) -> None:
        """Display detailed batch execution summary."""
        print(f"\n{'='*60}")
        print(f"[AEGIS] BATCH EXECUTION SUMMARY")
        print(f"{'='*60}")
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        optimized = [r for r in results if r.execution_mode == 'optimized']
        
        print(f"Total programs: {len(results)}")
        print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
        print(f"Optimized: {len(optimized)} ({len(optimized)/len(successful)*100:.1f}% of successful)")
        
        if successful:
            avg_time = sum(r.execution_time for r in successful) / len(successful)
            avg_trust = sum(r.trust_score for r in successful) / len(successful)
            print(f"Average execution time: {avg_time:.3f}s")
            print(f"Average trust score: {avg_trust:.2f}")
        
        # Individual program results
        print(f"\nIndividual Results:")
        for i, (result, file_path) in enumerate(zip(results, file_paths)):
            status = "✓" if result.success else "✗"
            mode = result.execution_mode[:4].upper()
            trust = f"{result.trust_score:.1f}" if result.success else "N/A"
            print(f"  {i+1:2d}. {status} {Path(file_path).name:<20} {mode} {result.execution_time:.3f}s Trust:{trust}")
    
    def interactive_mode(self) -> None:
        """
        Run AEGIS in interactive mode with enhanced features.
        """
        print(f"\n{'='*60}")
        print("[AEGIS] INTERACTIVE MODE")
        print(f"{'='*60}")
        print("Enter AEGIS code (type 'exit' to quit, 'help' for commands)")
        print("Multi-line input: end with empty line")
        
        while True:
            try:
                # Get input (support multi-line)
                lines = []
                print("\naegis> ", end="")
                
                while True:
                    line = input().strip()
                    if line == '':
                        break
                    lines.append(line)
                
                if not lines:
                    continue
                
                command = lines[0]
                
                if command == 'exit':
                    print("[AEGIS] Goodbye!")
                    break
                elif command == 'help':
                    self._show_interactive_help()
                elif command == 'status':
                    self._show_system_status()
                elif command == 'config':
                    self._interactive_config()
                elif command == 'clear':
                    self._clear_system_data()
                else:
                    # Execute the code
                    source_code = '\n'.join(lines)
                    self.execute_program(source_code, show_details=True)
                    
            except KeyboardInterrupt:
                print("\n[AEGIS] Interrupted by user")
                break
            except EOFError:
                print("\n[AEGIS] End of input")
                break
    
    def _show_interactive_help(self) -> None:
        """Show help information for interactive mode."""
        print(f"""
{'='*60}
[AEGIS] INTERACTIVE MODE HELP
{'='*60}

Commands:
  help     - Show this help message
  status   - Show system status and statistics
  config   - Configure system parameters
  clear    - Clear trust data and cache
  exit     - Exit interactive mode

AEGIS Language Syntax:
  x = 10        - Variable assignment
  y = x + 5     - Arithmetic expression
  print y       - Print variable value

Supported operators: + - * /
Data types: integers only

Multi-line input: Enter multiple lines, end with empty line

Examples:
  x = 5
  y = x * 2
  print y
  
Trust System:
- Programs start in SANDBOXED mode
- Safe execution builds trust score
- High trust enables OPTIMIZED mode
- Security violations trigger rollback
{'='*60}
        """)
    
    def _show_system_status(self) -> None:
        """Show detailed system status."""
        status = self.pipeline.get_system_status()
        
        print(f"\n{'='*60}")
        print("[AEGIS] SYSTEM STATUS")
        print(f"{'='*60}")
        
        # Execution statistics
        exec_stats = status['execution_stats']
        print(f"Execution Statistics:")
        print(f"  Total executions: {exec_stats['total_executions']}")
        print(f"  Successful: {exec_stats['successful_executions']}")
        print(f"  Optimized: {exec_stats['optimized_executions']}")
        print(f"  Rollbacks: {exec_stats['rollback_count']}")
        print(f"  Success rate: {exec_stats['success_rate']:.1%}")
        print(f"  Optimization rate: {exec_stats['optimization_rate']:.1%}")
        
        # Trust system
        trust_stats = status['trust_system']
        print(f"\nTrust System:")
        print(f"  Total programs: {trust_stats['total_codes']}")
        print(f"  Trusted programs: {trust_stats['trusted_codes']}")
        print(f"  Average trust score: {trust_stats['average_score']:.2f}")
        
        # Configuration
        config = status['configuration']
        print(f"\nConfiguration:")
        print(f"  Trust threshold: {config['trust_threshold']}")
        print(f"  Violation threshold: {config['violation_threshold']}")
        print(f"  Cache size: {config['cache_size']}")
        
        print(f"{'='*60}")
    
    def _interactive_config(self) -> None:
        """Interactive system configuration."""
        print(f"\n{'='*60}")
        print("[AEGIS] SYSTEM CONFIGURATION")
        print(f"{'='*60}")
        
        try:
            print("Enter new values (press Enter to keep current):")
            
            # Trust threshold
            current_trust = self.pipeline.trust_threshold
            trust_input = input(f"Trust threshold ({current_trust}): ").strip()
            if trust_input:
                new_trust = float(trust_input)
                self.pipeline.configure_system(trust_threshold=new_trust)
            
            # Violation threshold
            current_violation = self.pipeline.violation_threshold
            violation_input = input(f"Violation threshold ({current_violation}): ").strip()
            if violation_input:
                new_violation = int(violation_input)
                self.pipeline.configure_system(violation_threshold=new_violation)
            
            print("[AEGIS] Configuration updated")
            
        except ValueError as e:
            print(f"[ERROR] Invalid input: {e}")
    
    def _clear_system_data(self) -> None:
        """Clear system data with confirmation."""
        print(f"\n[WARNING] This will clear all trust data and cache.")
        confirm = input("Are you sure? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            self.pipeline.cleanup_system()
            print("[AEGIS] System data cleared")
        else:
            print("[AEGIS] Operation cancelled")


def main():
    """Main entry point for the AEGIS system."""
    parser = argparse.ArgumentParser(
        description="AEGIS - Adaptive Execution Guarded Interpreter System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py program.aegis           # Execute a file
  python main.py --interactive           # Interactive mode
  python main.py --batch *.aegis         # Batch execution
  python main.py --status                # Show system status
  
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
        '--batch', '-b',
        nargs='+',
        help='Execute multiple files in batch mode'
    )
    
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show system status and exit'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Reduce output verbosity'
    )
    
    parser.add_argument(
        '--trust-file',
        default='.aegis_trust.json',
        help='Trust data file path (default: .aegis_trust.json)'
    )
    
    parser.add_argument(
        '--config',
        action='store_true',
        help='Show configuration and exit'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='AEGIS 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Initialize the AEGIS system
    verbose = not args.quiet
    aegis = AEGISSystem(verbose=verbose, trust_file=args.trust_file)
    
    if args.status:
        # Show system status
        aegis._show_system_status()
    elif args.config:
        # Show configuration
        status = aegis.pipeline.get_system_status()
        config = status['configuration']
        print(json.dumps(config, indent=2))
    elif args.interactive:
        # Interactive mode
        aegis.interactive_mode()
    elif args.batch:
        # Batch execution mode
        aegis.execute_batch(args.batch, show_summary=True)
    elif args.source_file:
        # File execution mode
        aegis.execute_file(args.source_file, show_details=True)
    else:
        # No arguments provided
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()