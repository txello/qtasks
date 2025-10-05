"""QTasks Utils."""


def get_app():
    """Получить текущее приложение."""
    import qtasks._state

    return qtasks._state.app_main
