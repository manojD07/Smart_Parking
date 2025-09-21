import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { NotificationService, Notification } from '../../core/services/notification.service';

@Component({
  selector: 'app-notification-bell',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="notification-bell dropdown">
      <button 
        class="btn btn-link position-relative p-2 text-decoration-none"
        data-bs-toggle="dropdown"
        aria-expanded="false"
        [class.animate-bell]="hasNewNotifications">
        <i class="fas fa-bell fa-lg" [class]="unreadCount > 0 ? 'text-warning' : 'text-muted'"></i>
        <span 
          *ngIf="unreadCount > 0" 
          class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger animate-pulse">
          {{ unreadCount > 99 ? '99+' : unreadCount }}
          <span class="visually-hidden">unread notifications</span>
        </span>
      </button>
      
      <div class="dropdown-menu dropdown-menu-end notification-dropdown shadow-lg">
        <!-- Header -->
        <div class="dropdown-header d-flex justify-content-between align-items-center py-2">
          <div class="d-flex align-items-center">
            <i class="fas fa-bell me-2 text-primary"></i>
            <span class="fw-bold">Notifications</span>
          </div>
          <div class="d-flex gap-1">
            <button 
              *ngIf="unreadCount > 0"
              class="btn btn-sm btn-outline-primary px-2 py-1"
              (click)="markAllAsRead()"
              [disabled]="loading"
              title="Mark all as read">
              <i class="fas fa-check-double" [class.fa-spin]="loading"></i>
            </button>
            <button 
              class="btn btn-sm btn-outline-secondary px-2 py-1"
              (click)="refreshNotifications()"
              [disabled]="loading"
              title="Refresh">
              <i class="fas fa-sync-alt" [class.fa-spin]="loading"></i>
            </button>
          </div>
        </div>
        
        <!-- Loading State -->
        <div *ngIf="loading && recentNotifications.length === 0" class="text-center py-4">
          <div class="spinner-border spinner-border-sm text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="small text-muted mt-2 mb-0">Loading notifications...</p>
        </div>
        
        <!-- Notifications List -->
        <div class="notification-list" *ngIf="!loading || recentNotifications.length > 0">
          <div 
            *ngFor="let notification of recentNotifications; let i = index; trackBy: trackByNotificationId" 
            class="dropdown-item notification-item p-3"
            [class.unread]="!notification.is_read"
            [class.border-start]="notification.priority === 'critical'"
            [class.border-danger]="notification.priority === 'critical'"
            [class.border-warning]="notification.priority === 'high'"
            [style.animation-delay.ms]="i * 50"
            (click)="markAsRead(notification.id)">
            
            <div class="d-flex align-items-start">
              <!-- Notification Icon -->
              <div class="notification-icon me-3 mt-1">
                <i class="fas" 
                   [class]="getNotificationIcon(notification.type)"
                   [class]="getNotificationColor(notification.priority)"></i>
              </div>
              
              <!-- Notification Content -->
              <div class="notification-content flex-grow-1 min-w-0">
                <div class="d-flex justify-content-between align-items-start mb-1">
                  <h6 class="notification-title mb-0 text-truncate" 
                      [class.fw-bold]="!notification.is_read"
                      [class.text-muted]="notification.is_read">
                    {{ notification.title }}
                  </h6>
                  <small class="text-muted ms-2 flex-shrink-0">
                    {{ formatNotificationTime(notification.created_at) }}
                  </small>
                </div>
                
                <p class="notification-message small mb-1 text-muted">
                  {{ notification.message }}
                </p>
                
                <!-- Priority Badge -->
                <div class="d-flex justify-content-between align-items-center">
                  <span 
                    *ngIf="notification.priority !== 'normal'"
                    class="badge badge-sm"
                    [class]="getPriorityBadgeClass(notification.priority)">
                    {{ notification.priority | titlecase }}
                  </span>
                  
                  <!-- Read Indicator -->
                  <div class="notification-status">
                    <i *ngIf="!notification.is_read" 
                       class="fas fa-circle text-primary" 
                       style="font-size: 0.5rem;"
                       title="Unread"></i>
                    <i *ngIf="notification.is_read" 
                       class="fas fa-check-circle text-success opacity-50" 
                       style="font-size: 0.75rem;"
                       title="Read"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Empty State -->
          <div *ngIf="recentNotifications.length === 0 && !loading" class="text-center py-4">
            <i class="fas fa-bell-slash fa-2x text-muted mb-2"></i>
            <p class="small text-muted mb-0">No notifications yet</p>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="dropdown-divider" *ngIf="recentNotifications.length > 0"></div>
        <div class="dropdown-item-text text-center py-2">
          <a class="btn btn-sm btn-outline-primary text-decoration-none" routerLink="/notifications">
            <i class="fas fa-list me-1"></i>
            View All Notifications
          </a>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .notification-bell .btn {
      border: none !important;
      box-shadow: none !important;
    }

    .notification-bell .btn:focus {
      box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25) !important;
    }

    .notification-dropdown {
      width: 380px;
      max-height: 500px;
      border: none;
      border-radius: 12px;
      overflow: hidden;
    }

    .notification-list {
      max-height: 350px;
      overflow-y: auto;
    }

    .notification-item {
      border: none !important;
      border-radius: 0 !important;
      padding: 0.75rem 1rem !important;
      cursor: pointer;
      transition: all 0.2s ease;
      animation: slideInRight 0.3s ease-out;
      border-left: 3px solid transparent !important;
    }

    .notification-item:hover {
      background-color: #f8f9fa !important;
      transform: translateX(2px);
    }

    .notification-item.unread {
      background-color: #fff3cd !important;
      border-left-color: #ffc107 !important;
    }

    .notification-item.unread:hover {
      background-color: #fff0b3 !important;
    }

    .notification-icon {
      width: 24px;
      text-align: center;
    }

    .notification-title {
      font-size: 0.875rem;
      line-height: 1.2;
    }

    .notification-message {
      font-size: 0.8rem;
      line-height: 1.3;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .badge-sm {
      font-size: 0.65rem;
      padding: 0.25rem 0.5rem;
    }

    .notification-status {
      display: flex;
      align-items: center;
    }

    /* Animations */
    @keyframes slideInRight {
      from {
        transform: translateX(20px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    @keyframes pulse {
      0%, 100% {
        transform: scale(1);
      }
      50% {
        transform: scale(1.05);
      }
    }

    .animate-pulse {
      animation: pulse 2s infinite;
    }

    .animate-bell {
      animation: bell-ring 0.5s ease-in-out;
    }

    @keyframes bell-ring {
      0%, 100% { transform: rotate(0deg); }
      25% { transform: rotate(5deg); }
      75% { transform: rotate(-5deg); }
    }

    /* Custom scrollbar for notification list */
    .notification-list::-webkit-scrollbar {
      width: 6px;
    }

    .notification-list::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 3px;
    }

    .notification-list::-webkit-scrollbar-thumb {
      background: #c1c1c1;
      border-radius: 3px;
    }

    .notification-list::-webkit-scrollbar-thumb:hover {
      background: #a8a8a8;
    }

    /* Responsive design */
    @media (max-width: 768px) {
      .notification-dropdown {
        width: 320px;
      }
      
      .notification-title {
        font-size: 0.8rem;
      }
      
      .notification-message {
        font-size: 0.75rem;
      }
    }
  `]
})
export class NotificationBellComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  // Component state
  recentNotifications: Notification[] = [];
  unreadCount = 0;
  loading = false;
  hasNewNotifications = false;

  constructor(private notificationService: NotificationService) {}

  ngOnInit(): void {
    this.initializeComponent();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeComponent(): void {
    // Subscribe to notifications
    this.notificationService.getNotifications()
      .pipe(takeUntil(this.destroy$))
      .subscribe(notifications => {
        const previousCount = this.recentNotifications.length;
        this.recentNotifications = notifications.slice(0, 5); // Show only recent 5
        
        // Trigger bell animation if new notifications arrived
        if (notifications.length > previousCount && previousCount > 0) {
          this.hasNewNotifications = true;
          setTimeout(() => {
            this.hasNewNotifications = false;
          }, 500);
        }
      });

    // Subscribe to unread count
    this.notificationService.getUnreadCount()
      .pipe(takeUntil(this.destroy$))
      .subscribe(count => {
        this.unreadCount = count;
      });

    // Subscribe to loading state
    this.notificationService.isLoading()
      .pipe(takeUntil(this.destroy$))
      .subscribe(loading => {
        this.loading = loading;
      });
  }

  async markAsRead(notificationId: string): Promise<void> {
    try {
      await this.notificationService.markAsRead(notificationId);
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }

  async markAllAsRead(): Promise<void> {
    try {
      await this.notificationService.markAllAsRead();
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  }

  refreshNotifications(): void {
    this.notificationService.refreshNotifications();
  }

  // Helper methods
  getNotificationIcon(type: string): string {
    return this.notificationService.getNotificationIcon(type);
  }

  getNotificationColor(priority: string): string {
    return this.notificationService.getNotificationColor(priority);
  }

  getPriorityBadgeClass(priority: string): string {
    return this.notificationService.getPriorityBadgeClass(priority);
  }

  formatNotificationTime(dateString: string): string {
    return this.notificationService.formatNotificationTime(dateString);
  }

  trackByNotificationId(index: number, notification: Notification): string {
    return notification.id;
  }
}
