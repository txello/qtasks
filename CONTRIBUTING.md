# Contributing to QTasks

Thank you for your interest in contributing to QTasks.

QTasks is a component-oriented task queue framework focused on explicit architecture, replaceable components, and typed data exchange via dataclasses. Contributions are welcome from developers of all levels — from documentation improvements to deep architectural extensions.

---

## Table of Contents

* Code of Conduct
* Ways to Contribute
* Getting Started
* Development Environment
* Running Tests
* Code Style & Conventions
* Architecture Principles
* Working with Components
* Writing Plugins
* Submitting Changes
* Versioning & Changelog
* Security Issues

---

## Code of Conduct

Be respectful, constructive, and professional.

Disagreements about architecture or implementation details are normal — discussions should focus on technical merit and long‑term maintainability.

---

## Ways to Contribute

You can contribute in several ways:

### 1. Bug Reports

* Provide a minimal reproducible example
* Include Python version
* Include QTasks version
* Include Broker/Storage configuration details
* Include full traceback

### 2. Feature Requests

* Clearly describe the use case
* Explain why existing components/plugins are insufficient
* Describe how it aligns with QTasks architecture

### 3. Documentation Improvements

* Improve clarity
* Add examples
* Fix typos
* Add architectural explanations

### 4. Code Contributions

* Core components
* Plugins
* CLI extensions
* Test improvements
* Performance optimizations

---

## Getting Started

### 1. Fork the repository

```
git clone https://github.com/txello/qtasks.git
cd qtasks
```

### 2. Create a virtual environment

```
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 3. Install in editable mode

```
pip install -e .
```

---

## Development Environment

Recommended:

* Python 3.10–3.13
* tox (for multi-version testing)
* Redis (for integration tests)

Run all environments:

```
tox
```

---

## Running Tests

### Run with pytest

```
pytest
```

### Run via tox

```
tox -e py311
```

If your change affects:

* async behavior
* priority queues
* context managers
* cross-component communication

Please ensure tests cover these scenarios explicitly.

---

## Code Style & Conventions

### General Principles

* Explicit is better than implicit
* Avoid hidden global state
* Prefer typed dataclasses for inter-component communication
* No magic side-effects

### Typing

* Use type hints everywhere
* Avoid untyped Any unless justified
* Public APIs must be fully typed

### Async/Sync Separation

* Async and Sync implementations must remain clearly separated
* Do not mix event loop assumptions

### Logging

* Use ctx.get_logger() inside tasks
* Do not introduce hardcoded loggers in core components

---

## Architecture Principles

QTasks is built around replaceable components:

* Broker
* Worker
* Storage
* GlobalConfig
* Starter
* Router (optional)
* Plugins

Key rule:

> Components should implement minimal responsibility and communicate only via schemas.

Do not:

* Introduce cross-component tight coupling
* Embed business logic into infrastructure components

---

## Working with Components

When modifying or creating a component:

1. Respect the base abstract class
2. Keep constructor signature stable
3. Accept config via `config=config`
4. Avoid global singletons
5. Ensure testability via component replacement

If your component requires external resources (Redis, DB, etc.), ensure:

* Graceful startup/shutdown
* Proper async context handling
* Clear failure states

---

## Writing Plugins

Plugins must:

* Be optional
* Not modify core behavior silently
* Be explicitly registered

Good plugin characteristics:

* Self-contained
* Well-documented
* Minimal coupling

Examples of acceptable plugin types:

* Retry strategies
* Task concurrency strategies
* Metrics collectors
* Monitoring tools
* Distribution mechanisms (e.g., gRPC)

---

## Submitting Changes

### 1. Create a branch

```
git checkout -b feature/your-feature-name
```

### 2. Commit clearly

Commit messages should follow structure:

```
Component: short description

Detailed explanation of the change.
```

### 3. Open Pull Request

Include:

* Description of the problem
* Architectural reasoning
* Test coverage details
* Backward compatibility notes

---

## Versioning & Changelog

QTasks follows semantic versioning:

MAJOR.MINOR.PATCH

* MAJOR — breaking changes
* MINOR — new features (backward compatible)
* PATCH — bug fixes

If your PR introduces a breaking change, clearly document it.

---

## Security Issues

If you discover a security vulnerability:

* Do NOT open a public issue
* Contact the maintainer directly
* Provide detailed reproduction steps

---

## Final Notes

QTasks is designed to be:

* Explicit
* Replaceable
* Extensible
* Testable

When contributing, think not only about solving the immediate problem, but also about:

* Long-term maintainability
* Market readiness
* Plugin ecosystem growth
* Architectural clarity

Thank you for helping improve QTasks.
