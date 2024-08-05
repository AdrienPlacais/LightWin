"""Define helper function applying on commands."""

from lightwin.core.commands.command import Command
from lightwin.core.instruction import Instruction


def apply_commands(
    instructions: list[Instruction], freq_bunch: float
) -> list[Instruction]:
    """Apply all the implemented commands."""
    index = 0
    while index < len(instructions):
        instruction = instructions[index]

        if isinstance(instruction, Command):
            instruction.set_influenced_elements(instructions)
            if instruction.is_implemented:
                instructions = instruction.apply(
                    instructions, freq_bunch=freq_bunch
                )
        index += 1
    return instructions
