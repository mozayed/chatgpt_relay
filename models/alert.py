class Alert:
    """Stores alert messages"""
    
    def __init__(self):
        self.alerts = []
        self.active_alerts = set()
    
    def add_alert(self, message):
        """Add alert message"""
        self.alerts.append(message)
        self.active_alerts.add(message)
        print(f"Alert stored: {message}", flush=True)