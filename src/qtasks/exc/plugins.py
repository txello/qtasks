"""Plugins exceptions."""


class TaskPluginTriggerError(Exception):
    """
    The exception thrown when the plugin trigger fires.
    
        Can be intercepted in Worker to process triggers.
    """

    def __init__(self, *args, **kwargs):
        """Initializing an exception."""
        super().__init__(*args)
        self.kwargs = kwargs
