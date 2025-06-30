#!/usr/bin/env python3
"""
Edge Health Monitoring Client
Runs TensorFlow Lite models on edge devices for real-time health monitoring
with federated learning capabilities.
"""

import json
import time
import threading
import queue
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np
import requests
from cryptography.fernet import Fernet
import schedule

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite

from sensors.heart_rate_sensor import HeartRateSensor
from sensors.spo2_sensor import SpO2Sensor  
from sensors.activity_sensor import ActivitySensor
from federated.model_updater import FederatedModelUpdater
from utils.encryption import EncryptionManager
from utils.logger import setup_logger

class EdgeHealthMonitor:
    """Main edge client for health monitoring with federated learning"""
    
    def __init__(self, config_path: str):
        """Initialize the edge health monitor"""
        self.config = self._load_config(config_path)
        self.logger = setup_logger(self.config.get('log_level', 'INFO'))
        
        # Initialize components
        self.sensors = self._initialize_sensors()
        self.models = self._load_models()
        self.federated_updater = FederatedModelUpdater(self.config)
        self.encryption_manager = EncryptionManager(self.config.get('encryption_key'))
        
        # Data queues for processing
        self.sensor_data_queue = queue.Queue(maxsize=1000)
        self.inference_results_queue = queue.Queue(maxsize=100)
        
        # Control flags
        self.running = False
        self.threads = []
        
        self.logger.info("Edge Health Monitor initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            raise RuntimeError(f"Failed to load config from {config_path}: {e}")
    
    def _initialize_sensors(self) -> Dict:
        """Initialize all health monitoring sensors"""
        sensors = {}
        
        try:
            if self.config.get('sensors', {}).get('heart_rate', {}).get('enabled', False):
                sensors['heart_rate'] = HeartRateSensor(
                    pin=self.config['sensors']['heart_rate']['pin']
                )
            
            if self.config.get('sensors', {}).get('spo2', {}).get('enabled', False):
                sensors['spo2'] = SpO2Sensor(
                    i2c_address=self.config['sensors']['spo2']['i2c_address']
                )
            
            if self.config.get('sensors', {}).get('activity', {}).get('enabled', False):
                sensors['activity'] = ActivitySensor(
                    i2c_address=self.config['sensors']['activity']['i2c_address']
                )
            
            self.logger.info(f"Initialized {len(sensors)} sensors")
            return sensors
            
        except Exception as e:
            self.logger.error(f"Failed to initialize sensors: {e}")
            return {}
    
    def _load_models(self) -> Dict:
        """Load TensorFlow Lite models for inference"""
        models = {}
        model_dir = Path(self.config.get('model_dir', 'models'))
        
        try:
            # Load heart rate anomaly detection model
            hr_model_path = model_dir / 'heart_rate_anomaly.tflite'
            if hr_model_path.exists():
                models['heart_rate'] = tflite.Interpreter(model_path=str(hr_model_path))
                models['heart_rate'].allocate_tensors()
            
            # Load SpO2 trend prediction model
            spo2_model_path = model_dir / 'spo2_prediction.tflite'
            if spo2_model_path.exists():
                models['spo2'] = tflite.Interpreter(model_path=str(spo2_model_path))
                models['spo2'].allocate_tensors()
            
            # Load activity recognition model
            activity_model_path = model_dir / 'activity_recognition.tflite'
            if activity_model_path.exists():
                models['activity'] = tflite.Interpreter(model_path=str(activity_model_path))
                models['activity'].allocate_tensors()
            
            self.logger.info(f"Loaded {len(models)} TensorFlow Lite models")
            return models
            
        except Exception as e:
            self.logger.error(f"Failed to load models: {e}")
            return {}
    
    def start_monitoring(self):
        """Start the health monitoring system"""
        self.running = True
        
        # Start sensor data collection threads
        for sensor_name, sensor in self.sensors.items():
            thread = threading.Thread(
                target=self._sensor_data_collector,
                args=(sensor_name, sensor),
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
        
        # Start inference thread
        inference_thread = threading.Thread(
            target=self._inference_worker,
            daemon=True
        )
        inference_thread.start()
        self.threads.append(inference_thread)
        
        # Start data transmission thread
        transmission_thread = threading.Thread(
            target=self._data_transmission_worker,
            daemon=True
        )
        transmission_thread.start()
        self.threads.append(transmission_thread)
        
        # Schedule federated learning updates
        schedule.every(self.config.get('federated_update_interval_hours', 24)).hours.do(
            self._perform_federated_update
        )
        
        self.logger.info("Health monitoring started successfully")
        
        # Main monitoring loop
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop the health monitoring system"""
        self.running = False
        
        # Wait for threads to complete
        for thread in self.threads:
            thread.join(timeout=5)
        
        # Close sensors
        for sensor in self.sensors.values():
            if hasattr(sensor, 'close'):
                sensor.close()
        
        self.logger.info("Health monitoring stopped")
    
    def _sensor_data_collector(self, sensor_name: str, sensor):
        """Collect data from a specific sensor"""
        while self.running:
            try:
                data = sensor.read()
                if data is not None:
                    sensor_data = {
                        'sensor': sensor_name,
                        'timestamp': time.time(),
                        'data': data
                    }
                    
                    if not self.sensor_data_queue.full():
                        self.sensor_data_queue.put(sensor_data)
                    else:
                        self.logger.warning(f"Sensor data queue full, dropping {sensor_name} data")
                
                time.sleep(self.config.get('sensor_sampling_interval', 1.0))
                
            except Exception as e:
                self.logger.error(f"Error collecting data from {sensor_name}: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _inference_worker(self):
        """Process sensor data through ML models"""
        while self.running:
            try:
                # Get sensor data (blocking with timeout)
                try:
                    sensor_data = self.sensor_data_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                sensor_name = sensor_data['sensor']
                data = sensor_data['data']
                
                # Run inference if model is available
                if sensor_name in self.models:
                    prediction = self._run_inference(sensor_name, data)
                    
                    result = {
                        'sensor': sensor_name,
                        'timestamp': sensor_data['timestamp'],
                        'raw_data': data,
                        'prediction': prediction
                    }
                    
                    if not self.inference_results_queue.full():
                        self.inference_results_queue.put(result)
                    else:
                        self.logger.warning("Inference results queue full, dropping result")
                
                self.sensor_data_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in inference worker: {e}")
    
    def _run_inference(self, sensor_name: str, data: np.ndarray) -> Dict:
        """Run inference on sensor data using TensorFlow Lite model"""
        try:
            model = self.models[sensor_name]
            
            # Get input details
            input_details = model.get_input_details()
            output_details = model.get_output_details()
            
            # Preprocess data to match model input shape
            input_data = self._preprocess_data(data, input_details[0]['shape'])
            
            # Set input and run inference
            model.set_tensor(input_details[0]['index'], input_data)
            model.invoke()
            
            # Get output
            output_data = model.get_tensor(output_details[0]['index'])
            
            # Post-process results
            prediction = self._postprocess_prediction(sensor_name, output_data)
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"Inference error for {sensor_name}: {e}")
            return {'error': str(e)}
    
    def _preprocess_data(self, data: np.ndarray, target_shape: Tuple) -> np.ndarray:
        """Preprocess sensor data to match model input requirements"""
        # Reshape and normalize data as needed
        if len(data.shape) != len(target_shape) - 1:  # Account for batch dimension
            data = data.reshape(target_shape[1:])
        
        # Add batch dimension
        data = np.expand_dims(data, axis=0)
        
        # Ensure correct data type
        data = data.astype(np.float32)
        
        return data
    
    def _postprocess_prediction(self, sensor_name: str, output_data: np.ndarray) -> Dict:
        """Post-process model output into meaningful results"""
        if sensor_name == 'heart_rate':
            # Binary classification: normal vs. anomalous
            anomaly_score = float(output_data[0][0])
            return {
                'anomaly_score': anomaly_score,
                'is_anomalous': anomaly_score > 0.5,
                'confidence': max(anomaly_score, 1 - anomaly_score)
            }
        
        elif sensor_name == 'spo2':
            # Regression: predicted SpO2 level
            predicted_spo2 = float(output_data[0][0])
            return {
                'predicted_spo2': predicted_spo2,
                'is_critical': predicted_spo2 < 90.0
            }
        
        elif sensor_name == 'activity':
            # Multi-class classification: activity types
            activity_probs = output_data[0]
            activity_labels = ['resting', 'walking', 'running', 'sleeping']
            predicted_activity = activity_labels[np.argmax(activity_probs)]
            confidence = float(np.max(activity_probs))
            
            return {
                'activity': predicted_activity,
                'confidence': confidence,
                'probabilities': {
                    label: float(prob) 
                    for label, prob in zip(activity_labels, activity_probs)
                }
            }
        
        return {'raw_output': output_data.tolist()}
    
    def _data_transmission_worker(self):
        """Transmit inference results to the federation server"""
        batch_size = self.config.get('transmission_batch_size', 10)
        batch_interval = self.config.get('transmission_interval_seconds', 30)
        
        batch = []
        last_transmission = time.time()
        
        while self.running:
            try:
                # Collect batch of results
                try:
                    result = self.inference_results_queue.get(timeout=1)
                    batch.append(result)
                    self.inference_results_queue.task_done()
                except queue.Empty:
                    pass
                
                # Transmit batch if it's full or enough time has passed
                current_time = time.time()
                should_transmit = (
                    len(batch) >= batch_size or
                    (batch and current_time - last_transmission >= batch_interval)
                )
                
                if should_transmit:
                    self._transmit_batch(batch)
                    batch = []
                    last_transmission = current_time
                
            except Exception as e:
                self.logger.error(f"Error in data transmission worker: {e}")
    
    def _transmit_batch(self, batch: List[Dict]):
        """Transmit a batch of results to the federation server"""
        try:
            # Encrypt the batch data
            encrypted_data = self.encryption_manager.encrypt_data(batch)
            
            # Prepare payload
            payload = {
                'device_id': self.config.get('device_id'),
                'encrypted_data': encrypted_data,
                'batch_size': len(batch),
                'timestamp': time.time()
            }
            
            # Send to federation server
            federation_url = self.config.get('federation_server_url')
            response = requests.post(
                f"{federation_url}/api/v1/health-data",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully transmitted batch of {len(batch)} results")
            else:
                self.logger.error(f"Failed to transmit batch: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error transmitting batch: {e}")
    
    def _perform_federated_update(self):
        """Perform federated learning model update"""
        try:
            self.logger.info("Starting federated learning update...")
            
            # Generate local model updates
            model_updates = self.federated_updater.generate_updates(self.models)
            
            # Send updates to federation server
            success = self.federated_updater.send_updates(model_updates)
            
            if success:
                # Download and apply global model updates
                new_models = self.federated_updater.download_global_models()
                if new_models:
                    self.models.update(new_models)
                    self.logger.info("Successfully updated models with federated learning")
            
        except Exception as e:
            self.logger.error(f"Error in federated update: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Edge Health Monitoring Client')
    parser.add_argument('--config', default='config/development.json',
                       help='Configuration file path')
    parser.add_argument('--log-level', default='INFO',
                       help='Logging level (DEBUG, INFO, WARNING, ERROR)')
    
    args = parser.parse_args()
    
    try:
        monitor = EdgeHealthMonitor(args.config)
        monitor.start_monitoring()
    except Exception as e:
        logging.error(f"Failed to start health monitor: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())