import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { AuthService } from '../../features/auth/services/auth.service';
import { User } from '../../core/models/user.model';
import { NotificationBellComponent } from './notification-bell.component';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule, NotificationBellComponent],
  template: `
      <nav class="navbar navbar-expand-lg navbar-dark fixed-top" style="background: linear-gradient(135deg, #4e73df 0%, #224abe 100%) !important; min-height: 60px; z-index: 1030;">
      <div class="container">
        <a class="navbar-brand fw-bold brand-link" routerLink="/">
          <i class="fas fa-parking me-2"></i>
          Smart Parking
        </a>

        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
          aria-controls="navbarNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <!-- Admin Menu Items -->
            <li class="nav-item" *ngIf="isAuthenticated && currentUser?.is_admin">
              <a class="nav-link" routerLink="/admin/dashboard" routerLinkActive="active" (click)="collapseNavbar()">
                <i class="fas fa-tachometer-alt me-1"></i>
                Dashboard
              </a>
            </li>
            <li class="nav-item" *ngIf="isAuthenticated && currentUser?.is_admin">
              <a class="nav-link" routerLink="/admin/users" routerLinkActive="active">
                <i class="fas fa-users me-1"></i>
                Users
              </a>
            </li>
            <li class="nav-item" *ngIf="isAuthenticated && currentUser?.is_admin">
              <a class="nav-link" routerLink="/admin/parking" routerLinkActive="active">
                <i class="fas fa-parking me-1"></i>
                Parking
              </a>
            </li>
            <li class="nav-item" *ngIf="isAuthenticated && currentUser?.is_admin">
              <a class="nav-link" routerLink="/admin/bookings" routerLinkActive="active">
                <i class="fas fa-ticket-alt me-1"></i>
                Bookings
              </a>
            </li>
            <li class="nav-item" *ngIf="isAuthenticated && currentUser?.is_admin">
              <a class="nav-link" routerLink="/admin/analytics" routerLinkActive="active">
                <i class="fas fa-chart-line me-1"></i>
                Analytics
              </a>
            </li>
            <li class="nav-item" *ngIf="isAuthenticated && currentUser?.is_admin">
              <a class="nav-link" routerLink="/admin/checkin" routerLinkActive="active">
                <i class="fas fa-sign-in-alt me-1"></i>
                Check-In
              </a>
            </li>
            <li class="nav-item" *ngIf="isAuthenticated && currentUser?.is_admin">
              <a class="nav-link" routerLink="/admin/pricing" routerLinkActive="active" (click)="collapseNavbar()">
                <i class="fas fa-tags me-1"></i>
                Pricing
              </a>
            </li>

            <!-- Regular User Menu Items -->
            <li class="nav-item" *ngIf="isAuthenticated && !currentUser?.is_admin">
              <a class="nav-link" routerLink="/user-dashboard" routerLinkActive="active" (click)="collapseNavbar()">
                <i class="fas fa-tachometer-alt me-1"></i>
                Dashboard
              </a>
            </li>
            <li class="nav-item" *ngIf="isAuthenticated && !currentUser?.is_admin">
              <a class="nav-link" routerLink="/parking" routerLinkActive="active" (click)="collapseNavbar()">
                <i class="fas fa-map-marker-alt me-1"></i>
                Find Parking
              </a>
            </li>
            <li class="nav-item" *ngIf="isAuthenticated && !currentUser?.is_admin">
              <a class="nav-link" routerLink="/bookings" routerLinkActive="active" (click)="collapseNavbar()">
                <i class="fas fa-ticket-alt me-1"></i>
                My Bookings
              </a>
            </li>
          </ul>

          <ul class="navbar-nav">
            <!-- Notification Bell -->
            <li class="nav-item" *ngIf="isAuthenticated && currentUser">
              <app-notification-bell></app-notification-bell>
            </li>
            
            <!-- User Profile Link -->
            <li class="nav-item" *ngIf="isAuthenticated && currentUser">
              <a class="nav-link" routerLink="/profile" routerLinkActive="active">
                <i class="fas fa-user me-1"></i>
                {{ currentUser.first_name }}
              </a>
            </li>
            
            <!-- Logout Button -->
            <li class="nav-item" *ngIf="isAuthenticated">
              <button class="btn btn-outline-light ms-2" (click)="logout($event)">
                <i class="fas fa-sign-out-alt me-1"></i>
                Logout
              </button>
            </li>
            
            <!-- Original Dropdown (as fallback) -->
            <li class="nav-item dropdown d-none" *ngIf="isAuthenticated && currentUser">
              <a
                class="nav-link dropdown-toggle"
                href="#"
                id="navbarDropdown"
                role="button"
                data-bs-toggle="dropdown"
                aria-expanded="false"
              >
                <i class="fas fa-user-circle me-1"></i>
                {{ currentUser.first_name }} {{ currentUser.last_name }}
              </a>
              <ul class="dropdown-menu dropdown-menu-end">
                <li>
                  <a class="dropdown-item" routerLink="/profile">
                    <i class="fas fa-user me-2"></i>
                    Profile
                  </a>
                </li>
                <li><hr class="dropdown-divider" /></li>
                <li>
                  <a class="dropdown-item" href="#" (click)="logout($event)">
                    <i class="fas fa-sign-out-alt me-2"></i>
                    Logout
                  </a>
                </li>
              </ul>
            </li>

            <li class="nav-item" *ngIf="!isAuthenticated">
              <a class="nav-link" routerLink="/auth/login">
                <i class="fas fa-sign-in-alt me-1"></i>
                Login
              </a>
            </li>
            <li class="nav-item" *ngIf="!isAuthenticated">
              <a class="nav-link" routerLink="/auth/register">
                <i class="fas fa-user-plus me-1"></i>
                Register
              </a>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  `,
  styles: [`
    .brand-link {
      color: #ffffff !important;
      font-size: 1.25rem;
      text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
      text-decoration: none !important;
      transition: all 0.3s ease;
    }

    .brand-link:hover {
      color: #f8f9fa !important;
      text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.7);
      transform: translateY(-1px);
    }

    .brand-link i {
      color: #ffffff !important;
      text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
    }

    .navbar {
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    /* Ensure navbar brand is always visible */
    .navbar-brand {
      z-index: 1050;
      position: relative;
    }

    /* High contrast fallback */
    @media (prefers-contrast: high) {
      .brand-link {
        color: #ffffff !important;
        background-color: rgba(0, 0, 0, 0.3);
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
      }
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
      .brand-link {
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
      }
    }
  `]
})
export class NavbarComponent implements OnDestroy {
  currentUser: User | null = null;
  isAuthenticated = false;
  private destroy$ = new Subject<void>();

