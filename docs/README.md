# codeindex Documentation

Welcome to the codeindex documentation! This guide will help you navigate through all available documentation.

## 📚 Table of Contents

### For Users

#### Getting Started
- **[Getting Started Guide](guides/getting-started.md)** - Installation, quick start, and basic usage
- **[Configuration Guide](guides/configuration.md)** - All configuration options and examples
- **[Advanced Usage](guides/advanced-usage.md)** - Parallel scanning, CI/CD, custom prompts

### For Contributors

#### Development
- **[Development Setup](development/setup.md)** - Local development environment setup
- **[Contributing Guide](guides/contributing.md)** - How to contribute, TDD workflow, code style
- **[CHANGELOG](../CHANGELOG.md)** - Version history and changes

### Project Planning

#### Roadmap & Planning
- **[2025 Q1 Roadmap](planning/roadmap/2025-Q1.md)** - Quarterly goals and milestones
- **[Epics](planning/epics/)** - High-level feature initiatives
- **[Features](planning/features/)** - Specific feature designs
- **[Stories](planning/stories/)** - User stories and acceptance criteria
- **[Tasks](planning/tasks/)** - Detailed implementation tasks

### Architecture

#### Design Documents
- **[Initial Design](architecture/design/initial-design.md)** - Original design document
- **[Diagrams](architecture/diagrams/)** - Architecture diagrams (future)

#### Architecture Decision Records (ADR)
- **[ADR-001: Use tree-sitter for parsing](architecture/adr/001-use-tree-sitter-for-parsing.md)** - Why tree-sitter over AST/LSP
- **[ADR-002: External AI CLI integration](architecture/adr/002-external-ai-cli-integration.md)** - AI integration strategy

### API Reference

> Coming soon: Auto-generated API documentation

## 🗺️ Documentation Structure

```
docs/
├── README.md                    # This file
├── guides/                      # User guides
│   ├── getting-started.md
│   ├── configuration.md
│   ├── advanced-usage.md
│   └── contributing.md
├── development/                 # Development docs
│   └── setup.md
├── planning/                    # Agile planning
│   ├── roadmap/
│   ├── epics/
│   ├── features/
│   ├── stories/
│   └── tasks/
├── architecture/               # Architecture docs
│   ├── adr/                    # Decision records
│   ├── design/                 # Design documents
│   └── diagrams/               # Architecture diagrams
└── api/                        # API reference (future)
```

## 🚀 Quick Links

### I want to...

- **Get started quickly** → [Getting Started Guide](guides/getting-started.md)
- **Configure codeindex** → [Configuration Guide](guides/configuration.md)
- **Set up for development** → [Development Setup](development/setup.md)
- **Contribute code** → [Contributing Guide](guides/contributing.md)
- **See the roadmap** → [2025 Q1 Roadmap](planning/roadmap/2025-Q1.md)
- **Understand architecture** → [ADR Index](architecture/adr/)

## 📖 Documentation Philosophy

We follow these principles for documentation:

1. **Code as Documentation** - Clear code with good docstrings
2. **Examples First** - Show examples before explaining theory
3. **Progressive Disclosure** - Start simple, add complexity gradually
4. **Keep It Updated** - Documentation is updated with code changes
5. **Architecture Decisions** - Record important decisions in ADRs

## 🤝 Contributing to Docs

Found a typo or want to improve documentation?

1. Fork the repository
2. Edit the relevant `.md` file
3. Submit a pull request

See [Contributing Guide](guides/contributing.md) for details.

## 📝 Writing Style

- Use clear, concise language
- Provide code examples
- Include shell commands where applicable
- Use diagrams for complex concepts
- Keep paragraphs short

## 🔗 External Resources

- [tree-sitter Documentation](https://tree-sitter.github.io/)
- [Click Documentation](https://click.palletsprojects.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Need help?** Open an [issue](https://github.com/yourusername/codeindex/issues) or start a [discussion](https://github.com/yourusername/codeindex/discussions).
