from argparse import ArgumentParser
from importlib import import_module
import os
import sys
from types import FunctionType

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

if __name__ == "__main__":
    parser = ArgumentParser(
        prog='QTasks',
        description='QueueTasks framework',
        epilog='Text at the bottom of help'
    )

    parser.add_argument("start")
    parser.add_argument("-A", "-app")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    
    start = args.start
    
    if start == "worker":
        
        app_arg: str = args.A
        file_path, app_var = app_arg.split(':')[0], app_arg.split(':')[-1]
        
        file = import_module(file_path)
        app = getattr(file, app_var)
        
        if isinstance(app, FunctionType):
            app = app()
        
        app.run_forever()
    
    if start == "web":
        # Эксперементально!
        import qtasks_webview.webview as webview
        import uvicorn
        
        app_arg: str = args.A
        app_port: int = args.port
        
        file_path, app_var = "".join(app_arg.split('.')[:-1]), app_arg.split('.')[-1]
        
        file = import_module(file_path)
        app = getattr(file, app_var)
        webview.app_qtasks = app
        uvicorn.run(webview.app, port=app_port)
