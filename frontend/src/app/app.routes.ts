import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./features/guest/components/landing-page.component').then(m => m.GuestLandingPageComponent)
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
    path: 'guest',
    children: [
      {
        path: '',
        loadComponent: () => import('./features/guest/components/landing-page.component').then(m => m.GuestLandingPageComponent)
      },
      {
        path: 'search',
        loadComponent: () => import('./features/guest/components/guest-search.component').then(m => m.GuestSearchComponent)
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
    path: 'payment',
    canActivate: [authGuard],
    loadComponent: () => import('./features/payment/components/duration-payment-page.component').then(m => m.DurationPaymentPageComponent)
  },
  {
    path: 'payment/:bookingId',
    canActivate: [authGuard],
    loadComponent: () => import('./features/payment/components/payment-page.component').then(m => m.PaymentPageComponent)
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
        path: 'pricing',
        loadComponent: () => import('./features/admin/components/pricing/admin-pricing.component').then(m => m.AdminPricingComponent)
      },
      {
        path: 'checkin',
        loadComponent: () => import('./features/admin/components/admin-checkin.component').then(m => m.AdminCheckinComponent)
      },
      {
        path: 'pricing-rules',
        loadComponent: () => import('./features/admin/components/admin-pricing-rules.component').then(m => m.AdminPricingRulesComponent)
      }
    ]
  },
  {
    path: '**',
    loadComponent: () => import('./shared/components/not-found.component').then(m => m.NotFoundComponent)
  }
];
