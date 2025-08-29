class BaseScenario:
    maximum_steps = 10  # Default maximum steps

    def __init__(self, role):
        self.role = role
        self.state = {"step": 0}
        self.name = "Base Scenario"
        self.description = "Base scenario class"

    def execute_step(self, step):
        """Execute step based on role and return image path"""
        self.state["step"] = step
        method_name = f"step_{step}"
        if hasattr(self, method_name):
            x = getattr(self, method_name)()
            print(f'return value: {x}')
            return x
        return None  # Return None if step doesn't exist
