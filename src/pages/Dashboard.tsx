import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Heart, 
  Activity, 
  Thermometer, 
  Droplets, 
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Smartphone,
  Monitor,
  Cpu,
  Shield
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

// Mock data for demonstration
const generateHealthData = () => {
  const now = new Date();
  return Array.from({ length: 24 }, (_, i) => ({
    time: new Date(now.getTime() - (23 - i) * 60 * 60 * 1000).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    heartRate: 65 + Math.sin(i * 0.5) * 10 + Math.random() * 8,
    spo2: 96 + Math.sin(i * 0.3) * 2 + Math.random() * 2,
    activity: Math.max(0, 30 + Math.sin(i * 0.8) * 25 + Math.random() * 20),
    temperature: 98.6 + Math.sin(i * 0.2) * 0.5 + Math.random() * 0.3
  }));
};

const deviceData = [
  { id: 'edge-001', name: 'Bedroom Monitor', type: 'Jetson Nano', status: 'online', lastSeen: '2 min ago', battery: 85 },
  { id: 'edge-002', name: 'Living Room Hub', type: 'Raspberry Pi 4', status: 'online', lastSeen: '1 min ago', battery: 92 },
  { id: 'edge-003', name: 'Wearable Device', type: 'Custom IoT', status: 'offline', lastSeen: '15 min ago', battery: 23 }
];

const alerts = [
  { id: 1, type: 'warning', message: 'Heart rate elevated for 10+ minutes', time: '5 min ago', severity: 'medium' },
  { id: 2, type: 'info', message: 'Daily activity goal achieved', time: '1 hour ago', severity: 'low' },
  { id: 3, type: 'critical', message: 'SpO2 below normal range', time: '2 hours ago', severity: 'high' }
];

