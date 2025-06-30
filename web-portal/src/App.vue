<template>
  <v-app>
    <!-- Navigation drawer for authenticated users -->
    <NavigationDrawer
      v-if="authStore.isAuthenticated"
      v-model="drawerOpen"
      :items="navigationItems"
    />

    <!-- App bar -->
    <AppBar
      v-if="authStore.isAuthenticated"
      :title="currentPageTitle"
      @toggle-drawer="drawerOpen = !drawerOpen"
      @logout="handleLogout"
    />

    <!-- Main content area -->
    <v-main>
      <v-container
        :class="{ 'pa-0': !authStore.isAuthenticated }"
        fluid
      >
        <!-- Router view with transitions -->
        <router-view v-slot="{ Component, route }">
          <transition
            name="page-transition"
            mode="out-in"
          >
            <component
              :is="Component"
              :key="route.path"
            />
          </transition>
        </router-view>
      </v-container>
    </v-main>

    <!-- Global loading overlay -->
    <LoadingOverlay v-if="appStore.isLoading" />

    <!-- Global error snackbar -->
    <ErrorSnackbar
      v-model="appStore.error.show"
      :message="appStore.error.message"
      @close="appStore.clearError"
    />

    <!-- Connection status indicator -->
    <ConnectionStatus />
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'

// Stores
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { usePatientStore } from '@/stores/patient'

// Components
import NavigationDrawer from '@/components/layout/NavigationDrawer.vue'
import AppBar from '@/components/layout/AppBar.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import ErrorSnackbar from '@/components/common/ErrorSnackbar.vue'
import ConnectionStatus from '@/components/common/ConnectionStatus.vue'

// Services
import { socketService } from '@/services/socket'
import { notificationService } from '@/services/notification'

// Composables
import { useTheme } from '@/composables/useTheme'

const router = useRouter()
const route = useRoute()
const toast = useToast()

// Stores
const authStore = useAuthStore()
const appStore = useAppStore()
const patientStore = usePatientStore()

// Theme
const { toggleTheme } = useTheme()

// Reactive data
const drawerOpen = ref(false)

// Computed properties
const currentPageTitle = computed(() => {
  return route.meta?.title as string || 'Health Monitoring Portal'
})

const navigationItems = computed(() => [
  {
    title: 'Dashboard',
    icon: 'mdi-view-dashboard',
    to: '/dashboard',
    role: ['clinician', 'admin']
  },
  {
    title: 'Patients',
    icon: 'mdi-account-group',
    to: '/patients',
    role: ['clinician', 'admin']
  },
  {
    title: 'Analytics',
    icon: 'mdi-chart-line',
    to: '/analytics',
    role: ['clinician', 'admin']
  },
  {
    title: 'Devices',
    icon: 'mdi-devices',
    to: '/devices',
    role: ['clinician', 'admin']
  },
  {
    title: 'Alerts',
    icon: 'mdi-bell-alert',
    to: '/alerts',
    role: ['clinician', 'admin']
  },
  {
    title: 'Reports',
    icon: 'mdi-file-chart',
    to: '/reports',
    role: ['clinician', 'admin']
  },
  {
    title: 'System',
    icon: 'mdi-cog',
    to: '/system',
    role: ['admin']
  },
  {
    title: 'Settings',
    icon: 'mdi-account-cog',
    to: '/settings',
    role: ['clinician', 'admin']
  }
].filter(item => 
  !authStore.currentUser?.role || 
  item.role.includes(authStore.currentUser.role)
))

// Methods
const handleLogout = async () => {
  try {
    await authStore.logout()
    await router.push('/login')
    toast.success('Successfully logged out')
  } catch (error) {
    console.error('Logout error:', error)
    toast.error('Error during logout')
  }
}

const initializeApp = async () => {
  try {
    appStore.setLoading(true)
    
    // Initialize authentication
    await authStore.initializeAuth()
    
    if (authStore.isAuthenticated) {
      // Connect to WebSocket
      await socketService.connect()
      
      // Initialize notification service
      await notificationService.initialize()
      
      // Load initial data
      await patientStore.loadPatients()
    }
  } catch (error) {
    console.error('App initialization error:', error)
    appStore.setError('Failed to initialize application')
  } finally {
    appStore.setLoading(false)
  }
}

// Watchers
watch(
  () => authStore.isAuthenticated,
  async (isAuthenticated) => {
    if (isAuthenticated) {
      // User just logged in
      await socketService.connect()
      await notificationService.initialize()
      await patientStore.loadPatients()
    } else {
      // User just logged out
      socketService.disconnect()
      patientStore.clearPatients()
    }
  }
)

watch(
  () => route.path,
  () => {
    // Close drawer on mobile when navigating
    if (window.innerWidth < 960) {
      drawerOpen.value = false
    }
  }
)

// Lifecycle hooks
onMounted(async () => {
  await initializeApp()
})
</script>

<style lang="scss" scoped>
.page-transition-enter-active,
.page-transition-leave-active {
  transition: all 0.3s ease;
}

.page-transition-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.page-transition-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

:deep(.v-main) {
  padding-top: 64px !important;
}

:deep(.v-container) {
  max-width: 1400px;
}
</style>