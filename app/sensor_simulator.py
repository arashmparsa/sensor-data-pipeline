import random
import time
from datetime import datetime

class SensorSimulator:
    '''Simulates CO2 sensor readings'''
    
    def __init__(self, sensor_id="SENSOR_001"):
        self.sensor_id = sensor_id
        self.base_co2 = 400  # Normal atmospheric CO2
        
    def get_reading(self):
        '''Generate realistic sensor reading'''
        # Simulate daily variation (higher during day)
        hour = datetime.now().hour
        daily_variation = 100 * abs(((hour - 12) / 12))
        
        return {
            "sensor_id": self.sensor_id,
            "co2_ppm": self.base_co2 + daily_variation + random.uniform(-50, 50),
            "temperature": 20 + random.uniform(-2, 5),
            "humidity": 45 + random.uniform(-10, 10),
            "timestamp": datetime.utcnow().isoformat()
        }
