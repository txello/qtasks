"""Base middleware."""


class BaseMiddleware:
    """
    `BaseMiddleware` - An abstract class that is the foundation for Middleware classes.

    ## Example

    ```python
    from qtasks.middlewares.base import BaseMiddleware

    class MyMiddleware(BaseMiddleware):
        def __init__(self, name: str):
            super().__init__(name=name)
    ```
    """

    def __init__(self, name: str):
        """
        An instance of a class.

        Args:
            name (str): Name.
        """
        self.name = name
