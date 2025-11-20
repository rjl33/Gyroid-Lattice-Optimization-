# Test Bench GUI - Compression & Torsion Testing

A PySide6-based graphical interface for controlling compression and torsion testing machines on Raspberry Pi.

## Features

- **Dual Test Types**: Compression and Torsion testing
- **Test Modes**: 
  - Monotonic (single displacement to target)
  - Fatigue (cyclic testing with max cycle count)
- **Real-time Plotting**: Live force vs displacement graph using pyqtgraph
- **Data Logging**: Export to CSV and Excel formats
- **Email Results**: Automatically email test results with data attachments
- **Emergency Stop**: Safety feature for immediate test termination
- **Professional UI**: Clean, intuitive interface optimized for Raspberry Pi

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install PySide6 pyqtgraph numpy openpyxl
```

### 2. (Optional) Install Hardware Libraries

Depending on your hardware setup, you may need:

For GPIO control:
```bash
sudo apt-get install python3-rpi.gpio
```

For I2C/SPI sensors (Adafruit libraries):
```bash
pip install adafruit-circuitpython-ads1x15
```

For serial communication:
```bash
pip install pyserial
```

## Running the Application

### Basic Usage (Simulated Data)
```bash
python test_bench_gui.py
```

This will run with simulated data for testing the interface.

### With Hardware Integration

1. Edit `hardware_interface.py` to match your specific hardware setup
2. Update the `DataAcquisitionThread` class in `test_bench_gui.py` to use your hardware interface
3. Run the application

## Hardware Integration Guide

### Step 1: Configure Hardware Interface

Edit `hardware_interface.py` and customize the `HardwareInterface` class:

```python
def setup_hardware(self):
    # Add your specific hardware initialization
    # Example for I2C load cell:
    i2c = busio.I2C(board.SCL, board.SDA)
    self.ads = ADS1115(i2c)
    self.load_cell_channel = AnalogIn(self.ads, ADS1115.P0)
```

### Step 2: Implement Sensor Reading

Customize the `read_force()` and `read_displacement()` methods:

```python
def read_force(self):
    # Read from your load cell
    raw_value = self.load_cell_channel.value
    voltage = self.load_cell_channel.voltage
    force = voltage * self.load_cell_calibration
    return force

def read_displacement(self):
    # Read from your displacement sensor
    # (encoder, LVDT, etc.)
    displacement = self.encoder.read_position()
    return displacement
```

### Step 3: Connect to Main GUI

In `test_bench_gui.py`, update the `DataAcquisitionThread.run()` method:

```python
from hardware_interface import HardwareInterface

class DataAcquisitionThread(QThread):
    def __init__(self):
        super().__init__()
        self.hw = HardwareInterface()  # Add this
        
    def run(self):
        while self.running:
            # Replace simulated data with real readings
            self.current_force = self.hw.read_force()
            self.current_displacement = self.hw.read_displacement()
            
            self.data_ready.emit(self.current_force, self.current_displacement)
            self.msleep(50)  # 20 Hz update rate
```

## Common Hardware Setups

### Load Cell with HX711 Amplifier

```python
# Install: pip install hx711
from hx711 import HX711

def setup_hardware(self):
    self.hx = HX711(dout_pin=5, pd_sck_pin=6)
    self.hx.set_reading_format("MSB", "MSB")
    self.hx.reset()
    
def read_force(self):
    val = self.hx.get_weight(5)  # Average of 5 readings
    return val * self.load_cell_calibration
```

### Linear Encoder via Serial

```python
import serial

def setup_hardware(self):
    self.serial_port = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    
def read_displacement(self):
    if self.serial_port.in_waiting:
        line = self.serial_port.readline().decode().strip()
        displacement = float(line)
        return displacement
    return self.last_displacement
```

### Stepper Motor Control for Displacement

```python
import RPi.GPIO as GPIO

def setup_hardware(self):
    GPIO.setmode(GPIO.BCM)
    self.STEP_PIN = 17
    self.DIR_PIN = 27
    GPIO.setup(self.STEP_PIN, GPIO.OUT)
    GPIO.setup(self.DIR_PIN, GPIO.OUT)
    