  constructor(private authService: AuthService) {
    this.authService.currentUser$
      .pipe(takeUntil(this.destroy$))
      .subscribe(user => {
        this.currentUser = user;
        console.log('Navbar: Current user updated:', user);
        console.log('Navbar: Is admin?', user?.is_admin);
      });

    this.authService.isAuthenticated$
      .pipe(takeUntil(this.destroy$))
      .subscribe(isAuth => {
        this.isAuthenticated = isAuth;
        console.log('Navbar: Authentication status:', isAuth);
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }


  collapseNavbar(): void {
    // Collapse the mobile menu when a menu item is clicked
    const navbarCollapse = document.getElementById('navbarNav');
    if (navbarCollapse && navbarCollapse.classList.contains('show')) {
      const bsCollapse = new (window as any).bootstrap.Collapse(navbarCollapse);
      bsCollapse.hide();
    }
  }

  logout(event: Event): void {
    event.preventDefault();
    console.log('Logout button clicked');
    console.log('Current user before logout:', this.currentUser);
    console.log('Is authenticated before logout:', this.isAuthenticated);
    
    this.authService.logout();
    
    console.log('Logout method called');
    
    // Force reload after logout to ensure clean state
    setTimeout(() => {
      window.location.reload();
    }, 100);
  }
}
