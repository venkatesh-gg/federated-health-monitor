#!/usr/bin/env python3
"""
Federated Health Monitoring Server
Implements secure aggregation and differential privacy for federated learning
"""

import os
import json
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import redis
from celery import Celery
from cryptography.fernet import Fernet
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import tensorflow as tf

from federated.aggregator import FederatedAggregator
from federated.privacy import DifferentialPrivacyManager
from utils.encryption import EncryptionManager
from utils.logger import setup_logger
from models.database import db, Device, ModelUpdate, AggregationRound

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

# Initialize extensions
CORS(app)
db.init_app(app)

# Initialize Celery
celery = Celery(app.import_name)
celery.conf.update(app.config)

# Initialize Redis
redis_client = redis.Redis.from_url(app.config['REDIS_URL'])

# Initialize components
encryption_manager = EncryptionManager(app.config.get('ENCRYPTION_KEY'))
federated_aggregator = FederatedAggregator(app.config)
privacy_manager = DifferentialPrivacyManager(app.config)

# Setup logging
logger = setup_logger(app.config.get('LOG_LEVEL', 'INFO'))

# Prometheus metrics
metrics = {
    'requests_total': Counter('federation_requests_total', 'Total requests', ['method', 'endpoint']),
    'model_updates_received': Counter('model_updates_received_total', 'Model updates received', ['device_id']),
    'aggregation_rounds': Counter('aggregation_rounds_total', 'Aggregation rounds completed'),
    'active_devices': Gauge('active_devices', 'Number of active devices'),
    'request_duration': Histogram('request_duration_seconds', 'Request duration', ['endpoint'])
}


@app.before_request
def before_request():
    """Before request hook for metrics and logging"""
    g.start_time = time.time()
    metrics['requests_total'].labels(method=request.method, endpoint=request.endpoint).inc()


@app.after_request
def after_request(response):
    """After request hook for metrics"""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        metrics['request_duration'].labels(endpoint=request.endpoint).observe(duration)
    return response


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check Redis connection
        redis_client.ping()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': 'ok',
                'redis': 'ok',
                'aggregator': 'ok'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@app.route('/api/v1/devices/register', methods=['POST'])