def move_to_position(self, target_mm):
    steps = int(target_mm * self.steps_per_mm)
    GPIO.output(self.DIR_PIN, GPIO.HIGH if steps > 0 else GPIO.LOW)
    
    for _ in range(abs(steps)):
        GPIO.output(self.STEP_PIN, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(self.STEP_PIN, GPIO.LOW)
        time.sleep(0.001)
```

## Email Configuration

To use the email functionality:

1. Go to Settings tab in the GUI
2. Enter your email address
3. For Gmail, use an App-Specific Password:
   - Go to Google Account Settings → Security
   - Enable 2-Factor Authentication
   - Generate App Password for "Mail"
   - Use this password in the GUI

SMTP Settings:
- Gmail: smtp.gmail.com, port 587
- Outlook: smtp-mail.outlook.com, port 587
- Yahoo: smtp.mail.yahoo.com, port 587

## Test Configuration

### Monotonic Test
1. Select test type (Compression/Torsion)
2. Select "Monotonic" mode
3. Set target displacement
4. Click START TEST
5. Test runs until target displacement is reached

### Fatigue Test
1. Select test type (Compression/Torsion)
2. Select "Fatigue" mode
3. Set displacement amplitude
4. Set maximum number of cycles
5. Click START TEST
6. Test runs for specified cycles

## Data Export

### CSV Format
- Header with test metadata
- Columns: Time (s), Displacement (mm), Force (N)
- Human-readable format

### Excel Format
- Formatted spreadsheet with headers
- Test metadata at top
- Data in organized columns
- Compatible with data analysis tools

## Calibration

Before first use:

1. **Load Cell Calibration**:
   ```python
   hw = HardwareInterface()
   hw.calibrate_load_cell(known_force=100.0)  # Use a known weight
   ```

2. **Zero Sensors**:
   - Click "Tare Sensors" button before each test
   - Or call `hw.tare_sensors()` programmatically

## Safety Features

- **Emergency Stop Button**: Immediately halts all operations
- **Maximum Displacement Limits**: Prevent over-travel
- **Data Backup**: Prompt before clearing data
- **Hardware Watchdog**: Monitor sensor connections

## Troubleshooting

### GUI doesn't start
- Check PySide6 installation: `python -c "import PySide6; print('OK')"`
- On Raspberry Pi, ensure X11 is running: `echo $DISPLAY`

### No data from sensors
- Check hardware connections
- Verify I2C/SPI/Serial permissions: `sudo usermod -a -G dialout $USER`
- Test hardware interface: `python hardware_interface.py`

### Plot is slow/choppy
- Reduce update rate in `DataAcquisitionThread.run()`: increase `msleep()` value
- Downsample data for plotting if needed

### Email not sending
- Verify SMTP settings
- Check firewall/network settings
- For Gmail, ensure "Less secure app access" or use App Password

## File Structure

```
test_bench_gui/
├── test_bench_gui.py          # Main GUI application
├── hardware_interface.py      # Hardware abstraction layer
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## Customization

### Changing Plot Appearance
Edit `create_plot()` in test_bench_gui.py:
```python
plot_widget.setBackground('k')  # Black background
self.curve = plot_widget.plot(pen=pg.mkPen(color='r', width=3))  # Red line
```

### Adding New Test Types
1. Add to `test_type_combo` items
2. Update hardware control logic in `DataAcquisitionThread`
3. Adjust data processing as needed

### Custom Data Analysis
After test completion, access data:
```python
force_data = self.force_data
displacement_data = self.displacement_data
# Perform analysis (stiffness, energy, etc.)
```

## Performance Tips for Raspberry Pi

1. **Use lightweight desktop**: LXDE or LXQt instead of full GNOME
2. **Reduce plot points**: Downsample for display if collecting at high rates
3. **Use SSD**: Store data on external SSD for faster writes
4. **Close other applications**: Free up resources during testing
5. **Overclock carefully**: If needed, ensure adequate cooling

## License

This software is provided as-is for educational and research purposes.

## Support

For issues and questions:
- Check hardware connections and calibration
- Review Python error messages
- Test hardware interface independently
- Verify all dependencies are installed

## Future Enhancements

Possible additions:
- [ ] Real-time stress-strain calculation
- [ ] Multiple specimen tracking
- [ ] Database integration
- [ ] Advanced cycle counting (rainflow)
- [ ] Video sync for DIC
- [ ] Machine learning failure prediction
- [ ] Remote monitoring via web interface

---

**Version**: 1.0  
**Platform**: Raspberry Pi (3/4/5) with Python 3.8+  
**GUI Framework**: PySide6 (Qt6)
