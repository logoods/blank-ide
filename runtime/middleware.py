from typing import Callable, List


class Middleware:
    """
    before/after hook 系统 / Before/after hook system.
    在 Cell/Workflow 执行前后插入自定义逻辑。
    Inject custom logic before and after Cell/Workflow execution.

    用法 / Usage:
        mw = Middleware()

        @mw.before
        def log_before(ctx):
            print("before", ctx)

        @mw.after
        def log_after(ctx, result):
            print("after", result)
    """

    def __init__(self):
        self._before: List[Callable] = []
        self._after: List[Callable] = []

    def before(self, fn: Callable) -> Callable:
        """注册 before hook，可作装饰器使用。/ Register a before hook, usable as decorator."""
        self._before.append(fn)
        return fn

    def after(self, fn: Callable) -> Callable:
        """注册 after hook，可作装饰器使用。/ Register an after hook, usable as decorator."""
        self._after.append(fn)
        return fn

    def run_before(self, ctx: dict) -> None:
        for fn in self._before:
            fn(ctx)

    def run_after(self, ctx: dict, result) -> None:
        for fn in self._after:
            fn(ctx, result)
