class Alert:
    """Stores alert messages"""
    
    def __init__(self):
        self.alerts = []
    
    def add_alert(self, message):
        """Add alert message"""
        self.alerts.append(message)
        print(f"Alert stored: {message}", flush=True)