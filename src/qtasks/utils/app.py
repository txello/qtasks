"""QTasks Utils."""


def get_app():
    """Get the current application."""
    import qtasks._state

    return qtasks._state.app_main
