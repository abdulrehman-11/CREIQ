---
description: 
globs: 
alwaysApply: true
---

# Core Operational Rules

## Modes of Operation

1. **Plan Mode**
   - Gather all necessary information.
   - Work with the user to define a detailed plan.
   - No changes are made.

2. **Act Mode**
   - Implement changes strictly according to the approved plan.

## Mode Management

- Start in **Plan Mode**.
- Print `# Mode: PLAN` at the start of each Plan Mode response.
- Print `# Mode: ACT` at the start of each Act Mode response.
- Only switch to Act Mode when the user explicitly types `ACT`.
- Switch back to Plan Mode after every Act Mode response or when the user types `PLAN`.
- If the user requests action in Plan Mode, remind them that approval is required first.
- Always output the **full, updated plan** in every Plan Mode response.

# Clean Code Principles

- **Meaningful Names**: Choose clear, descriptive names that reveal intention.
- **Small Functions**: Functions should be small and do only one thing.
- **Single Responsibility Principle (SRP)**: Each module/class should have exactly one reason to change.
- **Expressive Code**: Code should be self-explanatory; minimize comments.
- **Error Handling**: Prefer exceptions over return codes.
- **DRY Principle**: Avoid code duplication at all costs.
- **Minimal Dependencies**: Keep code loosely coupled and modular.
- **Command-Query Separation**: A method should either perform an action or return data, not both.
- **Structured Error Handling**: Keep error management clean and separate.
- **Single Level of Abstraction**: Maintain consistent abstraction level within methods/functions.
- **Readability Over Cleverness**: Clear and readable code is always preferred over clever tricks.
- **Testing**: Write automated, small, fast, independent tests.
- **Testing Is Essential**: Code that is not tested cannot be considered clean.

---