const Dashboard: React.FC = () => {
  const [healthData, setHealthData] = useState(generateHealthData());
  const [currentTime, setCurrentTime] = useState(new Date());
  const [selectedMetric, setSelectedMetric] = useState('heartRate');

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
      // Simulate real-time data updates
      if (Math.random() > 0.7) {
        setHealthData(prev => {
          const newData = [...prev];
          const lastPoint = newData[newData.length - 1];
          newData.push({
            time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
            heartRate: Math.max(50, Math.min(120, lastPoint.heartRate + (Math.random() - 0.5) * 5)),
            spo2: Math.max(90, Math.min(100, lastPoint.spo2 + (Math.random() - 0.5) * 1)),
            activity: Math.max(0, Math.min(100, lastPoint.activity + (Math.random() - 0.5) * 10)),
            temperature: Math.max(97, Math.min(100, lastPoint.temperature + (Math.random() - 0.5) * 0.2))
          });
          return newData.slice(-24);
        });
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const latestData = healthData[healthData.length - 1];

  const getStatusColor = (value: number, metric: string) => {
    switch (metric) {
      case 'heartRate':
        if (value < 60 || value > 100) return 'text-red-500';
        if (value < 70 || value > 90) return 'text-yellow-500';
        return 'text-green-500';
      case 'spo2':
        if (value < 95) return 'text-red-500';
        if (value < 97) return 'text-yellow-500';
        return 'text-green-500';
      case 'temperature':
        if (value < 97.5 || value > 99.5) return 'text-red-500';
        if (value < 98.0 || value > 99.0) return 'text-yellow-500';
        return 'text-green-500';
      default:
        return 'text-gray-500';
    }
  };

  const MetricCard = ({ title, value, unit, icon: Icon, trend, metric }: any) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`bg-white rounded-2xl p-6 shadow-lg border-2 transition-all duration-300 cursor-pointer ${
        selectedMetric === metric ? 'border-blue-500 shadow-blue-200' : 'border-gray-100 hover:border-gray-200'
      }`}
      onClick={() => setSelectedMetric(metric)}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl">
            <Icon className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-600">{title}</h3>
            <div className="flex items-center space-x-2">
              <span className={`text-2xl font-bold ${getStatusColor(value, metric)}`}>
                {typeof value === 'number' ? value.toFixed(1) : value}
              </span>
              <span className="text-sm text-gray-500">{unit}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-1">
          <TrendingUp className={`w-4 h-4 ${trend > 0 ? 'text-green-500' : 'text-red-500'}`} />
          <span className={`text-xs font-medium ${trend > 0 ? 'text-green-500' : 'text-red-500'}`}>
            {Math.abs(trend).toFixed(1)}%
          </span>
        </div>
      </div>
    </motion.div>
  );

  const DeviceCard = ({ device }: any) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl p-4 shadow-md border border-gray-100"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${device.status === 'online' ? 'bg-green-100' : 'bg-red-100'}`}>
            {device.type.includes('Jetson') ? <Cpu className="w-4 h-4 text-green-600" /> :
             device.type.includes('Raspberry') ? <Monitor className="w-4 h-4 text-green-600" /> :
             <Smartphone className="w-4 h-4 text-green-600" />}
          </div>
          <div>
            <h4 className="font-medium text-gray-900">{device.name}</h4>
            <p className="text-xs text-gray-500">{device.type}</p>
          </div>
        </div>
        <div className={`w-3 h-3 rounded-full ${device.status === 'online' ? 'bg-green-500' : 'bg-red-500'}`} />
      </div>
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Last seen: {device.lastSeen}</span>
        <span>Battery: {device.battery}%</span>
      </div>
    </motion.div>
  );

  const AlertCard = ({ alert }: any) => (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`p-4 rounded-xl border-l-4 ${
        alert.severity === 'high' ? 'bg-red-50 border-red-500' :
        alert.severity === 'medium' ? 'bg-yellow-50 border-yellow-500' :
        'bg-blue-50 border-blue-500'
      }`}
    >
      <div className="flex items-start space-x-3">
        {alert.severity === 'high' ? <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" /> :
         alert.severity === 'medium' ? <Clock className="w-5 h-5 text-yellow-500 mt-0.5" /> :
         <CheckCircle className="w-5 h-5 text-blue-500 mt-0.5" />}
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">{alert.message}</p>
          <p className="text-xs text-gray-500 mt-1">{alert.time}</p>
        </div>
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-8">
      {/* Status Banner */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl p-6 text-white"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Shield className="w-8 h-8" />
            <div>
              <h2 className="text-xl font-bold">System Status: Operational</h2>
              <p className="text-green-100">All edge devices connected • Federated learning active • Data encrypted</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-green-100">Last updated</p>
            <p className="font-medium">{currentTime.toLocaleTimeString()}</p>
          </div>
        </div>
      </motion.div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Heart Rate"
          value={latestData?.heartRate}
          unit="BPM"
          icon={Heart}
          trend={2.3}
          metric="heartRate"
        />
        <MetricCard
          title="Blood Oxygen"
          value={latestData?.spo2}
          unit="%"
          icon={Droplets}
          trend={-0.5}
          metric="spo2"
        />
        <MetricCard
          title="Activity Level"
          value={latestData?.activity}
          unit="steps/min"
          icon={Activity}
          trend={15.2}
          metric="activity"
        />
        <MetricCard
          title="Temperature"
          value={latestData?.temperature}
          unit="°F"
          icon={Thermometer}
          trend={0.1}
          metric="temperature"
        />
      </div>

      {/* Charts and Data */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Chart */}
        <div className="lg:col-span-2">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Real-time Health Metrics</h3>
              <div className="flex space-x-2">
                {['heartRate', 'spo2', 'activity'].map((metric) => (
                  <button
                    key={metric}
                    onClick={() => setSelectedMetric(metric)}
                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                      selectedMetric === metric
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {metric === 'heartRate' ? 'Heart Rate' : 
                     metric === 'spo2' ? 'SpO₂' : 'Activity'}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={healthData}>
                  <defs>
                    <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis 
                    dataKey="time" 
                    stroke="#6B7280"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#6B7280"
                    fontSize={12}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #E5E7EB',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey={selectedMetric}
                    stroke="#3B82F6"
                    strokeWidth={2}
                    fill="url(#colorGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        </div>

        {/* Alerts Panel */}
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Health Alerts</h3>
            <div className="space-y-3">
              <AnimatePresence>
                {alerts.map((alert) => (
                  <AlertCard key={alert.id} alert={alert} />
                ))}
              </AnimatePresence>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Edge Devices</h3>
            <div className="space-y-3">
              {deviceData.map((device) => (
                <DeviceCard key={device.id} device={device} />
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Federated Learning Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Federated Learning Status</h3>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-green-600 font-medium">Active</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">3</div>
            <div className="text-sm text-gray-600">Participating Devices</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">127</div>
            <div className="text-sm text-gray-600">Training Rounds</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">94.2%</div>
            <div className="text-sm text-gray-600">Model Accuracy</div>
          </div>
        </div>
        
        <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl">
          <div className="flex items-center space-x-3">
            <Shield className="w-5 h-5 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-blue-900">Privacy Protection Active</p>
              <p className="text-xs text-blue-700">Differential privacy with ε=1.0 noise applied to all model updates</p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Dashboard;