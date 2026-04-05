# Contributing to My Wiki

Thank you for your interest in contributing! This document provides guidelines for contributions.

## Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest new features
- 📝 Improve documentation
- 🔧 Submit bug fixes
- ✨ Add new features

## Development Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/my-wiki.git
cd my-wiki

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install click pyyaml loguru openai

# Run tests
python -m pytest tests/
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for functions
- Keep functions under 50 lines

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### PR Guidelines

- Link related issues
- Describe the change and why it's needed
- Add tests for new features
- Update documentation if needed

## Reporting Issues

When reporting bugs, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Relevant logs (remove sensitive info)

## Feature Requests

For feature requests, please describe:

- The problem you're trying to solve
- Proposed solution
- Alternative solutions considered
- Potential impact on existing functionality

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the MIT License.