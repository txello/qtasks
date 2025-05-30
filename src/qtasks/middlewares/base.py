class BaseMiddleware:
    """
    `BaseMiddleware` - Абстрактный класс, который является фундаментом для классов Мидлварей.

    ## Пример

    ```python
    from qtasks.middlewares.base import BaseMiddleware
    
    class MyMiddleware(BaseMiddleware):
        def __init__(self, name: str):
            super().__init__(name=name)
    ```
    """
    def __init__(self,
            name: str
        ):
        """Экземпляр класса.

        Args:
            name (str): Имя.
        """
        self.name = name
