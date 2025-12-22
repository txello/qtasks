# Components: abstract classes

This page describes the role and structure of abstract classes in the QTasks architecture.
Abstract classes form component contracts and are a key mechanism for
system-wide consistency.

In QTasks, abstract classes are not an auxiliary element, but the foundation of
the architecture:
they define the permissible behavior of components, their interfaces, and extension
points.

---

## Role of abstract classes

Each main and additional QTasks component must inherit from
the corresponding abstract class. These classes:

* define the contract for the component's interaction with the system;
* fix the mandatory methods and their signatures;
* define the model of synchronous and asynchronous execution;
* serve as a single source of documentation and typing.

If a component does not implement a mandatory method declared via `@abstractmethod`,
its creation will result in a Python-level error before the system even starts.

---

## Basic naming

All abstract component classes follow a single naming pattern:

* `Base<Component>` — abstract class;
* `(A)sync<WorkingMethod><Component>` — concrete implementation.

Example:

* `BaseStorage` — storage component contract;
* `AsyncRedisStorage` — asynchronous implementation of Redis-based storage.

This naming convention makes the architecture self-documenting and allows you to
immediately determine the role and execution model of the component.

---

## Separation into Async and Sync

Abstract classes use parameterization via Generic[TAsyncFlag] for strict separation
of synchronous and asynchronous components.

* `TAsyncFlag = True` — asynchronous component;
* `TAsyncFlag = False` — synchronous component.

This separation is reflected in method types through `@overload`, for example:

* `self: BaseBroker[Literal[True]]` — asynchronous context;
* `self: BaseBroker[Literal[False]]` — synchronous context.

Architectural rule:

* asynchronous components can work with synchronous functions;
* synchronous components do not allow asynchronous functions to be called.

This restriction is intentionally strict and prevents implicit runtime errors.

---

## Component constructor

Each abstract class defines its own `__init__`, through which the component
initialization passes.

Through the constructor:

The constructor:

* passes mandatory dependencies;
* sets configuration parameters;
* fixes component invariants.

The set of parameters varies between base classes, but the idea of centralized
initialization is common to all components.

---

## Required methods and default behavior

Abstract classes in QTasks can contain:

* methods marked with `@abstractmethod`, which must be implemented;
* methods with default implementation;
* helper methods used within the component.

Thus, the contract includes not only signatures, but also basic behavior,
which is considered correct for a given component type.

---

## Documentation and typing

Each method in abstract classes is accompanied by documentation in the
Google docstring format.

This ensures:

* a consistent documentation style throughout QTasks;
* synchronization of the architectural description and the code;
* correct operation of the IDE, static analysis, and autocompletion.

An abstract class is the canonical source of information about how a component
should behave.

---

## Abstract plugin classes

The same architectural model applies to plugins.

* Base plugin class: `BasePlugin`;
* Specific implementations follow the same pattern `(A)sync<WorkingMethod>Plugin`.

Example:

* `BasePlugin`;
* `AsyncPydanticWrapperPlugin`.

This ensures consistency between components and plugins and simplifies their
joint use.

---

## Architectural invariants

* Any component must inherit from `Base<Component>`;
* Failure to comply with the contract results in an error during class creation.
* Async/Sync separation is fixed at the type level.
* Documentation and typing are part of the contract.

These rules make the QTasks architecture strict, predictable, and extensible
without hidden agreements.
