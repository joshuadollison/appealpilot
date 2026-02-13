# Engineering Rules

## Clean Code Rule (Required)
All code changes must follow Clean Code principles (Robert C. Martin) with priority on readability, maintainability, and simplicity.

### Core standards
- Write code that reads like clear prose.
- Prefer small, single-purpose functions and modules.
- Use meaningful, intention-revealing names.
- Keep control flow straightforward and easy to scan.
- Minimize comments; comments should explain *why*, not restate *what*.
- Remove dead code, duplication, and incidental complexity.
- Favor simple solutions first (KISS) and avoid speculative abstractions (YAGNI).
- Apply SOLID principles where they improve clarity and changeability.
- Keep dependencies explicit and boundaries clear.
- Leave each touched file cleaner than you found it (Boy Scout Rule).

### Definition of done for any change
- Readability improved or preserved.
- Complexity reduced or justified.
- Naming and structure make intent obvious.
- No unnecessary comments, indirection, or abstractions.
- Local design supports easy testing and future modification.
