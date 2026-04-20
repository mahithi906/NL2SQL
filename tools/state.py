class GlobalAgentState:
    """Tracks debug agent retry attempts."""

    def __init__(self):
        self.debug_triggered_times = 0

    def reset(self):
        """Reset debug counter."""
        self.debug_triggered_times = 0


# Single shared instance
GLOBAL_STATE = GlobalAgentState()
STATE = GLOBAL_STATE
