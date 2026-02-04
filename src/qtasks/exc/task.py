"""Task exceptions."""


class TaskCancelError(RuntimeError):
    """
    The exception thrown when a task is canceled.
    
        Can be intercepted in Worker to handle task cancellations.
    """

    def __init__(self, *args):
        """Initializing an exception."""
        super().__init__(*args)
