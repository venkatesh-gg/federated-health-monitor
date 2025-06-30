import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Smartphone, 
  Monitor, 
  Cpu, 
  Wifi, 
  WifiOff, 
  Battery, 
  Plus, 
  Settings, 
  MoreVertical,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  MapPin,
  Zap
} from 'lucide-react';

const devices = [
  {
    id: 'edge-001',
    name: 'Bedroom Monitor',
    type: 'Jetson Nano',
    location: 'Master Bedroom',
    status: 'online',
    lastSeen: '2 min ago',
    battery: 85,
    temperature: 42.3,
    cpuUsage: 34,
    memoryUsage: 67,
    uptime: '15 days',
    patients: ['Sarah Johnson', 'Michael Chen'],
    sensors: ['Heart Rate', 'SpO2', 'Temperature'],
    modelVersion: 'v2.1.3',
    dataTransmitted: '2.4 GB',
    alerts: 0
  },
  {
    id: 'edge-002',
    name: 'Living Room Hub',
    type: 'Raspberry Pi 4',
    location: 'Living Room',
    status: 'online',
    lastSeen: '1 min ago',
    battery: 92,
    temperature: 38.7,
    cpuUsage: 28,
    memoryUsage: 45,
    uptime: '8 days',
    patients: ['Emily Rodriguez'],
    sensors: ['Activity', 'Environmental'],
    modelVersion: 'v2.1.3',
    dataTransmitted: '1.8 GB',
    alerts: 1
  },
  {
    id: 'edge-003',
    name: 'Wearable Device',
    type: 'Custom IoT',
    location: 'Mobile',
    status: 'offline',
    lastSeen: '15 min ago',
    battery: 23,
    temperature: 35.2,
    cpuUsage: 0,
    memoryUsage: 0,
    uptime: '0 days',
    patients: ['Robert Williams'],
    sensors: ['Heart Rate', 'Activity', 'GPS'],
    modelVersion: 'v2.0.8',
    dataTransmitted: '0.9 GB',
    alerts: 3
  },
  {
    id: 'edge-004',
    name: 'Kitchen Monitor',
    type: 'Jetson Nano',
    location: 'Kitchen',
    status: 'maintenance',
    lastSeen: '2 hours ago',
    battery: 78,
    temperature: 45.1,
    cpuUsage: 12,
    memoryUsage: 23,
    uptime: '3 days',
    patients: ['Lisa Thompson'],
    sensors: ['Environmental', 'Air Quality'],
    modelVersion: 'v2.1.2',
    dataTransmitted: '1.2 GB',
    alerts: 2
  }
];

