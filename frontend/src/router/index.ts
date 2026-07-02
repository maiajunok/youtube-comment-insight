import { createRouter, createWebHistory } from 'vue-router'
import HomeView         from '../features/insight/pages/HomeView.vue'
import HistoryView      from '../features/insight/pages/HistoryView.vue'
import CompareView      from '../features/insight/pages/CompareView.vue'
import SettingsView     from '../features/settings/pages/SettingsView.vue'
import HowToView        from '../pages/HowToView.vue'
import StatsView        from '../pages/StatsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { name: 'home',          path: '/',              component: HomeView         },
    { name: 'history',       path: '/history',       component: HistoryView      },
    { name: 'stats',         path: '/stats',         component: StatsView        },
    { name: 'history-view',  path: '/history/view',  component: HomeView         },
    { name: 'compare',       path: '/compare',       component: CompareView      },
    { name: 'settings',      path: '/settings',      component: SettingsView     },
    { name: 'howto',         path: '/howto',         component: HowToView        },
  ],
})

export default router
