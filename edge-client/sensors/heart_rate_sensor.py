"""
Heart Rate Sensor Module
Interfaces with MAX30102 pulse oximeter sensor for heart rate monitoring
"""

import time
import numpy as np
from typing import Optional, List
import logging

try:
    import board
    import busio
    import adafruit_max30102
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("GPIO libraries not available, using simulation mode")


class HeartRateSensor:
    """Heart rate sensor using MAX30102 pulse oximeter"""
    
    def __init__(self, pin: Optional[int] = None, simulation_mode: bool = None):
        """Initialize heart rate sensor
        
        Args:
            pin: GPIO pin number (for compatibility, not used with I2C)
            simulation_mode: Force simulation mode for testing
        """
        self.logger = logging.getLogger(__name__)
        
        # Use simulation mode if GPIO not available or explicitly requested
        self.simulation_mode = simulation_mode or not GPIO_AVAILABLE
        
        if not self.simulation_mode:
            try:
                # Initialize I2C bus
                i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
                
                # Initialize MAX30102 sensor
                self.sensor = adafruit_max30102.MAX30102(i2c)
                
                # Configure sensor
                self.sensor.setup_sensor()
                self.sensor.set_mode_hr_only()  # Heart rate only mode
                
                self.logger.info("MAX30102 heart rate sensor initialized")
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize hardware sensor: {e}")
                self.logger.info("Falling back to simulation mode")
                self.simulation_mode = True
        
        # Initialize simulation variables
        if self.simulation_mode:
            self.base_heart_rate = 70  # Normal resting heart rate
            self.time_offset = time.time()
            self.logger.info("Heart rate sensor running in simulation mode")
        
        # Data buffers for smoothing
        self.raw_buffer = []
        self.filtered_buffer = []
        self.buffer_size = 50
        
        # Heart rate calculation variables
        self.last_peaks = []
        self.peak_threshold = 0.6
        
    def read(self) -> Optional[np.ndarray]:
        """Read heart rate data
        
        Returns:
            numpy array with heart rate data, or None if no data available
        """
        try:
            if self.simulation_mode:
                return self._read_simulated()
            else:
                return self._read_hardware()
                
        except Exception as e:
            self.logger.error(f"Error reading heart rate sensor: {e}")
            return None
    
    def _read_hardware(self) -> Optional[np.ndarray]:
        """Read data from actual MAX30102 sensor"""
        try:
            # Read raw IR values
            ir_data = []
            red_data = []
            
            # Collect multiple samples for better accuracy
            for _ in range(25):  # ~1 second at 25Hz
                if self.sensor.available():
                    red, ir = self.sensor.read_sensor()
                    red_data.append(red)
                    ir_data.append(ir)
                time.sleep(0.04)  # 25Hz sampling rate
            
            if not ir_data:
                return None
            
            # Use IR data for heart rate (more stable)
            raw_signal = np.array(ir_data, dtype=np.float32)
            
            # Apply filtering and heart rate calculation
            heart_rate = self._calculate_heart_rate(raw_signal)
            
            # Return structured data
            return np.array([heart_rate], dtype=np.float32)
            
        except Exception as e:
            self.logger.error(f"Hardware sensor read error: {e}")
            return None
    
    def _read_simulated(self) -> np.ndarray:
        """Generate simulated heart rate data"""
        current_time = time.time() - self.time_offset
        
        # Generate realistic heart rate variation
        # Base heart rate with natural variation and some noise
        variation = 10 * np.sin(current_time * 0.1)  # Slow breathing variation
        noise = 2 * np.random.normal()  # Random noise
        activity_boost = 20 * max(0, np.sin(current_time * 0.05))  # Activity periods
        
        heart_rate = self.base_heart_rate + variation + noise + activity_boost
        
        # Clamp to realistic range
        heart_rate = np.clip(heart_rate, 50, 180)
        
        return np.array([heart_rate], dtype=np.float32)
    
    def _calculate_heart_rate(self, raw_signal: np.ndarray) -> float:
        """Calculate heart rate from raw IR signal"""
        try:
            # Apply bandpass filter to isolate heart rate frequencies (0.5-4 Hz)
            filtered_signal = self._bandpass_filter(raw_signal)
            
            # Find peaks in the signal
            peaks = self._find_peaks(filtered_signal)
            
            if len(peaks) >= 2:
                # Calculate time between peaks
                peak_intervals = np.diff(peaks) * 0.04  # Convert to seconds (25Hz)
                
                # Calculate heart rate from average interval
                if len(peak_intervals) > 0:
                    avg_interval = np.mean(peak_intervals)
                    heart_rate = 60.0 / avg_interval  # Convert to BPM
                    
                    # Validate heart rate range
                    if 40 <= heart_rate <= 200:
                        return heart_rate
            
            # Return previous value or default if calculation fails
            if self.filtered_buffer:
                return self.filtered_buffer[-1]
            else:
                return 70.0  # Default resting heart rate
                
        except Exception as e:
            self.logger.error(f"Heart rate calculation error: {e}")
            return 70.0
    
    def _bandpass_filter(self, signal: np.ndarray) -> np.ndarray:
        """Apply simple bandpass filter for heart rate frequencies"""
        # Simple moving average filter to remove high frequency noise
        window_size = 5
        if len(signal) < window_size:
            return signal
        
        filtered = np.convolve(signal, np.ones(window_size)/window_size, mode='same')
        
        # Remove DC component
        filtered = filtered - np.mean(filtered)
        
        return filtered
    
    def _find_peaks(self, signal: np.ndarray) -> List[int]:
        """Find peaks in the filtered signal"""
        peaks = []
        
        if len(signal) < 3:
            return peaks
        
        # Simple peak detection
        threshold = np.std(signal) * self.peak_threshold
        
        for i in range(1, len(signal) - 1):
            if (signal[i] > signal[i-1] and 
                signal[i] > signal[i+1] and 
                signal[i] > threshold):
                peaks.append(i)
        
        return peaks
    
    def get_status(self) -> dict:
        """Get sensor status information
        
        Returns:
            Dictionary with sensor status
        """
        return {
            'sensor_type': 'heart_rate',
            'model': 'MAX30102' if not self.simulation_mode else 'Simulated',
            'simulation_mode': self.simulation_mode,
            'buffer_size': len(self.raw_buffer),
            'status': 'active' if self.simulation_mode or hasattr(self, 'sensor') else 'error'
        }
    
    def close(self):
        """Clean up sensor resources"""
        if hasattr(self, 'sensor') and not self.simulation_mode:
            try:
                # MAX30102 doesn't require explicit cleanup
                pass
            except Exception as e:
                self.logger.error(f"Error closing heart rate sensor: {e}")
        
        self.logger.info("Heart rate sensor closed")