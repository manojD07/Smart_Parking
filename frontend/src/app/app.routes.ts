import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./shared/components/role-redirect.component').then(m => m.RoleRedirectComponent)
  },
  {
    path: 'auth',
    canActivate: [guestGuard],
    children: [
      {
        path: 'login',
        loadComponent: () => import('./features/auth/components/login.component').then(m => m.LoginComponent)
      },
      {
        path: 'register',
        loadComponent: () => import('./features/auth/components/register.component').then(m => m.RegisterComponent)
      },
      {
        path: '',
        redirectTo: 'login',
        pathMatch: 'full'
      }
    ]
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./shared/components/dashboard-redirect.component').then(m => m.DashboardRedirectComponent)
  },
  {
    path: 'user-dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'parking',
    canActivate: [authGuard],
    loadComponent: () => import('./features/parking/components/parking-search.component').then(m => m.ParkingSearchComponent)
  },
  {
    path: 'parking/:id',
    canActivate: [authGuard],
    loadComponent: () => import('./features/parking/components/parking-details.component').then(m => m.ParkingDetailsComponent)
  },
  {
    path: 'booking',
    canActivate: [authGuard],
    loadComponent: () => import('./features/booking/components/booking-form.component').then(m => m.BookingFormComponent)
  },
  {
    path: 'bookings',
    canActivate: [authGuard],
    loadComponent: () => import('./features/booking/components/booking-list.component').then(m => m.BookingListComponent)
  },
  {
    path: 'bookings/:id',
    canActivate: [authGuard],
    loadComponent: () => import('./features/booking/components/booking-details.component').then(m => m.BookingDetailsComponent)
  },
  {
    path: 'profile',
    canActivate: [authGuard],
    loadComponent: () => import('./features/profile/profile.component').then(m => m.ProfileComponent)
  },
  {
    path: 'admin',
    canActivate: [authGuard, adminGuard],
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },
      {
        path: 'dashboard',
        loadComponent: () => import('./features/admin/components/admin-dashboard.component').then(m => m.AdminDashboardComponent)
      },
      {
        path: 'users',
        loadComponent: () => import('./features/admin/components/admin-users.component').then(m => m.AdminUsersComponent)
      },
      {
        path: 'parking',
        loadComponent: () => import('./features/admin/components/admin-parking.component').then(m => m.AdminParkingComponent)
      },
      {
        path: 'bookings',
        loadComponent: () => import('./features/admin/components/admin-bookings.component').then(m => m.AdminBookingsComponent)
      },
      {
        path: 'analytics',
        loadComponent: () => import('./features/admin/components/admin-analytics.component').then(m => m.AdminAnalyticsComponent)
      },
      {
        path: 'checkin',
        loadComponent: () => import('./features/admin/components/admin-checkin.component').then(m => m.AdminCheckinComponent)
      }
    ]
  },
  {
    path: '**',
    loadComponent: () => import('./shared/components/not-found.component').then(m => m.NotFoundComponent)
  }
];
