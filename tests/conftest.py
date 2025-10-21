import os
import sys
import time
import threading
import subprocess
import signal
from collections import deque
from pathlib import Path

import pytest


parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, parent_dir)


def pytest_collection_modifyitems(session, config, items):
    def key(item):
        p = Path(str(item.fspath))
        parts = [s.lower() for s in p.parts]
        is_async = "async" in parts  # папка tests/async
        # async -> 0 (раньше), sync/прочее -> 1 (позже)
        return (0 if is_async else 1, str(p))
    items.sort(key=key)


def _start_process(script_path: Path) -> subprocess.Popen:
    # Максимально «безбуферный» вывод
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    # Кроссплатформенно запускаем в новой группе процессов
    creationflags = 0
    preexec_fn = None
    if sys.platform.startswith("win"):
        # Чтобы потом можно было послать CTRL_BREAK_EVENT всей группе
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        # Новый session id → отдельная группа для последующего os.killpg
        preexec_fn = os.setsid # type: ignore

    return subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,               # построчный вывод
        env=env,
        creationflags=creationflags,
        preexec_fn=preexec_fn,
    )


def _kill_process_tree(proc: subprocess.Popen):
    if proc.poll() is not None:
        return

    try:
        if sys.platform.startswith("win"):
            # Сначала мягко: CTRL_BREAK_EVENT группе процесса
            try:
                proc.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
                proc.wait(timeout=5)
            except Exception:
                pass
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
        else:
            # Посылаем SIGTERM всей группе
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM) # type: ignore
            except ProcessLookupError:
                return
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Эскалация до SIGKILL
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL) # type: ignore
                except ProcessLookupError:
                    pass
    finally:
        # Последний шанс
        if proc.poll() is None:
            proc.kill()


@pytest.fixture(scope="package", autouse=True)
def run_server(app_script: str):
    """
    Запуск QTasks-сервера в отдельном процессе с live-логами и гарантированным убийством дерева процессов.
    """
    script_path = Path(__file__).parent / "apps" / app_script
    assert script_path.exists(), f"Script not found: {script_path}"

    process = _start_process(script_path)

    # Кольцевая буферизация последних строк (на случай фейла старта)
    tail = deque(maxlen=200)
    stop_reader = threading.Event()

    def _stream_output(pipe):
        # Печатаем в stdout pytest'а, а также складываем в tail
        for line in iter(pipe.readline, ""):
            msg = f"[SERVER] {line}"
            tail.append(msg.rstrip("\n"))
            # Пишем сразу, чтобы видно было при `pytest -s`
            sys.stdout.write(msg)
            sys.stdout.flush()
            if stop_reader.is_set():
                break
        try:
            pipe.close()
        except Exception:
            pass

    reader = threading.Thread(target=_stream_output, args=(process.stdout,), daemon=True)
    reader.start()

    # Ожидание старта: либо сервер сообщит в логах «готов», либо просто подождём таймаут
    # Настраивается переменной окружения, по умолчанию 8 секунд
    startup_timeout = float(os.getenv("QTS_TEST_STARTUP_TIMEOUT", "8"))
    started = False
    start_deadline = time.time() + startup_timeout

    # Хелсчек: ждём явный маркер в логах или просто конец таймаута
    # Если у вас в приложении есть явный лог «Server started» — добавьте строку ниже в condition
    START_MARKERS = ("Started", "Running", "Listening", "QTasks started", "Server ready")

    while time.time() < start_deadline:
        if process.poll() is not None:
            # Упал во время старта — покажем хвост логов и упадём
            stop_reader.set()
            reader.join(timeout=1)
            tail_text = "\n".join(tail)
            raise RuntimeError(
                f"Server exited too early (code {process.returncode}). "
                f"Last log lines:\n{tail_text}"
            )
        # Простая эвристика готовности по логам
        if any(any(m in line for m in START_MARKERS) for line in tail):
            started = True
            break
        time.sleep(0.05)

    if not started:
        # Сервер не подтвердил готовность — но мог подняться молча.
        # Если нужно жёстко требовать маркер — раскомментируйте падение:
        # stop_reader.set(); reader.join(1)
        # raise TimeoutError(f"Server did not start within {startup_timeout}s.\nLast logs:\n" + "\n".join(tail))
        pass

    # На случай мгновенной смерти после «старта»
    if process.poll() is not None:
        stop_reader.set()
        reader.join(timeout=1)
        tail_text = "\n".join(tail)
        raise RuntimeError(
            f"Server died right after start (code {process.returncode}). "
            f"Last log lines:\n{tail_text}"
        )

    # --- тесты выполняются ---
    try:
        yield
    finally:
        # Завершение процесса + читателя
        stop_reader.set()
        try:
            process.terminate()
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _kill_process_tree(process)
        except Exception:
            _kill_process_tree(process)
        # Дадим потоку дочитать то, что осталось в пайпе
        reader.join(timeout=2)
