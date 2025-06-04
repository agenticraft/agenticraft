# Contributing to AgentiCraft

Thank you for your interest in contributing to AgentiCraft! We love your input and appreciate your effort to make AI agent development simpler for everyone.

## 🎯 Our Philosophy

Before contributing, please read our [Philosophy](docs/philosophy.md) to understand our core principles:
- **Simplicity First**: If it's complex, it doesn't belong in core
- **Transparent by Default**: Show reasoning, not just results
- **Production-Ready**: Real-world usage drives decisions
- **Developer Joy**: APIs should be intuitive and delightful

## 🚀 Getting Started

### 1. Fork and Clone
```bash
git clone https://github.com/YOUR_USERNAME/agenticraft.git
cd agenticraft
```

### 2. Set Up Development Environment
```bash
make setup
# or manually:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev,test]"
pre-commit install
```

### 3. Validate Setup
```bash
python scripts/validate_env.py
```

## 📝 Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Changes
- Write clean, simple code
- Add tests for new functionality
- Update documentation
- Follow our code style

### 3. Run Checks
```bash
make check  # Runs lint, type-check, and tests
# or individually:
make lint
make type-check
make test
```

### 4. Commit Changes
```bash
git add .
git commit -m "component: clear description of change"
```

Commit message format:
- `core: add new reasoning pattern`
- `tools: implement web search tool`
- `docs: update installation guide`
- `fix: resolve memory leak in workflows`

### 5. Push and Create PR
```bash
git push origin your-branch-name
```

Then create a Pull Request on GitHub.

## 🏗️ Code Guidelines

### Style
- We use Black for formatting (line length: 88)
- We use Ruff for linting
- Type hints are required for all public APIs
- Google-style docstrings

### Testing
- Minimum 95% test coverage required
- Write unit tests for all new code
- Integration tests for cross-component features
- Use pytest fixtures for common setups

Example test:
```python
def test_agent_creation():
    """Test basic agent creation."""
    agent = Agent(name="test", instructions="Test agent")
    assert agent.name == "test"
    assert agent.instructions == "Test agent"
```

### Documentation
- Every public function needs a docstring
- Include usage examples in docstrings
- Update relevant .md files for features
- Add to changelog for notable changes

## 🔧 Common Tasks

### Adding a New Tool
1. Create tool in `agenticraft/tools/`
2. Add tests in `tests/tools/`
3. Document in `docs/guides/creating-tools.md`
4. Add example in `examples/`

### Adding a Provider
1. Implement provider interface in `agenticraft/providers/`
2. Add configuration in `core/config.py`
3. Write integration tests
4. Update provider documentation

### Improving Performance
1. Profile with real workloads
2. Optimize hot paths only
3. Maintain simplicity
4. Document any trade-offs

## 🐛 Reporting Issues

### Bug Reports
Include:
- Python version
- AgentiCraft version
- Minimal reproduction code
- Expected vs actual behavior
- Full error traceback

### Feature Requests
Include:
- Use case description
- Why existing features don't work
- Proposed API (if applicable)
- How it aligns with our philosophy

## 📊 Pull Request Process

1. **PR Title**: Clear and descriptive
2. **Description**: What, why, and how
3. **Tests**: All tests must pass
4. **Coverage**: Must maintain 95%+ coverage
5. **Documentation**: Updated as needed
6. **Review**: Address feedback promptly

### PR Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Changelog entry added (if needed)
- [ ] Code follows style guidelines
- [ ] Commit messages are clear
- [ ] PR description is complete

## 🎉 Recognition

Contributors are recognized in:
- [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Release notes
- Project documentation

## 💬 Getting Help

- **Discord**: [Join our community](https://discord.gg/agenticraft)
- **Discussions**: [GitHub Discussions](https://github.com/agenticraft/agenticraft/discussions)
- **Issues**: [GitHub Issues](https://github.com/agenticraft/agenticraft/issues)

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make AgentiCraft better! 🚀
