"""
SpO2 (Blood Oxygen Saturation) Sensor Module
Interfaces with MAX30102 sensor for blood oxygen monitoring
"""

import time
import numpy as np
from typing import Optional, Tuple
import logging

try:
    import board
    import busio
    import adafruit_max30102
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("GPIO libraries not available, using simulation mode")


class SpO2Sensor:
    """SpO2 sensor using MAX30102 pulse oximeter"""
    
    def __init__(self, i2c_address: int = 0x57, simulation_mode: bool = None):
        """Initialize SpO2 sensor
        
        Args:
            i2c_address: I2C address of the MAX30102 sensor
            simulation_mode: Force simulation mode for testing
        """
        self.logger = logging.getLogger(__name__)
        self.i2c_address = i2c_address
        
        # Use simulation mode if GPIO not available or explicitly requested
        self.simulation_mode = simulation_mode or not GPIO_AVAILABLE
        
        if not self.simulation_mode:
            try:
                # Initialize I2C bus
                i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
                
                # Initialize MAX30102 sensor
                self.sensor = adafruit_max30102.MAX30102(i2c, address=i2c_address)
                
                # Configure sensor for SpO2 measurement
                self.sensor.setup_sensor()
                self.sensor.set_mode_spo2()  # SpO2 mode (red + IR)
                
                self.logger.info(f"MAX30102 SpO2 sensor initialized at address 0x{i2c_address:02x}")
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize hardware sensor: {e}")
                self.logger.info("Falling back to simulation mode")
                self.simulation_mode = True
        
        # Initialize simulation variables
        if self.simulation_mode:
            self.base_spo2 = 98.0  # Normal SpO2 level
            self.time_offset = time.time()
            self.logger.info("SpO2 sensor running in simulation mode")
        
        # Calibration constants for SpO2 calculation
        self.calibration_coefficients = {
            'a': -45.060,
            'b': 30.354,
            'c': 94.845
        }
        
        # Data buffers
        self.red_buffer = []
        self.ir_buffer = []
        self.buffer_size = 100
        
    def read(self) -> Optional[np.ndarray]:
        """Read SpO2 data
        
        Returns:
            numpy array with SpO2 percentage, or None if no data available
        """
        try:
            if self.simulation_mode:
                return self._read_simulated()
            else:
                return self._read_hardware()
                
        except Exception as e:
            self.logger.error(f"Error reading SpO2 sensor: {e}")
            return None
    
    def _read_hardware(self) -> Optional[np.ndarray]:
        """Read data from actual MAX30102 sensor"""
        try:
            red_samples = []
            ir_samples = []
            
            # Collect samples for SpO2 calculation
            sample_count = 50  # 2 seconds at 25Hz
            
            for _ in range(sample_count):
                if self.sensor.available():
                    red, ir = self.sensor.read_sensor()
                    red_samples.append(red)
                    ir_samples.append(ir)
                time.sleep(0.04)  # 25Hz sampling rate
            
            if len(red_samples) < 10:  # Need minimum samples
                return None
            
            # Convert to numpy arrays
            red_signal = np.array(red_samples, dtype=np.float32)
            ir_signal = np.array(ir_samples, dtype=np.float32)
            
            # Calculate SpO2
            spo2 = self._calculate_spo2(red_signal, ir_signal)
            
            if spo2 is not None:
                return np.array([spo2], dtype=np.float32)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Hardware sensor read error: {e}")
            return None
    
    def _read_simulated(self) -> np.ndarray:
        """Generate simulated SpO2 data"""
        current_time = time.time() - self.time_offset
        
        # Generate realistic SpO2 variation
        # Base SpO2 with small natural variation
        variation = 1.0 * np.sin(current_time * 0.05)  # Slow breathing variation
        noise = 0.3 * np.random.normal()  # Small random noise
        
        # Occasional drops (simulating brief interruptions)
        if np.random.random() < 0.01:  # 1% chance
            drop = np.random.uniform(2, 5)  # Drop by 2-5%
            variation -= drop
        
        spo2 = self.base_spo2 + variation + noise
        
        # Clamp to realistic range
        spo2 = np.clip(spo2, 85, 100)
        
        return np.array([spo2], dtype=np.float32)
    
    def _calculate_spo2(self, red_signal: np.ndarray, ir_signal: np.ndarray) -> Optional[float]:
        """Calculate SpO2 from red and IR signals
        
        Args:
            red_signal: Red LED signal samples
            ir_signal: IR LED signal samples
            
        Returns:
            SpO2 percentage or None if calculation fails
        """
        try:
            # Remove DC component and calculate AC/DC ratios
            red_ac, red_dc = self._calculate_ac_dc(red_signal)
            ir_ac, ir_dc = self._calculate_ac_dc(ir_signal)
            
            # Avoid division by zero
            if red_dc == 0 or ir_dc == 0 or ir_ac == 0:
                return None
            
            # Calculate ratio of ratios (R)
            red_ratio = red_ac / red_dc
            ir_ratio = ir_ac / ir_dc
            
            if ir_ratio == 0:
                return None
                
            R = red_ratio / ir_ratio
            
            # Apply calibration formula
            # SpO2 = a * R^2 + b * R + c
            spo2 = (self.calibration_coefficients['a'] * R * R + 
                   self.calibration_coefficients['b'] * R + 
                   self.calibration_coefficients['c'])
            
            # Validate SpO2 range
            if 70 <= spo2 <= 100:
                return float(spo2)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"SpO2 calculation error: {e}")
            return None
    
    def _calculate_ac_dc(self, signal: np.ndarray) -> Tuple[float, float]:
        """Calculate AC and DC components of signal
        
        Args:
            signal: Input signal array
            
        Returns:
            Tuple of (AC component, DC component)
        """
        # DC component is the mean
        dc_component = np.mean(signal)
        
        # AC component is the standard deviation (RMS of AC signal)
        ac_component = np.std(signal)
        
        return ac_component, dc_component
    
    def calibrate(self, known_spo2: float, red_signal: np.ndarray, ir_signal: np.ndarray):
        """Calibrate sensor with known SpO2 value
        
        Args:
            known_spo2: Known SpO2 value for calibration
            red_signal: Red LED signal during calibration
            ir_signal: IR LED signal during calibration
        """
        try:
            # Calculate current ratio
            red_ac, red_dc = self._calculate_ac_dc(red_signal)
            ir_ac, ir_dc = self._calculate_ac_dc(ir_signal)
            
            if red_dc != 0 and ir_dc != 0 and ir_ac != 0:
                red_ratio = red_ac / red_dc
                ir_ratio = ir_ac / ir_dc
                R = red_ratio / ir_ratio
                
                # Simple linear calibration adjustment
                # This is a simplified approach - production systems use more sophisticated calibration
                current_spo2 = (self.calibration_coefficients['a'] * R * R + 
                               self.calibration_coefficients['b'] * R + 
                               self.calibration_coefficients['c'])
                
                offset = known_spo2 - current_spo2
                
                # Adjust the constant term
                self.calibration_coefficients['c'] += offset
                
                self.logger.info(f"Calibrated SpO2 sensor with offset: {offset:.2f}")
                
        except Exception as e:
            self.logger.error(f"Calibration error: {e}")
    
    def get_signal_quality(self) -> dict:
        """Get signal quality metrics
        
        Returns:
            Dictionary with signal quality information
        """
        if self.simulation_mode:
            return {
                'signal_strength': 'good',
                'red_signal_quality': 0.95,
                'ir_signal_quality': 0.93,
                'motion_detected': False
            }
        
        # For hardware implementation, analyze recent buffer data
        quality = {
            'signal_strength': 'unknown',
            'red_signal_quality': 0.0,
            'ir_signal_quality': 0.0,
            'motion_detected': False
        }
        
        if len(self.red_buffer) > 10 and len(self.ir_buffer) > 10:
            # Simple quality metrics based on signal stability
            red_stability = 1.0 / (1.0 + np.std(self.red_buffer[-20:]))
            ir_stability = 1.0 / (1.0 + np.std(self.ir_buffer[-20:]))
            
            quality['red_signal_quality'] = min(red_stability, 1.0)
            quality['ir_signal_quality'] = min(ir_stability, 1.0)
            
            avg_quality = (quality['red_signal_quality'] + quality['ir_signal_quality']) / 2
            
            if avg_quality > 0.8:
                quality['signal_strength'] = 'excellent'
            elif avg_quality > 0.6:
                quality['signal_strength'] = 'good'
            elif avg_quality > 0.4:
                quality['signal_strength'] = 'fair'
            else:
                quality['signal_strength'] = 'poor'
        
        return quality
    
    def get_status(self) -> dict:
        """Get sensor status information
        
        Returns:
            Dictionary with sensor status
        """
        return {
            'sensor_type': 'spo2',
            'model': 'MAX30102' if not self.simulation_mode else 'Simulated',
            'simulation_mode': self.simulation_mode,
            'i2c_address': f"0x{self.i2c_address:02x}",
            'buffer_size': len(self.red_buffer),
            'status': 'active' if self.simulation_mode or hasattr(self, 'sensor') else 'error'
        }
    
    def close(self):
        """Clean up sensor resources"""
        if hasattr(self, 'sensor') and not self.simulation_mode:
            try:
                # MAX30102 doesn't require explicit cleanup
                pass
            except Exception as e:
                self.logger.error(f"Error closing SpO2 sensor: {e}")
        
        self.logger.info("SpO2 sensor closed")