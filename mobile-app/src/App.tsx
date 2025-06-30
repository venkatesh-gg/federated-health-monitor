import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Provider as PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { Alert, StatusBar } from 'react-native';

// Firebase
import auth, { FirebaseAuthTypes } from '@react-native-firebase/auth';
import messaging from '@react-native-firebase/messaging';

// Screens
import LoginScreen from './screens/auth/LoginScreen';
import DashboardScreen from './screens/dashboard/DashboardScreen';
import HealthMetricsScreen from './screens/health/HealthMetricsScreen';
import DevicesScreen from './screens/devices/DevicesScreen';
import ProfileScreen from './screens/profile/ProfileScreen';
import AlertsScreen from './screens/alerts/AlertsScreen';

// Services
import { AuthService } from './services/AuthService';
import { NotificationService } from './services/NotificationService';
import { HealthMetricsService } from './services/HealthMetricsService';

// Contexts
import { AuthContext } from './contexts/AuthContext';
import { HealthContext } from './contexts/HealthContext';

// Theme
import { theme } from './theme/theme';

// Types
interface User {
  uid: string;
  email: string | null;
  displayName: string | null;
}

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

const AuthStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name="Login" component={LoginScreen} />
  </Stack.Navigator>
);

const MainTabs = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        let iconName: string;

        switch (route.name) {
          case 'Dashboard':
            iconName = 'dashboard';
            break;
          case 'Health':
            iconName = 'favorite';
            break;
          case 'Devices':
            iconName = 'devices';
            break;
          case 'Alerts':
            iconName = 'notifications';
            break;
          case 'Profile':
            iconName = 'account-circle';
            break;
          default:
            iconName = 'help';
        }

        return <Icon name={iconName} size={size} color={color} />;
      },
      tabBarActiveTintColor: theme.colors.primary,
      tabBarInactiveTintColor: 'gray',
      tabBarStyle: {
        backgroundColor: 'white',
        borderTopWidth: 1,
        borderTopColor: '#e0e0e0',
        paddingBottom: 5,
        paddingTop: 5,
        height: 60,
      },
      headerStyle: {
        backgroundColor: theme.colors.primary,
      },
      headerTintColor: 'white',
      headerTitleStyle: {
        fontWeight: 'bold',
      },
    })}
  >
    <Tab.Screen 
      name="Dashboard" 
      component={DashboardScreen}
      options={{ title: 'Health Dashboard' }}
    />
    <Tab.Screen 
      name="Health" 
      component={HealthMetricsScreen}
      options={{ title: 'Health Metrics' }}
    />
    <Tab.Screen 
      name="Devices" 
      component={DevicesScreen}
      options={{ title: 'My Devices' }}
    />
    <Tab.Screen 
      name="Alerts" 
      component={AlertsScreen}
      options={{ title: 'Health Alerts' }}
    />
    <Tab.Screen 
      name="Profile" 
      component={ProfileScreen}
      options={{ title: 'My Profile' }}
    />
  </Tab.Navigator>
);

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [healthData, setHealthData] = useState({
    latestMetrics: [],
    alerts: [],
    devices: [],
  });

  useEffect(() => {
    // Initialize Firebase services
    initializeApp();

    // Set up authentication state listener
    const unsubscribe = auth().onAuthStateChanged(handleAuthStateChange);

    return unsubscribe;
  }, []);

  const initializeApp = async () => {
    try {
      // Request notification permissions
      await NotificationService.requestPermissions();
      
      // Set up notification handlers
      setupNotificationHandlers();
      
      // Initialize other services
      await HealthMetricsService.initialize();
      
    } catch (error) {
      console.error('App initialization error:', error);
      Alert.alert('Error', 'Failed to initialize app services');
    }
  };

  const handleAuthStateChange = async (firebaseUser: FirebaseAuthTypes.User | null) => {
    try {
      if (firebaseUser) {
        // User is signed in
        const userData: User = {
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: firebaseUser.displayName,
        };
        
        setUser(userData);
        
        // Initialize user-specific services
        await AuthService.setCurrentUser(userData);
        
        // Load initial health data
        await loadHealthData();
        
      } else {
        // User is signed out
        setUser(null);
        setHealthData({ latestMetrics: [], alerts: [], devices: [] });
      }
    } catch (error) {
      console.error('Auth state change error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadHealthData = async () => {
    try {
      const [latestMetrics, alerts, devices] = await Promise.all([
        HealthMetricsService.getLatestMetrics(),
        HealthMetricsService.getAlerts(),
        HealthMetricsService.getDevices(),
      ]);

      setHealthData({
        latestMetrics,
        alerts,
        devices,
      });
    } catch (error) {
      console.error('Error loading health data:', error);
    }
  };

  const setupNotificationHandlers = () => {
    // Handle notification when app is in background
    messaging().onNotificationOpenedApp(remoteMessage => {
      console.log('Notification caused app to open from background:', remoteMessage);
      handleNotificationNavigation(remoteMessage);
    });

    // Handle notification when app is opened from quit state
    messaging().getInitialNotification().then(remoteMessage => {
      if (remoteMessage) {
        console.log('Notification caused app to open from quit state:', remoteMessage);
        handleNotificationNavigation(remoteMessage);
      }
    });

    // Handle notification when app is in foreground
    messaging().onMessage(async remoteMessage => {
      console.log('Foreground notification:', remoteMessage);
      
      // Show local notification
      Alert.alert(
        remoteMessage.notification?.title || 'Health Alert',
        remoteMessage.notification?.body || 'You have a new health alert',
        [
          { text: 'Dismiss', style: 'cancel' },
          { text: 'View', onPress: () => handleNotificationNavigation(remoteMessage) },
        ]
      );
    });
  };

  const handleNotificationNavigation = (remoteMessage: any) => {
    // Navigate to appropriate screen based on notification data
    const { type } = remoteMessage.data || {};
    
    // This would be handled by navigation ref in production
    console.log('Navigate to:', type);
  };

  const authContextValue = {
    user,
    signIn: AuthService.signIn,
    signOut: AuthService.signOut,
    signUp: AuthService.signUp,
    isLoading,
  };

  const healthContextValue = {
    ...healthData,
    refreshHealthData: loadHealthData,
    updateHealthData: setHealthData,
  };

  if (isLoading) {
    // Show loading screen
    return (
      <PaperProvider theme={theme}>
        <SafeAreaProvider>
          <StatusBar barStyle="light-content" backgroundColor={theme.colors.primary} />
          {/* Loading screen component would go here */}
        </SafeAreaProvider>
      </PaperProvider>
    );
  }

  return (
    <PaperProvider theme={theme}>
      <SafeAreaProvider>
        <StatusBar barStyle="light-content" backgroundColor={theme.colors.primary} />
        <AuthContext.Provider value={authContextValue}>
          <HealthContext.Provider value={healthContextValue}>
            <NavigationContainer>
              {user ? <MainTabs /> : <AuthStack />}
            </NavigationContainer>
          </HealthContext.Provider>
        </AuthContext.Provider>
      </SafeAreaProvider>
    </PaperProvider>
  );
};

export default App;