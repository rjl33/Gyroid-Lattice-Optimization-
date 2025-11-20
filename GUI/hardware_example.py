"""
Example: Hardware Integration with HX711 Load Cell and Rotary Encoder
This shows a complete working example for a common testing machine setup
"""

import time
import threading
from collections import deque

# Hardware libraries (install as needed)
try:
    from hx711 import HX711
    HX711_AVAILABLE = True
except ImportError:
    HX711_AVAILABLE = False
    print("Warning: hx711 library not available. Install with: pip install hx711")

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO not available. Install with: sudo apt-get install python3-rpi.gpio")


class TestMachineHardware:
    """
    Complete hardware interface for a test machine with:
    - HX711 Load Cell Amplifier
    - Rotary Encoder for displacement
    - Stepper motor for motion control
    """
    
    def __init__(self):
        # Pin definitions (customize for your setup)
        self.LOAD_CELL_DOUT = 5
        self.LOAD_CELL_SCK = 6
        
        self.ENCODER_A = 17
        self.ENCODER_B = 27
        
        self.MOTOR_STEP = 22
        self.MOTOR_DIR = 23
        self.MOTOR_ENABLE = 24
        
        # Calibration factors
        self.load_cell_scale = 1.0  # Set after calibration
        self.encoder_resolution = 0.01  # mm per count
        self.steps_per_mm = 200  # Steps per mm of travel
        
        # State
        self.encoder_position = 0
        self.last_encoder_state = 0
        self.force_offset = 0
        self.displacement_offset = 0
        
        # Hardware objects
        self.hx711 = None
        self.connected = False
        
        # Initialize
        self.setup()
    
    def setup(self):
        """Initialize all hardware"""
        if not (HX711_AVAILABLE and GPIO_AVAILABLE):
            print("Required hardware libraries not available - running in simulation mode")
            return
        
        try:
            # Setup GPIO
            GPIO.setmode(GPIO.BCM)
            
            # Setup Load Cell (HX711)
            self.hx711 = HX711(
                dout_pin=self.LOAD_CELL_DOUT,
                pd_sck_pin=self.LOAD_CELL_SCK
            )
            self.hx711.set_reading_format("MSB", "MSB")
            self.hx711.reset()
            
            # Setup Rotary Encoder
            GPIO.setup(self.ENCODER_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.ENCODER_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.ENCODER_A, GPIO.BOTH, callback=self._encoder_callback)
            
            # Setup Stepper Motor
            GPIO.setup(self.MOTOR_STEP, GPIO.OUT)
            GPIO.setup(self.MOTOR_DIR, GPIO.OUT)
            GPIO.setup(self.MOTOR_ENABLE, GPIO.OUT)
            GPIO.output(self.MOTOR_ENABLE, GPIO.LOW)  # Enable motor
            
            self.connected = True
            print("Hardware initialized successfully")
            
        except Exception as e:
            print(f"Hardware setup failed: {e}")
            self.connected = False
    
    def _encoder_callback(self, channel):
        """Interrupt callback for rotary encoder"""
        a_state = GPIO.input(self.ENCODER_A)
        b_state = GPIO.input(self.ENCODER_B)
        
        # Quadrature decoding
        if a_state != self.last_encoder_state:
            if b_state != a_state:
                self.encoder_position += 1
            else:
                self.encoder_position -= 1
        
        self.last_encoder_state = a_state
    
    def read_force(self):
        """Read force from load cell in Newtons"""
        if not self.connected or self.hx711 is None:
            # Simulation mode
            return 0.0
        
        try:
            # Get average of 5 readings for stability
            raw_value = self.hx711.get_weight(5)
            
            # Apply calibration and offset
            force = (raw_value * self.load_cell_scale) - self.force_offset
            
            return force
            
        except Exception as e:
            print(f"Error reading force: {e}")
            return 0.0
    
    def read_displacement(self):
        """Read displacement from encoder in mm"""
        if not self.connected:
            return 0.0
        
        try:
            # Convert encoder counts to displacement
            displacement = (self.encoder_position * self.encoder_resolution) - self.displacement_offset
            return displacement
            
        except Exception as e:
            print(f"Error reading displacement: {e}")
            return 0.0
    
    def move_motor(self, direction, steps):
        """
        Move stepper motor
        direction: 1 for forward, -1 for reverse
        steps: number of steps to move
        """
        if not self.connected:
            return
        
        try:
            # Set direction
            GPIO.output(self.MOTOR_DIR, GPIO.HIGH if direction > 0 else GPIO.LOW)
            
            # Step motor
            for _ in range(abs(steps)):
                GPIO.output(self.MOTOR_STEP, GPIO.HIGH)
                time.sleep(0.0001)  # Adjust for desired speed
                GPIO.output(self.MOTOR_STEP, GPIO.LOW)
                time.sleep(0.0001)
                
        except Exception as e:
            print(f"Error moving motor: {e}")
    
    def move_to_displacement(self, target_mm, speed_mm_per_sec=1.0):
        """
        Move to a target displacement at specified speed
        target_mm: Target displacement in mm
        speed_mm_per_sec: Movement speed
        """
        if not self.connected:
            return
        
        current_disp = self.read_displacement()
        delta = target_mm - current_disp
        
        steps = int(abs(delta) * self.steps_per_mm)
        direction = 1 if delta > 0 else -1
        
        step_delay = 1.0 / (speed_mm_per_sec * self.steps_per_mm * 2)  # Half period
        
        GPIO.output(self.MOTOR_DIR, GPIO.HIGH if direction > 0 else GPIO.LOW)
        
        for _ in range(steps):
            GPIO.output(self.MOTOR_STEP, GPIO.HIGH)
            time.sleep(step_delay)
            GPIO.output(self.MOTOR_STEP, GPIO.LOW)
            time.sleep(step_delay)
    
    def stop_motor(self):
        """Emergency stop motor"""
        if not self.connected:
            return
        
        try:
            GPIO.output(self.MOTOR_ENABLE, GPIO.HIGH)  # Disable motor
            time.sleep(0.1)
            GPIO.output(self.MOTOR_ENABLE, GPIO.LOW)  # Re-enable for next operation
        except Exception as e:
            print(f"Error stopping motor: {e}")
    
    def calibrate_load_cell(self, known_mass_kg):
        """
        Calibrate load cell with known mass
        known_mass_kg: Mass of calibration weight in kg
        """
        if not self.connected or self.hx711 is None:
            print("Cannot calibrate - hardware not connected")
            return False
        
        try:
            print("Place calibration weight on load cell...")
            time.sleep(2)
            
            # Take reading
            raw_value = self.hx711.get_weight(20)  # Average 20 readings
            
            if raw_value != 0:
                # Calculate scale factor (convert mass to force: F = mg)
                known_force = known_mass_kg * 9.81
                self.load_cell_scale = known_force / raw_value
                
                print(f"Calibration complete!")
                print(f"Scale factor: {self.load_cell_scale:.6f}")
                print(f"Measured force: {known_force:.2f} N")
                
                return True
            else:
                print("Error: Zero reading from load cell")
                return False
                
        except Exception as e:
            print(f"Calibration error: {e}")
            return False
    
    def tare_sensors(self):
        """Zero all sensors at current position"""
        if not self.connected:
            return False
        
        try:
            print("Taring sensors...")
            
            # Take multiple readings and average
            force_readings = []
            for _ in range(20):
                force_readings.append(self.read_force() + self.force_offset)
                time.sleep(0.05)
            
            self.force_offset = sum(force_readings) / len(force_readings)
            self.displacement_offset = self.read_displacement() + self.displacement_offset
            
            print(f"Tare complete. Force offset: {self.force_offset:.2f} N")
            print(f"Displacement offset: {self.displacement_offset:.3f} mm")
            
            return True
            
        except Exception as e:
            print(f"Tare error: {e}")
            return False
    
    def run_test_sequence(self, target_displacement, test_type="compression"):
        """
        Run a complete test sequence
        target_displacement: Target displacement in mm
        test_type: "compression" or "tension"
        """
        print(f"\nStarting {test_type} test to {target_displacement} mm")
        
        # Tare sensors
        self.tare_sensors()
        
        # Determine direction
        direction = -1 if test_type == "compression" else 1
        
        # Move to target while collecting data
        data = []
        start_time = time.time()
        
        while True:
            current_disp = self.read_displacement()
            current_force = self.read_force()
            elapsed = time.time() - start_time
            
            data.append((elapsed, current_disp, current_force))
            
            # Check if target reached
            if abs(current_disp) >= abs(target_displacement):
                break
            
            # Move motor one step
            self.move_motor(direction, 1)
            time.sleep(0.001)
        
        print(f"Test complete! Collected {len(data)} data points")
        return data
    
    def cleanup(self):
        """Clean up GPIO"""
        if GPIO_AVAILABLE and self.connected:
            try:
                GPIO.cleanup()
                print("GPIO cleaned up")
            except Exception as e:
                print(f"Cleanup error: {e}")


# Test the hardware interface
if __name__ == "__main__":
    print("Testing Hardware Interface")
    print("=" * 50)
    
    hw = TestMachineHardware()
    
    if hw.connected:
        print("\nHardware connected successfully!")
        
        # Calibration example
        response = input("\nDo you want to calibrate the load cell? (y/n): ")
        if response.lower() == 'y':
            mass_kg = float(input("Enter calibration mass (kg): "))
            hw.calibrate_load_cell(mass_kg)
        
        # Tare sensors
        input("\nPress Enter to tare sensors...")
        hw.tare_sensors()
        
        # Test readings
        print("\nReading sensors for 5 seconds...")
        for i in range(50):
            force = hw.read_force()
            disp = hw.read_displacement()
            print(f"Force: {force:8.2f} N  |  Displacement: {disp:8.3f} mm", end='\r')
            time.sleep(0.1)
        
        print("\n\nTest complete!")
        
    else:
        print("\nRunning in simulation mode (hardware not available)")
    
    hw.cleanup()
