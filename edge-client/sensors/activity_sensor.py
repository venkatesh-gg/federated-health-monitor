"""
Activity Recognition Sensor Module
Interfaces with LSM6DS33 IMU for activity and motion detection
"""

import time
import numpy as np
from typing import Optional, Dict, List
import logging
from collections import deque

try:
    import board
    import busio
    import adafruit_lsm6ds.lsm6ds33 as lsm6ds33
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("GPIO libraries not available, using simulation mode")


class ActivitySensor:
    """Activity sensor using LSM6DS33 IMU (accelerometer + gyroscope)"""
    
    def __init__(self, i2c_address: int = 0x6a, simulation_mode: bool = None):
        """Initialize activity sensor
        
        Args:
            i2c_address: I2C address of the LSM6DS33 sensor
            simulation_mode: Force simulation mode for testing
        """
        self.logger = logging.getLogger(__name__)
        self.i2c_address = i2c_address
        
        # Use simulation mode if GPIO not available or explicitly requested
        self.simulation_mode = simulation_mode or not GPIO_AVAILABLE
        
        if not self.simulation_mode:
            try:
                # Initialize I2C bus
                i2c = busio.I2C(board.SCL, board.SDA)
                
                # Initialize LSM6DS33 sensor
                self.sensor = lsm6ds33.LSM6DS33(i2c, address=i2c_address)
                
                # Configure sensor
                self.sensor.accelerometer_range = lsm6ds33.Range.RANGE_4G
                self.sensor.gyro_range = lsm6ds33.GyroRange.RANGE_500_DPS
                self.sensor.accelerometer_data_rate = lsm6ds33.Rate.RATE_104_HZ
                self.sensor.gyro_data_rate = lsm6ds33.Rate.RATE_104_HZ
                
                self.logger.info(f"LSM6DS33 activity sensor initialized at address 0x{i2c_address:02x}")
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize hardware sensor: {e}")
                self.logger.info("Falling back to simulation mode")
                self.simulation_mode = True
        
        # Initialize simulation variables
        if self.simulation_mode:
            self.current_activity = 'resting'
            self.activity_cycle_time = 0
            self.time_offset = time.time()
            self.logger.info("Activity sensor running in simulation mode")
        
        # Data buffers for activity recognition
        self.accel_buffer = deque(maxlen=100)  # 1 second at 100Hz
        self.gyro_buffer = deque(maxlen=100)
        
        # Feature calculation variables
        self.window_size = 50  # 0.5 seconds
        self.step_count = 0
        self.last_step_time = 0
        
        # Activity detection thresholds
        self.thresholds = {
            'resting': {'accel_std': 0.1, 'gyro_std': 0.05},
            'walking': {'accel_std': 0.5, 'gyro_std': 0.2},
            'running': {'accel_std': 1.0, 'gyro_std': 0.5},
            'sleeping': {'accel_std': 0.05, 'gyro_std': 0.02}
        }
    
    def read(self) -> Optional[np.ndarray]:
        """Read activity sensor data
        
        Returns:
            numpy array with accelerometer and gyroscope data, or None if no data available
        """
        try:
            if self.simulation_mode:
                return self._read_simulated()
            else:
                return self._read_hardware()
                
        except Exception as e:
            self.logger.error(f"Error reading activity sensor: {e}")
            return None
    
    def _read_hardware(self) -> Optional[np.ndarray]:
        """Read data from actual LSM6DS33 sensor"""
        try:
            # Read accelerometer data (x, y, z in m/s²)
            accel_x, accel_y, accel_z = self.sensor.acceleration
            
            # Read gyroscope data (x, y, z in rad/s)
            gyro_x, gyro_y, gyro_z = self.sensor.gyro
            
            # Store in buffers
            accel_data = np.array([accel_x, accel_y, accel_z])
            gyro_data = np.array([gyro_x, gyro_y, gyro_z])
            
            self.accel_buffer.append(accel_data)
            self.gyro_buffer.append(gyro_data)
            
            # Combine accelerometer and gyroscope data
            combined_data = np.concatenate([accel_data, gyro_data])
            
            return combined_data.astype(np.float32)
            
        except Exception as e:
            self.logger.error(f"Hardware sensor read error: {e}")
            return None
    
    def _read_simulated(self) -> np.ndarray:
        """Generate simulated activity sensor data"""
        current_time = time.time() - self.time_offset
        
        # Cycle through different activities
        cycle_duration = 60  # 1 minute per activity
        cycle_position = (current_time % (cycle_duration * 4)) / cycle_duration
        
        if cycle_position < 1:
            self.current_activity = 'resting'
        elif cycle_position < 2:
            self.current_activity = 'walking'
        elif cycle_position < 3:
            self.current_activity = 'running'
        else:
            self.current_activity = 'sleeping'
        
        # Generate realistic sensor data based on current activity
        accel_data, gyro_data = self._generate_activity_data(self.current_activity, current_time)
        
        # Store in buffers
        self.accel_buffer.append(accel_data)
        self.gyro_buffer.append(gyro_data)
        
        # Combine accelerometer and gyroscope data
        combined_data = np.concatenate([accel_data, gyro_data])
        
        return combined_data.astype(np.float32)
    
    def _generate_activity_data(self, activity: str, time_val: float) -> tuple:
        """Generate realistic sensor data for specific activity
        
        Args:
            activity: Current activity type
            time_val: Current time value for wave generation
            
        Returns:
            Tuple of (accelerometer_data, gyroscope_data)
        """
        if activity == 'resting':
            # Small random movements, mostly gravity
            accel_base = np.array([0.1, 0.1, 9.8])  # Mostly gravity on Z-axis
            accel_noise = np.random.normal(0, 0.1, 3)
            accel_data = accel_base + accel_noise
            
            gyro_noise = np.random.normal(0, 0.05, 3)
            gyro_data = gyro_noise
            
        elif activity == 'walking':
            # Regular stepping pattern
            step_freq = 2.0  # 2 Hz (2 steps per second)
            step_wave = np.sin(2 * np.pi * step_freq * time_val)
            
            accel_base = np.array([0.5 * step_wave, 0.2 * np.sin(2 * np.pi * step_freq * time_val + np.pi/4), 9.8])
            accel_noise = np.random.normal(0, 0.2, 3)
            accel_data = accel_base + accel_noise
            
            gyro_base = np.array([0.1 * step_wave, 0.1 * np.cos(2 * np.pi * step_freq * time_val), 0.05 * step_wave])
            gyro_noise = np.random.normal(0, 0.1, 3)
            gyro_data = gyro_base + gyro_noise
            
        elif activity == 'running':
            # More intense movement patterns
            run_freq = 3.5  # 3.5 Hz (3.5 steps per second)
            run_wave = np.sin(2 * np.pi * run_freq * time_val)
            
            accel_base = np.array([1.5 * run_wave, 0.8 * np.sin(2 * np.pi * run_freq * time_val + np.pi/4), 9.8])
            accel_noise = np.random.normal(0, 0.5, 3)
            accel_data = accel_base + accel_noise
            
            gyro_base = np.array([0.3 * run_wave, 0.4 * np.cos(2 * np.pi * run_freq * time_val), 0.2 * run_wave])
            gyro_noise = np.random.normal(0, 0.2, 3)
            gyro_data = gyro_base + gyro_noise
            
        else:  # sleeping
            # Very minimal movement
            accel_base = np.array([0.05, 0.05, 9.8])  # Almost pure gravity
            accel_noise = np.random.normal(0, 0.03, 3)
            accel_data = accel_base + accel_noise
            
            gyro_noise = np.random.normal(0, 0.01, 3)
            gyro_data = gyro_noise
        
        return accel_data, gyro_data
    
    def get_activity_features(self) -> Optional[Dict]:
        """Calculate activity recognition features from sensor data
        
        Returns:
            Dictionary with calculated features or None if insufficient data
        """
        if len(self.accel_buffer) < self.window_size or len(self.gyro_buffer) < self.window_size:
            return None
        
        try:
            # Get recent data
            recent_accel = np.array(list(self.accel_buffer)[-self.window_size:])
            recent_gyro = np.array(list(self.gyro_buffer)[-self.window_size:])
            
            # Calculate statistical features
            features = {}
            
            # Accelerometer features
            accel_magnitude = np.linalg.norm(recent_accel, axis=1)
            features['accel_mean'] = np.mean(accel_magnitude)
            features['accel_std'] = np.std(accel_magnitude)
            features['accel_max'] = np.max(accel_magnitude)
            features['accel_min'] = np.min(accel_magnitude)
            
            # Gyroscope features
            gyro_magnitude = np.linalg.norm(recent_gyro, axis=1)
            features['gyro_mean'] = np.mean(gyro_magnitude)
            features['gyro_std'] = np.std(gyro_magnitude)
            features['gyro_max'] = np.max(gyro_magnitude)
            features['gyro_min'] = np.min(gyro_magnitude)
            
            # Frequency domain features (simplified)
            features['accel_energy'] = np.sum(accel_magnitude ** 2)
            features['gyro_energy'] = np.sum(gyro_magnitude ** 2)
            
            # Step detection
            steps_detected = self._detect_steps(accel_magnitude)
            features['step_frequency'] = steps_detected * 2  # Extrapolate to per second
            
            return features
            
        except Exception as e:
            self.logger.error(f"Feature calculation error: {e}")
            return None
    
    def _detect_steps(self, accel_magnitude: np.ndarray) -> int:
        """Simple step detection based on acceleration peaks
        
        Args:
            accel_magnitude: Acceleration magnitude array
            
        Returns:
            Number of steps detected
        """
        try:
            # Simple peak detection for steps
            threshold = np.mean(accel_magnitude) + 0.5 * np.std(accel_magnitude)
            
            steps = 0
            above_threshold = False
            
            for magnitude in accel_magnitude:
                if magnitude > threshold and not above_threshold:
                    steps += 1
                    above_threshold = True
                elif magnitude <= threshold:
                    above_threshold = False
            
            return steps
            
        except Exception:
            return 0
    
    def classify_activity(self) -> Optional[Dict]:
        """Classify current activity based on sensor features
        
        Returns:
            Dictionary with activity classification or None if insufficient data
        """
        features = self.get_activity_features()
        if features is None:
            return None
        
        try:
            # Simple rule-based classification
            accel_std = features['accel_std']
            gyro_std = features['gyro_std']
            step_freq = features['step_frequency']
            
            # Classification logic
            if accel_std < self.thresholds['sleeping']['accel_std'] and gyro_std < self.thresholds['sleeping']['gyro_std']:
                activity = 'sleeping'
                confidence = 0.9
            elif accel_std < self.thresholds['resting']['accel_std'] and gyro_std < self.thresholds['resting']['gyro_std']:
                activity = 'resting'
                confidence = 0.8
            elif accel_std > self.thresholds['running']['accel_std'] or step_freq > 3:
                activity = 'running'
                confidence = 0.85
            elif step_freq > 1:
                activity = 'walking'
                confidence = 0.8
            else:
                activity = 'resting'
                confidence = 0.6
            
            return {
                'activity': activity,
                'confidence': confidence,
                'features': features,
                'step_frequency': step_freq
            }
            
        except Exception as e:
            self.logger.error(f"Activity classification error: {e}")
            return None
    
    def get_status(self) -> dict:
        """Get sensor status information
        
        Returns:
            Dictionary with sensor status
        """
        status = {
            'sensor_type': 'activity',
            'model': 'LSM6DS33' if not self.simulation_mode else 'Simulated',
            'simulation_mode': self.simulation_mode,
            'i2c_address': f"0x{self.i2c_address:02x}",
            'buffer_size': len(self.accel_buffer),
            'status': 'active' if self.simulation_mode or hasattr(self, 'sensor') else 'error'
        }
        
        if self.simulation_mode:
            status['current_simulated_activity'] = self.current_activity
        
        return status
    
    def close(self):
        """Clean up sensor resources"""
        if hasattr(self, 'sensor') and not self.simulation_mode:
            try:
                # LSM6DS33 doesn't require explicit cleanup
                pass
            except Exception as e:
                self.logger.error(f"Error closing activity sensor: {e}")
        
        self.logger.info("Activity sensor closed")