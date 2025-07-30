# Contributing to PayPal Merchant Troubleshooting

Thank you for your interest in contributing to the PayPal Merchant Troubleshooting application! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Git

### Development Setup
1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/pp-merchantai.git
   cd pp-merchantai
   ```

2. **Set up the development environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Start Elasticsearch**
   ```bash
   docker run -d --name elasticsearch -p 9200:9200 -e 'discovery.type=single-node' elasticsearch:8.11.0
   ```

4. **Generate sample data**
   ```bash
   python scripts/generate_sample_data.py
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

## 📝 Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints for function parameters and return values
- Write docstrings for all functions and classes
- Keep functions small and focused

### Project Structure
```
pp-merchantai/
├── app/                    # Main application code
│   ├── __init__.py
│   ├── main.py            # Application entry point
│   ├── api.py             # FastAPI routes
│   ├── models.py          # Pydantic models
│   ├── config.py          # Configuration
│   ├── elastic_client.py  # Elasticsearch client
│   └── analytics.py       # Analytics service
├── templates/             # HTML templates
├── scripts/              # Utility scripts
├── tests/                # Test files
└── docs/                 # Documentation
```

### Testing
- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Use pytest for testing framework

### Git Workflow
1. Create a feature branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

3. Push to your fork
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a Pull Request

### Commit Message Format
Use conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding tests
- `chore:` for maintenance tasks

## 🐛 Reporting Issues

When reporting issues, please include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Screenshots if applicable

## 💡 Feature Requests

For feature requests:
- Describe the feature clearly
- Explain the use case and benefits
- Provide examples if possible
- Consider implementation complexity

## 🔧 Development Tools

### Recommended IDE Setup
- VS Code with Python extension
- Pre-commit hooks for code quality
- Black for code formatting
- Flake8 for linting

### Pre-commit Setup
```bash
pip install pre-commit
pre-commit install
```

## 📚 Documentation

- Keep README.md updated
- Document new API endpoints
- Update demo guide for new features
- Add inline code comments for complex logic

## 🚀 Deployment

### Local Development
```bash
# Using Docker Compose
docker-compose up -d

# Manual setup
python scripts/generate_sample_data.py
uvicorn app.main:app --reload
```

### Production Deployment
- Use environment variables for configuration
- Set up proper logging
- Configure monitoring and health checks
- Use production-grade Elasticsearch setup

## 🤝 Code Review Process

1. All PRs require review from maintainers
2. Ensure CI/CD checks pass
3. Address review comments promptly
4. Keep PRs focused and manageable in size

## 📞 Getting Help

- Open an issue for bugs or questions
- Join our community discussions
- Check existing documentation first

Thank you for contributing to making PayPal merchant troubleshooting better! 🎉 