def register_device():
    """Register a new edge device"""
    try:
        data = request.get_json()
        
        if not data or 'device_id' not in data:
            return jsonify({'error': 'device_id is required'}), 400
        
        device_id = data['device_id']
        
        # Check if device already exists
        existing_device = Device.query.filter_by(device_id=device_id).first()
        if existing_device:
            existing_device.last_seen = datetime.utcnow()
            existing_device.status = 'active'
        else:
            # Create new device
            device = Device(
                device_id=device_id,
                device_type=data.get('device_type', 'edge'),
                capabilities=json.dumps(data.get('capabilities', {})),
                location=data.get('location'),
                status='active',
                registered_at=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
            db.session.add(device)
        
        db.session.commit()
        
        # Update active devices metric
        active_count = Device.query.filter_by(status='active').count()
        metrics['active_devices'].set(active_count)
        
        logger.info(f"Device registered: {device_id}")
        
        return jsonify({
            'status': 'registered',
            'device_id': device_id,
            'server_config': {
                'aggregation_interval': app.config.get('AGGREGATION_INTERVAL_HOURS', 24),
                'privacy_budget': app.config.get('PRIVACY_BUDGET', 1.0)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Device registration error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/health-data', methods=['POST'])
def receive_health_data():
    """Receive encrypted health data from edge devices"""
    try:
        data = request.get_json()
        
        if not data or 'device_id' not in data or 'encrypted_data' not in data:
            return jsonify({'error': 'device_id and encrypted_data are required'}), 400
        
        device_id = data['device_id']
        encrypted_data = data['encrypted_data']
        
        # Verify device exists and is active
        device = Device.query.filter_by(device_id=device_id, status='active').first()
        if not device:
            return jsonify({'error': 'Device not found or inactive'}), 404
        
        # Decrypt health data
        try:
            decrypted_data = encryption_manager.decrypt_data(encrypted_data)
        except Exception as e:
            logger.error(f"Decryption failed for device {device_id}: {e}")
            return jsonify({'error': 'Invalid encrypted data'}), 400
        
        # Store data for processing
        cache_key = f"health_data:{device_id}:{int(time.time())}"
        redis_client.setex(cache_key, 3600, json.dumps(decrypted_data))  # 1 hour TTL
        
        # Update device last seen
        device.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Trigger async processing
        process_health_data.delay(device_id, decrypted_data)
        
        logger.info(f"Received health data from device {device_id}, batch size: {data.get('batch_size', 1)}")
        
        return jsonify({
            'status': 'received',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Health data reception error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/model-updates', methods=['POST'])
def receive_model_updates():
    """Receive model weight updates from edge devices"""
    try:
        data = request.get_json()
        
        if not data or 'device_id' not in data or 'model_updates' not in data:
            return jsonify({'error': 'device_id and model_updates are required'}), 400
        
        device_id = data['device_id']
        model_updates = data['model_updates']
        
        # Verify device
        device = Device.query.filter_by(device_id=device_id, status='active').first()
        if not device:
            return jsonify({'error': 'Device not found or inactive'}), 404
        
        # Store model updates
        for model_name, update_data in model_updates.items():
            model_update = ModelUpdate(
                device_id=device_id,
                model_name=model_name,
                update_data=json.dumps(update_data),
                samples_count=update_data.get('samples_count', 0),
                created_at=datetime.utcnow()
            )
            db.session.add(model_update)
        
        db.session.commit()
        
        # Update metrics
        metrics['model_updates_received'].labels(device_id=device_id).inc()
        
        # Check if we have enough updates for aggregation
        check_aggregation_readiness.delay()
        
        logger.info(f"Received model updates from device {device_id}, models: {list(model_updates.keys())}")
        
        return jsonify({
            'status': 'received',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Model updates reception error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/global-models', methods=['GET'])
def download_global_models():
    """Download latest global models for edge devices"""
    try:
        device_id = request.args.get('device_id')
        if not device_id:
            return jsonify({'error': 'device_id parameter is required'}), 400
        
        # Verify device
        device = Device.query.filter_by(device_id=device_id, status='active').first()
        if not device:
            return jsonify({'error': 'Device not found or inactive'}), 404
        
        # Get latest aggregation round
        latest_round = AggregationRound.query.filter_by(status='completed').order_by(
            AggregationRound.completed_at.desc()
        ).first()
        
        if not latest_round:
            return jsonify({'error': 'No global models available'}), 404
        
        # Get global models
        global_models = json.loads(latest_round.global_models)
        
        # Update device last seen
        device.last_seen = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Device {device_id} downloaded global models from round {latest_round.round_number}")
        
        return jsonify({
            'round_number': latest_round.round_number,
            'global_models': global_models,
            'created_at': latest_round.completed_at.isoformat(),
            'participating_devices': latest_round.participating_devices
        }), 200
        
    except Exception as e:
        logger.error(f"Global models download error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/metrics', methods=['GET'])
def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}


@celery.task
def process_health_data(device_id: str, health_data: List[Dict]):
    """Process health data from edge devices"""
    try:
        logger.info(f"Processing health data from device {device_id}")
        
        # Here you would implement health data analysis
        # For now, we'll just log the data
        for data_point in health_data:
            sensor_type = data_point.get('sensor')
            prediction = data_point.get('prediction', {})
            
            # Check for critical conditions
            if sensor_type == 'spo2' and prediction.get('is_critical', False):
                logger.warning(f"Critical SpO2 detected from device {device_id}: {prediction}")
                # Trigger alert system
                trigger_health_alert.delay(device_id, 'spo2_critical', prediction)
            
            elif sensor_type == 'heart_rate' and prediction.get('is_anomalous', False):
                logger.warning(f"Heart rate anomaly detected from device {device_id}: {prediction}")
                trigger_health_alert.delay(device_id, 'heart_rate_anomaly', prediction)
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing health data from device {device_id}: {e}")
        return False


@celery.task
def trigger_health_alert(device_id: str, alert_type: str, data: Dict):
    """Trigger health alert for critical conditions"""
    try:
        logger.warning(f"HEALTH ALERT - Device: {device_id}, Type: {alert_type}, Data: {data}")
        
        # Here you would implement alert mechanisms:
        # - Send notifications to healthcare providers
        # - Store alerts in database
        # - Trigger emergency protocols if needed
        
        alert_data = {
            'device_id': device_id,
            'alert_type': alert_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': 'high' if 'critical' in alert_type else 'medium'
        }
        
        # Store in Redis for real-time dashboard
        redis_client.lpush('health_alerts', json.dumps(alert_data))
        redis_client.ltrim('health_alerts', 0, 999)  # Keep last 1000 alerts
        
        return True
        
    except Exception as e:
        logger.error(f"Error triggering health alert: {e}")
        return False


@celery.task
def check_aggregation_readiness():
    """Check if we have enough model updates to start aggregation"""
    try:
        min_devices = app.config.get('MIN_DEVICES_FOR_AGGREGATION', 3)
        
        # Count recent model updates (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_updates = db.session.query(ModelUpdate.device_id).filter(
            ModelUpdate.created_at >= cutoff_time
        ).distinct().count()
        
        if recent_updates >= min_devices:
            logger.info(f"Aggregation ready with {recent_updates} devices")
            start_aggregation_round.delay()
        else:
            logger.info(f"Aggregation not ready: {recent_updates}/{min_devices} devices")
        
        return recent_updates
        
    except Exception as e:
        logger.error(f"Error checking aggregation readiness: {e}")
        return 0


@celery.task
def start_aggregation_round():
    """Start a new federated learning aggregation round"""
    try:
        logger.info("Starting new aggregation round")
        
        # Create new aggregation round
        round_number = db.session.query(AggregationRound).count() + 1
        
        aggregation_round = AggregationRound(
            round_number=round_number,
            status='in_progress',
            started_at=datetime.utcnow()
        )
        db.session.add(aggregation_round)
        db.session.commit()
        
        # Get recent model updates
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        model_updates = ModelUpdate.query.filter(
            ModelUpdate.created_at >= cutoff_time,
            ModelUpdate.aggregated == False
        ).all()
        
        if not model_updates:
            logger.warning("No model updates available for aggregation")
            aggregation_round.status = 'failed'
            aggregation_round.error_message = 'No model updates available'
            db.session.commit()
            return False
        
        # Group updates by model name
        updates_by_model = {}
        participating_devices = set()
        
        for update in model_updates:
            model_name = update.model_name
            if model_name not in updates_by_model:
                updates_by_model[model_name] = []
            
            updates_by_model[model_name].append({
                'device_id': update.device_id,
                'update_data': json.loads(update.update_data),
                'samples_count': update.samples_count
            })
            participating_devices.add(update.device_id)
        
        # Perform federated aggregation
        global_models = {}
        
        for model_name, updates in updates_by_model.items():
            logger.info(f"Aggregating {len(updates)} updates for model {model_name}")
            
            # Apply differential privacy
            private_updates = privacy_manager.add_noise_to_updates(updates)
            
            # Perform federated averaging
            global_model = federated_aggregator.aggregate_model_updates(
                model_name, private_updates
            )
            
            if global_model:
                global_models[model_name] = global_model
        
        # Save aggregation results
        aggregation_round.global_models = json.dumps(global_models)
        aggregation_round.participating_devices = len(participating_devices)
        aggregation_round.status = 'completed'
        aggregation_round.completed_at = datetime.utcnow()
        
        # Mark updates as aggregated
        for update in model_updates:
            update.aggregated = True
        
        db.session.commit()
        
        # Update metrics
        metrics['aggregation_rounds'].inc()
        
        logger.info(f"Aggregation round {round_number} completed with {len(participating_devices)} devices")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in aggregation round: {e}")
        
        # Update aggregation round with error
        if 'aggregation_round' in locals():
            aggregation_round.status = 'failed'
            aggregation_round.error_message = str(e)
            db.session.commit()
        
        return False


def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")


if __name__ == '__main__':
    # Create tables
    create_tables()
    
    # Start Flask app
    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000),
        debug=app.config.get('DEBUG', False)
    )