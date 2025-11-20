"""
Hardware Interface Module
Customize this for your specific Raspberry Pi and sensor setup
"""

import time
import numpy as np

# Uncomment and configure based on your hardware:
# For GPIO control:
# import RPi.GPIO as GPIO

# For I2C/SPI sensors:
# import board
# import busio
# from adafruit_ads1x15.ads1115 import ADS1115
# from adafruit_ads1x15.analog_in import AnalogIn

# For serial communication:
# import serial


class HardwareInterface:
    """
    Hardware interface for load cell and displacement sensor
    Customize this class for your specific hardware setup
    """
    
    def __init__(self):
        """Initialize hardware connections"""
        self.connected = False
        self.load_cell_calibration = 1.0  # Calibration factor for load cell
        self.displacement_calibration = 1.0  # Calibration factor for displacement
        
        # Initialize your hardware here
        self.setup_hardware()
    
    def setup_hardware(self):
        """Setup hardware connections - CUSTOMIZE THIS"""
        try:
            # Example: Setup GPIO pins
            # GPIO.setmode(GPIO.BCM)
            # GPIO.setup(MOTOR_PIN, GPIO.OUT)
            
            # Example: Setup I2C for load cell ADC
            # i2c = busio.I2C(board.SCL, board.SDA)
            # self.ads = ADS1115(i2c)
            # self.load_cell_channel = AnalogIn(self.ads, ADS1115.P0)
            
            # Example: Setup serial connection for displacement sensor
            # self.serial_port = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
            
            self.connected = True
            print("Hardware initialized successfully")
            
        except Exception as e:
            print(f"Hardware initialization failed: {e}")
            self.connected = False
    
    def read_force(self):
        """
        Read force from load cell
        Returns: Force in Newtons
        """
        if not self.connected:
            # Return simulated data if hardware not connected
            return np.random.normal(0, 5)
        
        try:
            # Example: Read from ADC and convert to force
            # raw_value = self.load_cell_channel.value
            # voltage = self.load_cell_channel.voltage
            # force = voltage * self.load_cell_calibration
            # return force
            
            # Placeholder - replace with actual hardware read
            return 0.0
            
        except Exception as e:
            print(f"Error reading force: {e}")
            return 0.0
    
    def read_displacement(self):
        """
        Read displacement from sensor
        Returns: Displacement in mm
        """
        if not self.connected:
            # Return simulated data if hardware not connected
            return 0.0
        
        try:
            # Example: Read from serial encoder
            # if self.serial_port.in_waiting:
            #     line = self.serial_port.readline().decode().strip()
            #     displacement = float(line) * self.displacement_calibration
            #     return displacement
            
            # Placeholder - replace with actual hardware read
            return 0.0
            
        except Exception as e:
            print(f"Error reading displacement: {e}")
            return 0.0
    
    def set_motor_speed(self, speed):
        """
        Set motor speed for displacement control
        speed: Speed value (range depends on your motor controller)
        """
        if not self.connected:
            return
        
        try:
            # Example: Set PWM for motor control
            # pwm.ChangeDutyCycle(speed)
            pass
            
        except Exception as e:
            print(f"Error setting motor speed: {e}")
    
    def stop_motor(self):
        """Emergency stop for motor"""
        if not self.connected:
            return
        
        try:
            # Example: Stop motor immediately
            # GPIO.output(MOTOR_PIN, GPIO.LOW)
            pass
            
        except Exception as e:
            print(f"Error stopping motor: {e}")
    
    def calibrate_load_cell(self, known_force):
        """
        Calibrate load cell with a known force
        known_force: Known force value in Newtons
        """
        try:
            raw_reading = self.read_force()
            if raw_reading != 0:
                self.load_cell_calibration = known_force / raw_reading
                print(f"Load cell calibrated. Factor: {self.load_cell_calibration}")
                return True
            return False
        except Exception as e:
            print(f"Calibration error: {e}")
            return False
    
    def tare_sensors(self):
        """Zero/tare all sensors"""
        try:
            # Take multiple readings and average
            force_readings = [self.read_force() for _ in range(10)]
            self.force_offset = np.mean(force_readings)
            
            disp_readings = [self.read_displacement() for _ in range(10)]
            self.displacement_offset = np.mean(disp_readings)
            
            print("Sensors tared successfully")
            return True
        except Exception as e:
            print(f"Taring error: {e}")
            return False
    
    def cleanup(self):
        """Cleanup hardware connections"""
        try:
            # Example: Cleanup GPIO
            # GPIO.cleanup()
            
            # Example: Close serial port
            # if hasattr(self, 'serial_port') and self.serial_port.is_open:
            #     self.serial_port.close()
            
            print("Hardware cleaned up")
        except Exception as e:
            print(f"Cleanup error: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Test hardware interface
    hw = HardwareInterface()
    
    if hw.connected:
        print("Testing hardware...")
        for i in range(10):
            force = hw.read_force()
            displacement = hw.read_displacement()
            print(f"Force: {force:.2f} N, Displacement: {displacement:.3f} mm")
            time.sleep(0.1)
    else:
        print("Hardware not connected - using simulated data")
    
    hw.cleanup()
