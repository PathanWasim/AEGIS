"""
AEGIS Bytecode VM — Instruction definitions.

A simple stack-based bytecode instruction set for the AEGIS VM.
Each instruction is one opcode + an optional operand.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


class OpCode(Enum):
    # Stack ops
    PUSH        = auto()  # PUSH <literal>         → push value onto stack
    LOAD        = auto()  # LOAD <name>            → push env[name]
    STORE       = auto()  # STORE <name>           → env[name] = pop()

    # Arithmetic
    ADD         = auto()
    SUB         = auto()
    MUL         = auto()
    DIV         = auto()
    MOD         = auto()

    # Comparison  (result: 1 true / 0 false)
    EQ          = auto()
    NEQ         = auto()
    LT          = auto()
    LTE         = auto()
    GT          = auto()
    GTE         = auto()

    # I/O
    PRINT       = auto()

    # Control flow
    JUMP        = auto()  # JUMP <offset>          → ip = offset
    JUMP_IF_FALSE = auto()  # JUMP_IF_FALSE <offset> → if pop()==0: ip=offset

    # Program control
    HALT        = auto()


@dataclass
class Instruction:
    """A single bytecode instruction."""
    opcode: OpCode
    arg: Optional[Any] = None
    line: int = 0  # source line for debugging

    def __str__(self) -> str:
        if self.arg is not None:
            return f"{self.opcode.name:<18} {self.arg}"
        return self.opcode.name

    def to_dict(self) -> dict:
        return {
            "opcode": self.opcode.name,
            "arg": self.arg,
            "line": self.line,
        }
