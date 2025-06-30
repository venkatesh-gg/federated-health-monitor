import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Bell, 
  Filter, 
  Search,
  MoreVertical,
  Heart,
  Activity,
  Thermometer,
  Droplets,
  User,
  Calendar,
  X
} from 'lucide-react';

const alerts = [
  {
    id: 1,
    type: 'critical',
    title: 'Critical SpO2 Level',
    message: 'Patient Robert Williams SpO2 dropped to 89% - immediate attention required',
    patient: 'Robert Williams',
    device: 'Wearable Device',
    timestamp: '2024-01-16T14:30:00Z',
    status: 'active',
    severity: 'high',
    category: 'health',
    icon: Droplets,
    value: '89%',
    threshold: '95%'
  },
  {
    id: 2,
    type: 'warning',
    title: 'Elevated Heart Rate',
    message: 'Patient Michael Chen heart rate elevated above 100 BPM for 15 minutes',
    patient: 'Michael Chen',
    device: 'Bedroom Monitor',
    timestamp: '2024-01-16T13:45:00Z',
    status: 'acknowledged',
    severity: 'medium',
    category: 'health',
    icon: Heart,
    value: '105 BPM',
    threshold: '100 BPM'
  },
  {
    id: 3,
    type: 'info',
    title: 'Device Battery Low',
    message: 'Wearable Device battery level at 23% - charging recommended',
    patient: 'Robert Williams',
    device: 'Wearable Device',
    timestamp: '2024-01-16T12:20:00Z',
    status: 'resolved',
    severity: 'low',
    category: 'device',
    icon: Activity,
    value: '23%',
    threshold: '30%'
  },
  {
    id: 4,
    type: 'warning',
    title: 'Temperature Anomaly',
    message: 'Patient Sarah Johnson body temperature elevated to 99.8°F',
    patient: 'Sarah Johnson',
    device: 'Bedroom Monitor',
    timestamp: '2024-01-16T11:15:00Z',
    status: 'active',
    severity: 'medium',
    category: 'health',
    icon: Thermometer,
    value: '99.8°F',
    threshold: '99.0°F'
  },
  {
    id: 5,
    type: 'info',
    title: 'Daily Activity Goal Achieved',
    message: 'Patient Emily Rodriguez completed daily activity goal of 10,000 steps',
    patient: 'Emily Rodriguez',
    device: 'Living Room Hub',
    timestamp: '2024-01-16T10:30:00Z',
    status: 'resolved',
    severity: 'low',
    category: 'achievement',
    icon: Activity,
    value: '10,247 steps',
    threshold: '10,000 steps'
  },
  {
    id: 6,
    type: 'critical',
    title: 'Device Offline',
    message: 'Kitchen Monitor has been offline for 2 hours - connectivity issue detected',
    patient: 'Lisa Thompson',
    device: 'Kitchen Monitor',
    timestamp: '2024-01-16T09:00:00Z',
    status: 'active',
    severity: 'high',
    category: 'device',
    icon: Activity,
    value: 'Offline 2h',
    threshold: 'Online'
  }
];

