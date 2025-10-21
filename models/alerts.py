
class Alert:
    current_alerts = []
    def __init__(self):
        pass
    
    def add_alert(self, new_alert):
        Alert.current_alerts.append(new_alert)
    
    def remove_alert(self, current_alert):
        Alert.current_alerts.remove(current_alert)

    