class Workflow:
    """
    顺序执行一组 Cell 的流程容器。
    Sequential runner for a list of Cells.
    """

    def __init__(self, steps):
        # 步骤列表（每个 step 需有 run() 方法）/ List of steps (each must have run())
        self.steps = steps

    def run(self):
        """顺序执行所有步骤，返回最后一步结果。
        Run all steps in order, return the last result."""
        result = None
        for step in self.steps:
            result = step.run()
        return result