const Alerts: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterCategory, setFilterCategory] = useState('all');
  const [selectedAlert, setSelectedAlert] = useState<number | null>(null);

  const filteredAlerts = alerts.filter(alert => {
    const matchesSearch = alert.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         alert.patient.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         alert.message.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeverity = filterSeverity === 'all' || alert.severity === filterSeverity;
    const matchesStatus = filterStatus === 'all' || alert.status === filterStatus;
    const matchesCategory = filterCategory === 'all' || alert.category === filterCategory;
    
    return matchesSearch && matchesSeverity && matchesStatus && matchesCategory;
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'text-red-600 bg-red-100 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-100 border-blue-200';
      default: return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-red-600 bg-red-100';
      case 'acknowledged': return 'text-yellow-600 bg-yellow-100';
      case 'resolved': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'critical': return AlertTriangle;
      case 'warning': return Clock;
      case 'info': return CheckCircle;
      default: return Bell;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const AlertCard = ({ alert }: { alert: any }) => {
    const TypeIcon = getTypeIcon(alert.type);
    const AlertIcon = alert.icon;

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ scale: 1.01 }}
        className={`bg-white rounded-2xl p-6 shadow-lg border-2 transition-all duration-300 cursor-pointer ${
          selectedAlert === alert.id ? 'border-blue-500 shadow-blue-200' : 'border-gray-100 hover:border-gray-200'
        }`}
        onClick={() => setSelectedAlert(selectedAlert === alert.id ? null : alert.id)}
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start space-x-4">
            <div className={`p-3 rounded-xl border ${getSeverityColor(alert.severity)}`}>
              <TypeIcon className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                <h3 className="text-lg font-semibold text-gray-900">{alert.title}</h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(alert.status)}`}>
                  {alert.status}
                </span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                  {alert.severity}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-3">{alert.message}</p>
              
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <div className="flex items-center space-x-1">
                  <User className="w-3 h-3" />
                  <span>{alert.patient}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Activity className="w-3 h-3" />
                  <span>{alert.device}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Calendar className="w-3 h-3" />
                  <span>{formatTimestamp(alert.timestamp)}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">{alert.value}</p>
              <p className="text-xs text-gray-500">Threshold: {alert.threshold}</p>
            </div>
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <MoreVertical className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>

        {selectedAlert === alert.id && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-gray-100 pt-4"
          >
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Alert Details</h4>
                  <div className="space-y-1 text-xs text-gray-600">
                    <p><span className="font-medium">Category:</span> {alert.category}</p>
                    <p><span className="font-medium">Type:</span> {alert.type}</p>
                    <p><span className="font-medium">Timestamp:</span> {new Date(alert.timestamp).toLocaleString()}</p>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Actions</h4>
                  <div className="flex flex-wrap gap-2">
                    {alert.status === 'active' && (
                      <>
                        <button className="px-3 py-1 bg-yellow-500 text-white text-xs rounded-lg hover:bg-yellow-600 transition-colors">
                          Acknowledge
                        </button>
                        <button className="px-3 py-1 bg-green-500 text-white text-xs rounded-lg hover:bg-green-600 transition-colors">
                          Resolve
                        </button>
                      </>
                    )}
                    {alert.status === 'acknowledged' && (
                      <button className="px-3 py-1 bg-green-500 text-white text-xs rounded-lg hover:bg-green-600 transition-colors">
                        Resolve
                      </button>
                    )}
                    <button className="px-3 py-1 bg-blue-500 text-white text-xs rounded-lg hover:bg-blue-600 transition-colors">
                      View Patient
                    </button>
                    <button className="px-3 py-1 bg-gray-500 text-white text-xs rounded-lg hover:bg-gray-600 transition-colors">
                      Escalate
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Health Alerts</h1>
          <p className="text-gray-600">Monitor and manage patient health alerts</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="bg-red-500 text-white text-sm rounded-full px-3 py-1">
            {alerts.filter(a => a.status === 'active').length} Active
          </span>
          <span className="bg-yellow-500 text-white text-sm rounded-full px-3 py-1">
            {alerts.filter(a => a.status === 'acknowledged').length} Acknowledged
          </span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
        >
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-red-100 rounded-xl">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Critical</p>
              <p className="text-2xl font-bold text-gray-900">
                {alerts.filter(a => a.severity === 'high').length}
              </p>
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
            <div className="p-3 bg-yellow-100 rounded-xl">
              <Clock className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Warning</p>
              <p className="text-2xl font-bold text-gray-900">
                {alerts.filter(a => a.severity === 'medium').length}
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
            <div className="p-3 bg-blue-100 rounded-xl">
              <CheckCircle className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Info</p>
              <p className="text-2xl font-bold text-gray-900">
                {alerts.filter(a => a.severity === 'low').length}
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
            <div className="p-3 bg-green-100 rounded-xl">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Resolved</p>
              <p className="text-2xl font-bold text-gray-900">
                {alerts.filter(a => a.status === 'resolved').length}
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search alerts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value)}
                className="border border-gray-300 rounded-xl px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Severity</option>
                <option value="high">Critical</option>
                <option value="medium">Warning</option>
                <option value="low">Info</option>
              </select>
            </div>
            
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="border border-gray-300 rounded-xl px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
            </select>
            
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="border border-gray-300 rounded-xl px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Categories</option>
              <option value="health">Health</option>
              <option value="device">Device</option>
              <option value="achievement">Achievement</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        <AnimatePresence>
          {filteredAlerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </AnimatePresence>
      </div>

      {filteredAlerts.length === 0 && (
        <div className="text-center py-12">
          <Bell className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No alerts found</h3>
          <p className="text-gray-600">Try adjusting your search or filter criteria</p>
        </div>
      )}
    </div>
  );
};

export default Alerts;