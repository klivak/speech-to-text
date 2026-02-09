# Contributing to EchoScribe

## Quick Start
1. Fork the repository
2. Clone your fork
3. Create a branch: `git checkout -b feature/my-feature`
4. Install dev dependencies: `pip install -r requirements-dev.txt`
5. Install pre-commit hooks: `pre-commit install`
6. Make changes
7. Run tests: `pytest`
8. Run linter: `ruff check src/`
9. Commit and push
10. Open a Pull Request

## Code Style
- Python code follows Ruff defaults
- Comments in Ukrainian
- No emoji in code or comments
- Type hints for all functions
- Docstrings for classes and public methods

## Commit Messages
Format: `type: short description`
Types: feat, fix, docs, style, refactor, test, chore
Example: `feat: add floating microphone button`
