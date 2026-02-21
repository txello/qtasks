# Security Policy

## Supported Versions

QTasks follows semantic versioning.

Security updates are provided for:

* The latest stable MAJOR release
* The most recent MINOR release within the previous MAJOR (if still actively used)

Older versions may not receive security patches.

---

## Reporting a Vulnerability

If you discover a security vulnerability in QTasks, please follow responsible disclosure principles.

### Do NOT:

* Open a public GitHub issue
* Publish exploit details
* Share proof-of-concept publicly

### Instead:

* Contact the maintainer directly
* Provide a clear description of the issue
* Include reproduction steps
* Include environment details (Python version, Broker, Storage, OS)
* Provide logs or tracebacks if relevant

You will receive acknowledgment of the report and an estimated timeline for assessment.

---

## Scope of Security Considerations

QTasks is a task queue framework. Security considerations include, but are not limited to:

* Broker message integrity
* Storage consistency and access control
* Task serialization/deserialization safety
* Remote execution vectors
* Plugin isolation boundaries
* CLI exposure risks
* Configuration injection via environment variables

Contributors must consider security impact when modifying:

* Serialization logic
* Network transports
* Plugin hooks
* Context management
* Global configuration handling

---

## Secure Development Guidelines

When contributing to QTasks, follow these principles:

### 1. Avoid Implicit Trust

* Never trust external task payloads
* Validate schemas strictly
* Avoid unsafe deserialization patterns

### 2. No Arbitrary Code Execution

* Do not introduce dynamic eval/exec
* Avoid reflection-based invocation unless strictly controlled

### 3. Explicit Configuration Handling

* Environment variables must be validated
* Configuration values must be type-safe

### 4. Isolation Between Components

* Do not leak internal state between components
* Avoid hidden shared mutable state

### 5. Safe Async Patterns

* Ensure proper cancellation handling
* Avoid unbounded queue growth
* Ensure graceful shutdown

---

## Dependency Management

* Keep dependencies minimal
* Avoid unnecessary third-party libraries
* Monitor dependency vulnerabilities

If a dependency vulnerability is discovered:

* Assess impact on QTasks
* Release a patched version if necessary
* Document mitigation steps

---

## Security in Plugins

Plugins must:

* Be explicitly registered
* Not override core security guarantees
* Clearly document any network exposure

Plugins introducing external communication (e.g., gRPC, HTTP, distributed routing) must document:

* Authentication strategy
* Transport security assumptions
* Failure isolation mechanisms

---

## Responsible Disclosure Timeline

Typical process:

1. Acknowledgment within a reasonable timeframe
2. Internal assessment and reproduction
3. Patch development
4. Coordinated disclosure
5. Release of patched version

If the issue is critical, a hotfix release may be issued.

---

## Security Philosophy

QTasks is designed with the following principles:

* Explicit behavior
* Replaceable components
* Minimal hidden logic
* Typed schema boundaries

Security is treated as an architectural concern, not an afterthought.

All contributors share responsibility for maintaining a secure ecosystem.

Thank you for helping keep QTasks secure.