const Devices: React.FC = () => {
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState('all');

  const filteredDevices = devices.filter(device => 
    filterStatus === 'all' || device.status === filterStatus
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-600 bg-green-100';
      case 'offline': return 'text-red-600 bg-red-100';
      case 'maintenance': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getDeviceIcon = (type: string) => {
    if (type.includes('Jetson')) return Cpu;
    if (type.includes('Raspberry')) return Monitor;
    return Smartphone;
  };

  const getBatteryColor = (battery: number) => {
    if (battery > 60) return 'text-green-500';
    if (battery > 30) return 'text-yellow-500';
    return 'text-red-500';
  };

  const DeviceCard = ({ device }: { device: any }) => {
    const DeviceIcon = getDeviceIcon(device.type);
    
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ scale: 1.02 }}
        className={`bg-white rounded-2xl p-6 shadow-lg border-2 transition-all duration-300 cursor-pointer ${
          selectedDevice === device.id ? 'border-blue-500 shadow-blue-200' : 'border-gray-100 hover:border-gray-200'
        }`}
        onClick={() => setSelectedDevice(selectedDevice === device.id ? null : device.id)}
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className={`p-3 rounded-xl ${
              device.status === 'online' ? 'bg-green-100' : 
              device.status === 'offline' ? 'bg-red-100' : 'bg-yellow-100'
            }`}>
              <DeviceIcon className={`w-6 h-6 ${
                device.status === 'online' ? 'text-green-600' : 
                device.status === 'offline' ? 'text-red-600' : 'text-yellow-600'
              }`} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{device.name}</h3>
              <p className="text-sm text-gray-600">{device.type}</p>
              <div className="flex items-center space-x-2 mt-1">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(device.status)}`}>
                  {device.status}
                </span>
                {device.alerts > 0 && (
                  <span className="px-2 py-1 bg-red-100 text-red-600 rounded-full text-xs font-medium">
                    {device.alerts} alerts
                  </span>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {device.status === 'online' ? 
              <Wifi className="w-5 h-5 text-green-500" /> : 
              <WifiOff className="w-5 h-5 text-red-500" />
            }
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <MoreVertical className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-600">{device.location}</span>
          </div>
          <div className="flex items-center space-x-2">
            <Battery className={`w-4 h-4 ${getBatteryColor(device.battery)}`} />
            <span className="text-sm text-gray-600">{device.battery}%</span>
          </div>
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-blue-500" />
            <span className="text-sm text-gray-600">CPU: {device.cpuUsage}%</span>
          </div>
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4 text-purple-500" />
            <span className="text-sm text-gray-600">{device.temperature}°C</span>
          </div>
        </div>

        {selectedDevice === device.id && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-gray-100 pt-4 mt-4"
          >
            <div className="space-y-3">
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Assigned Patients</h4>
                <div className="flex flex-wrap gap-2">
                  {device.patients.map((patient, index) => (
                    <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-lg">
                      {patient}
                    </span>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Sensors</h4>
                <div className="flex flex-wrap gap-2">
                  {device.sensors.map((sensor, index) => (
                    <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-lg">
                      {sensor}
                    </span>
                  ))}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
                <div>
                  <span className="font-medium">Uptime:</span> {device.uptime}
                </div>
                <div>
                  <span className="font-medium">Model:</span> {device.modelVersion}
                </div>
                <div>
                  <span className="font-medium">Memory:</span> {device.memoryUsage}%
                </div>
                <div>
                  <span className="font-medium">Data:</span> {device.dataTransmitted}
                </div>
              </div>
            </div>
          </motion.div>
        )}

        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <span className="text-xs text-gray-500">Last seen: {device.lastSeen}</span>
          <div className="flex space-x-2">
            <button className="px-3 py-1 bg-blue-500 text-white text-xs rounded-lg hover:bg-blue-600 transition-colors">
              Configure
            </button>
            <button className="px-3 py-1 bg-gray-100 text-gray-600 text-xs rounded-lg hover:bg-gray-200 transition-colors">
              Logs
            </button>
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Device Management</h1>
          <p className="text-gray-600">Monitor and manage edge computing devices</p>
        </div>
        <button className="flex items-center space-x-2 bg-blue-500 text-white px-4 py-2 rounded-xl hover:bg-blue-600 transition-colors">
          <Plus className="w-5 h-5" />
          <span>Add Device</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
        >
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-blue-100 rounded-xl">
              <Monitor className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Devices</p>
              <p className="text-2xl font-bold text-gray-900">{devices.length}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
        >
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-green-100 rounded-xl">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Online</p>
              <p className="text-2xl font-bold text-gray-900">
                {devices.filter(d => d.status === 'online').length}
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
        >
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-red-100 rounded-xl">
              <WifiOff className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Offline</p>
              <p className="text-2xl font-bold text-gray-900">
                {devices.filter(d => d.status === 'offline').length}
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
        >
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-yellow-100 rounded-xl">
              <Settings className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Maintenance</p>
              <p className="text-2xl font-bold text-gray-900">
                {devices.filter(d => d.status === 'maintenance').length}
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Filter */}
      <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
        <div className="flex items-center space-x-4">
          <span className="text-sm font-medium text-gray-700">Filter by status:</span>
          <div className="flex space-x-2">
            {['all', 'online', 'offline', 'maintenance'].map((status) => (
              <button
                key={status}
                onClick={() => setFilterStatus(status)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                  filterStatus === status
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Devices Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredDevices.map((device) => (
          <DeviceCard key={device.id} device={device} />
        ))}
      </div>

      {filteredDevices.length === 0 && (
        <div className="text-center py-12">
          <Monitor className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No devices found</h3>
          <p className="text-gray-600">Try adjusting your filter criteria</p>
        </div>
      )}
    </div>
  );
};

export default Devices;