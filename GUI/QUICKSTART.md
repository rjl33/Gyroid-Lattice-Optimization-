# Quick Start Guide

## Immediate Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test the GUI (No Hardware Required)
```bash
python test_bench_gui.py
```

The GUI will run with simulated data so you can test all features.

### 3. Configure Email (Optional but Recommended)
1. Run the GUI
2. Go to Settings tab
3. Enter your email and SMTP settings
4. For Gmail: Use an App Password (not your regular password)

## Testing the Interface

Once the GUI is running, try these features:

1. **Test Configuration**
   - Select Compression or Torsion
   - Choose Monotonic or Fatigue mode
   - Set displacement target

2. **Run a Simulated Test**
   - Click "START TEST"
   - Watch the real-time plot update
   - Click "STOP TEST" when done

3. **Save Data**
   - Click "Save Data (CSV)" or "Save Data (Excel)"
   - Choose location and filename

4. **Email Results**
   - Configure email in Settings tab
   - Click "Email Results" to send data

## Next Steps: Hardware Integration

### Option A: Quick Hardware Test
If you have your hardware ready, edit the `DataAcquisitionThread.run()` method in `test_bench_gui.py`:

```python
def run(self):
    while self.running:
        # Replace these lines with your hardware reads
        self.current_force = read_your_load_cell()  # Your function here
        self.current_displacement = read_your_encoder()  # Your function here
        
        self.data_ready.emit(self.current_force, self.current_displacement)
        self.msleep(50)
```

### Option B: Use Hardware Template
1. Edit `hardware_interface.py` with your specific sensors
2. See `hardware_example.py` for a complete HX711 + encoder setup
3. Test hardware independently: `python hardware_interface.py`
4. Integrate into GUI using the template

## Common Hardware Configurations

### HX711 Load Cell
```bash
pip install hx711
```
See `hardware_example.py` for complete implementation.

### Serial Sensors
```bash
pip install pyserial
```
Use `/dev/ttyUSB0` or `/dev/ttyACM0` for Arduino/serial devices.

### I2C ADC (ADS1115)
```bash
pip install adafruit-circuitpython-ads1x15
```
Common for high-resolution load cell readings.

## Raspberry Pi Tips

### Enable I2C/SPI
```bash
sudo raspi-config
# Navigate to Interface Options → Enable I2C/SPI
```

### Add User to Dialout Group (for serial)
```bash
sudo usermod -a -G dialout $USER
# Log out and back in for changes to take effect
```

### Run GUI on Boot (Optional)
Add to `~/.config/autostart/`:
```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/testbench.desktop
```

Content:
```
[Desktop Entry]
Type=Application
Name=Test Bench GUI
Exec=python3 /home/pi/test_bench_gui.py
Terminal=false
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'PySide6'"
```bash
pip install PySide6
```

### "Permission denied: /dev/ttyUSB0"
```bash
sudo usermod -a -G dialout $USER
# Then log out and back in
```

### GUI is slow on Raspberry Pi
- Close other applications
- Reduce plot update rate (increase `msleep()` value)
- Use LXDE instead of full desktop

### Load cell readings are noisy
- Add hardware filtering (capacitor)
- Average multiple readings
- Increase `get_weight()` sample count

## File Overview

- `test_bench_gui.py` - Main GUI application
- `hardware_interface.py` - Template for your hardware
- `hardware_example.py` - Complete HX711 example
- `requirements.txt` - Python dependencies
- `README.md` - Full documentation

## Need Help?

1. Check the full README.md for detailed documentation
2. Test hardware independently before integrating
3. Use simulation mode to verify GUI functionality
4. Review hardware_example.py for working code patterns

---

**Ready to start testing!** Run `python test_bench_gui.py` now.
