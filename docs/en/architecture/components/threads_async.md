# Components: threads and asynchrony

This page describes how QTasks organizes the launch of components in server mode,
how execution threads are formed, and where exactly asynchrony occurs in the architecture.

This refers exclusively to the application's server mode. In client mode, no
background threads, processing cycles, or workers are launched.

---

## The role of Starter in the architecture

A separate component, **Starter**, is used to launch QTasks in server mode.

Starter is responsible for the initial initialization of execution threads and
managing the life cycle of components. Its task is to start the system and stop
it correctly without interfering with the internal logic of the components themselves.

Starter:

* accepts application launch parameters;
* distributes them among components;
* starts and stops components;
* initiates the launch of plugins.
Starter **does not determine** how components will work after launch.
* starts and stops components;
* initiates the launch of plugins.

At the same time, Starter **does not determine** how components will work after
launch. The execution model, queues, blocking, and asynchrony are completely
determined by the components themselves.

---

## Using the default Starter

Starter is used automatically when the application is launched via `app.run_forever()`.

Depending on the type of application, the appropriate implementation is used:

* `AsyncStarter` — for `qtasks.asyncio.QueueTasks`;
* `SyncStarter` — for `qtasks.QueueTasks`.

If necessary, Starter can be replaced with a custom implementation when
saving the contract.

---

## Startup sequence

Starter launches components in a strictly defined order.

### Launch

1. All registered plugins are launched:

   * Starter plugins;
   * Component plugins.

   `start()` is called for each plugin.

2. Worker is launched via the call:

   ```text
   worker.start(num_workers)
   ```

3. Broker is started, to which a reference to Worker is passed:

   ```text
   broker.start(worker)
   ```

At this stage, the system is considered to be running and ready to process tasks.

---

## Shutdown sequence

The system is shut down in reverse order and is also controlled by Starter.

1. The main components are shut down one by one:

   * Broker;
   * Worker;
   * Storage;
   * GlobalConfig (if present).

   `stop()` is called for each component.
1.1. If `_global_loop` was created during operation, it is also stopped.

2. After the components are stopped, all running plugins are stopped via `stop()`.

This sequence ensures that background processes are terminated correctly and
resources are freed.

---

!!! note
   The `GlobalConfig` component is an optional core component. Although
   it has a default implementation, it may be absent.
   In all places where it needs to be started or stopped, you must first check
   that the component exists (is not equal to `None`).

---

## Component startup architecture diagram

In simplified form, the startup and dependency diagram for components looks like
this:

```text
Starter
  ├── Worker
  ├── Broker
  │     └── Storage
  │           └── GlobalConfig (optional)
```

This diagram only reflects the startup hierarchy and dependencies, but does not
define internal execution models.

---

## Asynchrony as a local property

In the QTasks architecture, asynchrony is not a global application state.

* Starter only initiates the launch of components;
* each component independently determines:

  * whether to use an event loop;
  * how to organize queues;
  * which synchronization mechanisms to use.

This allows you to combine synchronous and asynchronous components within a
single system and adapt the execution model to a specific infrastructure.

---

## Architectural invariants

* Server mode is initiated exclusively through Starter;
* Starter manages the lifecycle, but not the execution logic;
* Asynchrony is localized within components;
* The order of component startup and shutdown is fixed and predictable.

This approach makes execution threads in QTasks manageable and transparent even
in complex usage scenarios.
