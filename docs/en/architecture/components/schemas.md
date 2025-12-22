# Components: Data Schemas

This page describes the role of data schemas in the QTasks architecture and the
rules for their use when components interact.

Data schemas are the primary mechanism for transferring information between components.
They form a strict, typed contract that replaces direct exchange of objects and
execution state.

---

## Role of Schemas in Architecture

When data needs to be transferred from one component to another, both components
must adhere to an agreed-upon data schema.

Schemas:

* define the exact structure of the transmitted data;
* fix the state of the task at each stage of the life cycle;
* allow you to serialize, store, and restore data;
* serve as the basis for typing and static analysis.

The only exception to this rule is adding a task to a Worker via the
`add` contract, where data is passed as parameters and converted to schemas
on the Worker side.

---

## General schema rules

All data schemas in QTasks are subject to uniform architectural rules.

### 1. Strict structure

Each schema must be a dataclass-like structure with explicitly defined fields and
types. This ensures:

* compatibility with `mypy` and other typing tools;
* predictability of the data structure;
* unambiguity of contracts between components.

Schemas are not intended to store logic and should not contain behavior that goes
beyond data representation.

### 2. Schema assembly on the sender side

Schema formation always occurs in the sender component.

This rule ensures that the receiving component:

* receives already validated data;
* does not depend on the details of structure formation;
* can work exclusively with the contract.

The exception is Worker (`add`), which accepts task parameters and independently
forms the corresponding schemas.

### 3. Schema stability

A schema is considered part of a public architectural contract. Changes to
schemas must be deliberate and compatible, as they directly affect the
interaction of components and plugins.

---

## Key QTasks schemas

Below are the main schemas used in the QTasks architecture and their purpose.

### QueueConfig

A configuration schema used by all components starting with `QueueTasks`. It defines
the basic parameters of the system and is passed during component initialization.

---

### Task

The task result schema returned to the client. Represents the aggregated state of
the task, taking into account its current or final status.

---

### BaseTaskStatusSchema

The basic task status schema. Used to represent the status of the task at
individual stages of execution.

Derived schemas:

* `TaskStatusNewSchema`;
* `TaskStatusProcessSchema`;
* `TaskStatusSuccessSchema`;
* `TaskStatusErrorSchema`;
* `TaskStatusCancelSchema`.

The main consumer of these schemas is the Storage component.

---

### TaskExecSchema

Schema containing information about the task and its execution function. Used
primarily by Worker when preparing a task for execution and transferring it to `TaskExecutor`.

---

### TaskPrioritySchema

Schema for adding a task to Worker. Stores input data passed via `add`,
as well as the execution priority.

This schema is the entry point for a task into the Worker execution queue.

---

### BaseTaskCls

Schema of a pre-assembled task, representing an alternative way of creating a task.

Derivative variants:

* `AsyncTaskCls`;
* `SyncTaskCls`.

These schemas allow you to work with a task as a call object, rather than through
a direct call to `add_task`.

---

### InitsExecSchema

Schema for event functions used in the QTasks event system.

An example of use is handlers of the type:

```python
@app.events.on.worker_running
```

---

### GlobalConfigSchema

The main schema of the `GlobalConfig` component, designed to store and
distribute global parameters.

By default, the implementation uses Redis as the storage server.

---

### ArgMeta

The metadata schema for task arguments.

Stores:

* argument names;
* values;
* position or key;
* type annotations and auxiliary information.

Used primarily in `TaskExecutor` and plugins that need to understand the structure
of task arguments.

For plugins, `ArgMeta` is passed as a parameter in the corresponding triggers.

---

## Architectural invariants

* Components exchange only data schemas.
* Schemas do not contain execution logic.
* Schemas are formed before data is transferred.
* Schema stability is critical for component and plugin compatibility.

Data schemas form the "language" of interaction between QTasks components and ensure
the integrity of the architecture as it expands.
