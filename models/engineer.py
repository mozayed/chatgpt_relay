import os

class Engineer:
    def __init__(self):
        self.phone_number = os.getenv("ENGINEER_PHONE_NUMBER")