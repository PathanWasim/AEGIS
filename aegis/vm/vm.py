"""
AEGIS Stack-Based Virtual Machine.

Executes a flat list of Instruction objects produced by BytecodeCompiler.
Maintains: operand stack, environment (variables), output buffer, IP.
"""
from typing import List, Any, Dict
from .bytecode import Instruction, OpCode


MAX_INT =  2_147_483_647
MIN_INT = -2_147_483_648
MAX_OPS = 200_000


class VMRuntimeError(Exception):
    pass


class AegisVM:
    def __init__(self):
        self.stack:  List[Any]       = []
        self.env:    Dict[str, Any]  = {}
        self.output: List[str]       = []
        self.ip:     int             = 0
        self._ops:   int             = 0

    # ── Public ────────────────────────────────────────────────────
    def run(self, instructions: List[Instruction]) -> List[str]:
        """Execute instructions, return output lines."""
        self.stack  = []
        self.env    = {}
        self.output = []
        self.ip     = 0
        self._ops   = 0

        while self.ip < len(instructions):
            instr = instructions[self.ip]
            self.ip += 1
            self._ops += 1
            if self._ops > MAX_OPS:
                raise VMRuntimeError(f"Operation limit exceeded ({MAX_OPS})")
            self._execute(instr)

        return self.output

    # ── Dispatcher ────────────────────────────────────────────────
    def _execute(self, instr: Instruction) -> None:
        op = instr.opcode

        if op == OpCode.PUSH:
            self.stack.append(instr.arg)

        elif op == OpCode.LOAD:
            name = instr.arg
            if name not in self.env:
                raise VMRuntimeError(f"Undefined variable: '{name}'")
            self.stack.append(self.env[name])

        elif op == OpCode.STORE:
            self.env[instr.arg] = self._pop()

        elif op == OpCode.PRINT:
            self.output.append(str(self._pop()))

        elif op == OpCode.ADD:
            b, a = self._pop(), self._pop()
            self._push_checked(a + b)

        elif op == OpCode.SUB:
            b, a = self._pop(), self._pop()
            self._push_checked(a - b)

        elif op == OpCode.MUL:
            b, a = self._pop(), self._pop()
            self._push_checked(a * b)

        elif op == OpCode.DIV:
            b, a = self._pop(), self._pop()
            if b == 0:
                raise VMRuntimeError("Division by zero")
            self.stack.append(a // b)

        elif op == OpCode.MOD:
            b, a = self._pop(), self._pop()
            if b == 0:
                raise VMRuntimeError("Modulo by zero")
            self.stack.append(a % b)

        elif op == OpCode.EQ:
            b, a = self._pop(), self._pop()
            self.stack.append(1 if a == b else 0)
        elif op == OpCode.NEQ:
            b, a = self._pop(), self._pop()
            self.stack.append(1 if a != b else 0)
        elif op == OpCode.LT:
            b, a = self._pop(), self._pop()
            self.stack.append(1 if a < b else 0)
        elif op == OpCode.LTE:
            b, a = self._pop(), self._pop()
            self.stack.append(1 if a <= b else 0)
        elif op == OpCode.GT:
            b, a = self._pop(), self._pop()
            self.stack.append(1 if a > b else 0)
        elif op == OpCode.GTE:
            b, a = self._pop(), self._pop()
            self.stack.append(1 if a >= b else 0)

        elif op == OpCode.JUMP:
            self.ip = instr.arg

        elif op == OpCode.JUMP_IF_FALSE:
            if not self._pop():
                self.ip = instr.arg

        elif op == OpCode.HALT:
            self.ip = len([])  # terminate

    # ── Helpers ───────────────────────────────────────────────────
    def _pop(self) -> Any:
        if not self.stack:
            raise VMRuntimeError("Stack underflow")
        return self.stack.pop()

    def _push_checked(self, value: int) -> None:
        if value < MIN_INT or value > MAX_INT:
            raise VMRuntimeError(f"Integer overflow: {value}")
        self.stack.append(value)
