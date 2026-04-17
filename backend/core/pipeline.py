"""
backend/core/pipeline.py
Upgraded AEGIS execution pipeline with new trust model:
  - Statically safe  → initial trust 0.6  (eligible after 2nd run)
  - Statically unsafe → initial trust 0.2
  - Each safe run: +0.3
  - Threshold: 1.0
  - Violation: reset to 0.0 + rollback
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

from aegis.lexer.lexer import Lexer
from aegis.parser.parser import Parser
from aegis.ast.serializer import ast_to_dict
from aegis.interpreter.interpreter import SandboxedInterpreter
from aegis.interpreter.context import ExecutionContext
from aegis.runtime.monitor import RuntimeMonitor
from aegis.errors import (
    LexicalError, SemanticError,
    SyntaxError as AegisSyntaxError,
    RuntimeError as AegisRuntimeError,
    SecurityError, AegisError
)

# ── Trust store (in-memory, per-server-session) ───────────────────────────────

_trust_store: Dict[str, float] = {}

INITIAL_SAFE   = 0.6
INITIAL_UNSAFE = 0.2
INCREMENT      = 0.3
THRESHOLD      = 1.0
TRUST_MAX      = 1.5   # Hard upper cap
TRUST_MIN      = 0.0   # Hard lower floor


def code_hash(source: str) -> str:
    return hashlib.sha256(source.encode()).hexdigest()[:12]


def get_trust(h: str) -> float:
    return _trust_store.get(h, 0.0)


def trust_level(score: float) -> str:
    if score >= 1.0: return "HIGH"
    if score >= 0.6: return "MEDIUM"
    if score >= 0.2: return "LOW"
    return "NONE"


def _update_trust(h: str, had_violation: bool, initially_safe: bool) -> float:
    if had_violation:
        _trust_store[h] = TRUST_MIN
        return TRUST_MIN
    if h not in _trust_store:
        _trust_store[h] = INITIAL_SAFE if initially_safe else INITIAL_UNSAFE
    else:
        _trust_store[h] = _trust_store[h] + INCREMENT
    # Enforce hard bounds
    _trust_store[h] = max(TRUST_MIN, min(TRUST_MAX, _trust_store[h]))
    return _trust_store[h]


def reset_all_trust():
    _trust_store.clear()


def all_trust_entries() -> int:
    return len(_trust_store)


# ── Static analysis ───────────────────────────────────────────────────────────

@dataclass
class Issue:
    type: str        # UNDEFINED_VAR | DIV_BY_ZERO | INFINITE_LOOP | OVERFLOW | DEEP_NESTING
    message: str
    line: int
    severity: str    # LOW | MEDIUM | HIGH

    def to_dict(self):
        return {"type": self.type, "message": self.message,
                "line": self.line, "severity": self.severity}


def run_static_analysis(ast_nodes) -> List[Issue]:
    issues: List[Issue] = []
    defined: set = set()

    def _ln(node) -> int:
        return getattr(node, 'line', 0)

    def walk(node, depth=0):
        from aegis.ast.nodes import (
            AssignmentNode, PrintNode, IfNode, WhileNode,
            BinaryOpNode, IdentifierNode, IntegerNode,
        )
        if isinstance(node, AssignmentNode):
            walk(node.expression, depth)
            name = node.identifier if isinstance(node.identifier, str) else node.identifier.name
            defined.add(name)

        elif isinstance(node, PrintNode):
            walk(node.expression, depth)

        elif isinstance(node, IfNode):
            walk(node.condition, depth)
            for s in node.then_body: walk(s, depth)
            for s in node.else_body: walk(s, depth)

        elif isinstance(node, WhileNode):
            cond = node.condition
            # Detect trivially infinite loop: literal == literal where result is always true
            from aegis.ast.nodes import BinaryOpNode as BOP, IntegerNode as IN
            if isinstance(cond, BOP) and isinstance(cond.left, IN) and isinstance(cond.right, IN):
                lv, rv, op = cond.left.value, cond.right.value, cond.operator
                always_true = (
                    (op == '==' and lv == rv) or (op == '<=' and lv <= rv) or
                    (op == '>=' and lv >= rv) or (op == '<'  and lv <  rv) or
                    (op == '>'  and lv >  rv)
                )
                if always_true:
                    issues.append(Issue("INFINITE_LOOP",
                        f"Condition `{lv} {op} {rv}` is always true — infinite loop",
                        _ln(node), "HIGH"))
            for s in node.body: walk(s, depth)

        elif isinstance(node, BinaryOpNode):
            if depth > 8:
                issues.append(Issue("DEEP_NESTING",
                    "Expression exceeds 8 nesting levels — potential stack stress",
                    _ln(node), "MEDIUM"))
            walk(node.left, depth + 1)
            walk(node.right, depth + 1)
            from aegis.ast.nodes import IntegerNode as IN
            if node.operator in ('/', '%') and isinstance(node.right, IN) and node.right.value == 0:
                issues.append(Issue("DIV_BY_ZERO",
                    "Literal division by zero", _ln(node), "HIGH"))
            if node.operator in ('+', '*') and isinstance(node.left, IN) and isinstance(node.right, IN):
                if node.left.value > 1_000_000 or node.right.value > 1_000_000:
                    issues.append(Issue("OVERFLOW",
                        "Large literal operands may cause arithmetic overflow",
                        _ln(node), "MEDIUM"))

        elif isinstance(node, IdentifierNode):
            if node.name not in defined:
                issues.append(Issue("UNDEFINED_VAR",
                    f"Variable `{node.name}` used before assignment",
                    _ln(node), "HIGH"))

    for node in ast_nodes:
        walk(node)
    return issues


# ── Optimized execution cache ─────────────────────────────────────────────────

_ast_cache: Dict[str, List[str]] = {}   # code_hash → cached output lines


def _exec_optimized(h: str, ast_nodes, context: ExecutionContext, monitor) -> None:
    if h in _ast_cache:
        for line in _ast_cache[h]:
            context.add_output(line)
        return
    interp = SandboxedInterpreter(monitor)
    interp.execute(ast_nodes, context)
    _ast_cache[h] = list(context.output_buffer)


# ── Pipeline result ───────────────────────────────────────────────────────────

@dataclass
class PipelineResult:
    success: bool
    output: List[str]
    execution_mode: str
    trust_score: float
    trust_level: str
    issues: List[Issue]
    logs: List[str]
    violations: List[str]
    rollback: bool
    execution_time_ms: float
    tokens: List[dict] = field(default_factory=list)
    ast: Optional[Any] = None
    pipeline_stages: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self):
        return {
            "success":           self.success,
            "output":            self.output,
            "execution_mode":    self.execution_mode,
            "trust_score":       round(self.trust_score, 3),
            "trust_level":       self.trust_level,
            "issues":            [i.to_dict() for i in self.issues],
            "logs":              self.logs,
            "violations":        self.violations,
            "rollback":          self.rollback,
            "execution_time_ms": self.execution_time_ms,
            "tokens":            self.tokens,
            "ast":               self.ast,
            "pipeline_stages":   self.pipeline_stages,
            "metrics":           self.metrics,
            "error":             self.error,
        }


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(source: str) -> PipelineResult:
    logs: List[str] = []
    start = time.perf_counter()
    h = code_hash(source)
    # All 7 stages tracked — interpreter is always attempted first (invariant)
    stages = {
        "lexed":      False,
        "parsed":     False,
        "ast_built":  False,
        "analyzed":   False,
        "interpreted": False,
        "trust":      False,
        "optimized":  False,
    }

    lexer  = Lexer()
    parser = Parser()

    # ── Phase 1: Lex ──────────────────────────────────────────────────────────
    try:
        logs.append("[LEXER] Tokenizing...")
        tokens = lexer.tokenize(source)
        stages["lexed"] = True
        logs.append(f"[LEXER] {len(tokens)} tokens")
    except LexicalError as e:
        return _fail(h, start, str(e), logs, stages, [])

    # ── Phase 2: Parse ────────────────────────────────────────────────────────
    try:
        logs.append("[PARSER] Building AST...")
        ast_nodes = parser.parse(tokens)
        stages["parsed"] = True
        logs.append(f"[PARSER] {len(ast_nodes)} top-level nodes")
    except AegisSyntaxError as e:
        return _fail(h, start, str(e), logs, stages, tokens)

    stages["ast_built"] = True

    # Serialize AST
    try:
        ast_dict = ast_to_dict(ast_nodes)
    except Exception:
        ast_dict = None

    # Serialize tokens
    from core.helpers import token_to_dict
    token_list = [token_to_dict(t) for t in tokens]

    # ── Phase 3: Static analysis ──────────────────────────────────────────────
    logs.append("[ANALYZER] Running static checks...")
    issues = run_static_analysis(ast_nodes)
    stages["analyzed"] = True
    has_high = any(i.severity == "HIGH" for i in issues)
    optimization_blocked = has_high

    if issues:
        for iss in issues:
            logs.append(f"[{iss.severity}] {iss.type}: {iss.message} (line {iss.line})")
    else:
        logs.append("[ANALYZER] Clean — no issues")

    initially_safe = not has_high

    # ── Phase 4: Trust check ──────────────────────────────────────────────────
    current_score = get_trust(h)
    can_optimize  = (current_score >= THRESHOLD) and not optimization_blocked
    # Invariant: first run is ALWAYS interpreter (trust starts at 0 before any run)
    mode = "optimized" if can_optimize else "interpreter"

    stages["trust"] = True
    logs.append(f"[TRUST] Score: {round(current_score, 2)} | Threshold: {THRESHOLD}")
    logs.append(f"[MODE] {mode.upper()}")
    if optimization_blocked:
        logs.append("[TRUST] Optimization BLOCKED — HIGH severity issues present")

    # ── Phase 5: Execute ──────────────────────────────────────────────────────
    monitor  = RuntimeMonitor()
    context  = ExecutionContext()
    violations: List[str] = []
    rollback = False

    monitor.start_monitoring(context)
    try:
        if mode == "optimized":
            logs.append("[VM] Executing optimized path (cached AST)")
            _exec_optimized(h, ast_nodes, context, monitor)
            stages["optimized"] = True
        else:
            logs.append("[INTERP] Executing in sandboxed interpreter")
            interp = SandboxedInterpreter(monitor)
            interp.execute(ast_nodes, context)
            stages["interpreted"] = True

    except (AegisRuntimeError, SecurityError) as e:
        msg = str(e)
        violations.append(msg)
        logs.append(f"[VIOLATION] {msg}")
        if mode == "optimized":
            rollback = True
            logs.append("[ROLLBACK] Triggered — trust reset, reverting to interpreter")
            _trust_store[h] = TRUST_MIN
            logs.append("[TRUST] Score reset to 0.0")
        final_metrics = monitor.stop_monitoring()
        elapsed = (time.perf_counter() - start) * 1000
        score = get_trust(h)
        return PipelineResult(
            success=False, output=list(context.output_buffer), execution_mode=mode,
            trust_score=score, trust_level=trust_level(score), issues=issues,
            logs=logs, violations=violations, rollback=rollback,
            execution_time_ms=round(elapsed, 2), tokens=token_list, ast=ast_dict,
            pipeline_stages=stages, metrics=_build_metrics(final_metrics, elapsed), error=msg,
        )

    except SemanticError as e:
        msg = str(e)
        monitor.stop_monitoring()
        elapsed = (time.perf_counter() - start) * 1000
        score = get_trust(h)
        return PipelineResult(
            success=False, output=[], execution_mode="failed",
            trust_score=score, trust_level=trust_level(score), issues=issues,
            logs=logs, violations=[msg], rollback=False,
            execution_time_ms=round(elapsed, 2), tokens=token_list, ast=ast_dict,
            pipeline_stages=stages, error=msg,
        )

    # ── Phase 6: Update trust ─────────────────────────────────────────────────
    final_metrics = monitor.stop_monitoring()
    new_score = _update_trust(h, had_violation=False, initially_safe=initially_safe)
    logs.append(f"[TRUST] Updated → {round(new_score, 2)}")
    logs.append(f"[METRICS] Instructions: {final_metrics.instruction_count} | Time: {round((time.perf_counter()-start)*1000, 2)}ms")

    elapsed = (time.perf_counter() - start) * 1000
    return PipelineResult(
        success=True, output=list(context.output_buffer), execution_mode=mode,
        trust_score=new_score, trust_level=trust_level(new_score), issues=issues,
        logs=logs, violations=[], rollback=False,
        execution_time_ms=round(elapsed, 2), tokens=token_list, ast=ast_dict,
        pipeline_stages=stages, metrics=_build_metrics(final_metrics, elapsed),
    )


def _build_metrics(m, elapsed_ms: float) -> dict:
    """Convert RuntimeMonitor metrics to a JSON-serialisable dict."""
    return {
        "instruction_count":    m.instruction_count,
        "arithmetic_ops":       m.arithmetic_operations,
        "assignment_ops":       m.assignment_operations,
        "print_ops":            m.print_operations,
        "variables_accessed":   len(m.variables_accessed),
        "execution_time_ms":    round(elapsed_ms, 2),
    }


def _fail(h, start, error, logs, stages, tokens) -> PipelineResult:
    elapsed = (time.perf_counter() - start) * 1000
    score = get_trust(h)
    from core.helpers import token_to_dict
    token_list = [token_to_dict(t) for t in tokens] if tokens else []
    return PipelineResult(
        success=False, output=[], execution_mode="failed",
        trust_score=score, trust_level=trust_level(score), issues=[],
        logs=logs, violations=[error], rollback=False,
        execution_time_ms=round(elapsed, 2), tokens=token_list, ast=None,
        pipeline_stages=stages, error=error,
    )
