import { Component, OnInit, OnDestroy, Input, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil, combineLatest } from 'rxjs';
import { WebSocketService, WebSocketEventPriority } from '../../core/services/websocket.service';
import { AuthService } from '../../features/auth/services/auth.service';

interface DisplayNotification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'danger';
  priority: WebSocketEventPriority;
  timestamp: Date;
  dismissible: boolean;
  autoHide: boolean;
  duration?: number;
}

@Component({
  selector: 'app-websocket-notifications',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="websocket-notifications">
      <!-- Connection Status Banner -->
      <div 
        class="connection-banner alert mb-3" 
        [class.alert-success]="isConnected"
        [class.alert-warning]="!isConnected"
        *ngIf="showConnectionStatus"
      >
        <div class="d-flex align-items-center justify-content-between">
          <div class="d-flex align-items-center">
            <i class="fas" [class.fa-wifi]="isConnected" [class.fa-exclamation-triangle]="!isConnected" class="me-2"></i>
            <span>
              {{ isConnected ? 'Connected to live updates' : 'Connecting to live updates...' }}
            </span>
          </div>
          <button 
            *ngIf="!isConnected && connectionStats.reconnectAttempts > 0"
            class="btn btn-sm btn-outline-primary"
            (click)="forceReconnect()"
          >
            <i class="fas fa-sync-alt me-1"></i>
            Reconnect
          </button>
        </div>
      </div>

      <!-- Notifications -->
      <div class="notifications-container">
        <div 
          *ngFor="let notification of visibleNotifications; let i = index"
          class="notification-item alert alert-dismissible fade show"
          [class.alert-info]="notification.type === 'info'"
          [class.alert-success]="notification.type === 'success'"
          [class.alert-warning]="notification.type === 'warning'"
          [class.alert-danger]="notification.type === 'danger'"
          [class.priority-critical]="notification.priority === 'critical'"
          [style.animation-delay.ms]="i * 100"
        >
          <div class="d-flex align-items-start">
            <!-- Priority indicator -->
            <div class="priority-indicator me-2">
              <i class="fas" [class]="getPriorityIcon(notification.priority)"></i>
            </div>
            
            <!-- Content -->
            <div class="flex-grow-1">
              <div class="notification-header d-flex align-items-center justify-content-between">
                <h6 class="notification-title mb-1" *ngIf="notification.title">
                  {{ notification.title }}
                </h6>
                <small class="text-muted">
                  {{ getTimeAgo(notification.timestamp) }}
                </small>
              </div>
              <div class="notification-message">
                {{ notification.message }}
              </div>
            </div>

            <!-- Dismiss button -->
            <button 
              *ngIf="notification.dismissible"
              type="button" 
              class="btn-close btn-close-sm ms-2" 
              (click)="dismissNotification(notification.id)"
            ></button>
          </div>

          <!-- Progress bar for auto-hide notifications -->
          <div 
            *ngIf="notification.autoHide && notification.duration"
            class="auto-hide-progress"
          >
            <div 
              class="progress-bar"
              [style.animation-duration.s]="notification.duration"
            ></div>
          </div>
        </div>
      </div>

      <!-- Show more button -->
      <div class="text-center mt-3" *ngIf="hiddenNotifications.length > 0">
        <button 
          class="btn btn-sm btn-outline-secondary"
          (click)="toggleShowAll()"
        >
          <i class="fas fa-chevron-down me-1" *ngIf="!showAll"></i>
          <i class="fas fa-chevron-up me-1" *ngIf="showAll"></i>
          {{ showAll ? 'Show Less' : 'Show ' + hiddenNotifications.length + ' More' }}
        </button>
      </div>

      <!-- Clear all button -->
      <div class="text-center mt-2" *ngIf="allNotifications.length > 0">
        <button 
          class="btn btn-sm btn-link text-muted"
          (click)="clearAll()"
        >
          <i class="fas fa-trash me-1"></i>
          Clear All
        </button>
      </div>
    </div>

    <!-- Custom CSS -->
    <style>
      .websocket-notifications {
        max-height: 400px;
        overflow-y: auto;
      }

      .connection-banner {
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        border: none;
      }

      .notifications-container {
        max-height: 300px;
        overflow-y: auto;
      }

      .notification-item {
        border-radius: 8px;
        border: 1px solid rgba(0,0,0,0.1);
        margin-bottom: 0.75rem;
        animation: slideInRight 0.3s ease-out;
        position: relative;
        overflow: hidden;
      }

      .notification-item.priority-critical {
        border-left: 4px solid #dc3545;
        box-shadow: 0 2px 8px rgba(220, 53, 69, 0.2);
      }

      .notification-item:last-child {
        margin-bottom: 0;
      }

      .priority-indicator {
        min-width: 20px;
        text-align: center;
      }

      .notification-title {
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0;
      }

      .notification-message {
        font-size: 0.85rem;
        line-height: 1.4;
      }

      .btn-close-sm {
        font-size: 0.7rem;
        padding: 0.2rem;
      }

      .auto-hide-progress {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: rgba(0,0,0,0.1);
      }

      .auto-hide-progress .progress-bar {
        height: 100%;
        background: currentColor;
        opacity: 0.7;
        animation: shrink linear;
        transform-origin: left;
      }

      @keyframes slideInRight {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }

      @keyframes shrink {
        from {
          transform: scaleX(1);
        }
        to {
          transform: scaleX(0);
        }
      }

      .btn-link {
        text-decoration: none;
        font-size: 0.8rem;
      }

      .btn-link:hover {
        text-decoration: underline;
      }

      /* Custom scrollbar */
      .websocket-notifications::-webkit-scrollbar,
      .notifications-container::-webkit-scrollbar {
        width: 6px;
      }

      .websocket-notifications::-webkit-scrollbar-track,
      .notifications-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
      }

      .websocket-notifications::-webkit-scrollbar-thumb,
      .notifications-container::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 3px;
      }

      .websocket-notifications::-webkit-scrollbar-thumb:hover,
      .notifications-container::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
      }
    </style>
  `
})
export class WebSocketNotificationsComponent implements OnInit, OnDestroy {
  @Input() maxVisible: number = 5;
  @Input() showConnectionStatus: boolean = true;
  @Input() autoHideDuration: number = 5000; // 5 seconds
  @Input() enableAutoHide: boolean = true;

  allNotifications: DisplayNotification[] = [];
  isConnected = false;
  connectionStats: any = {};
  showAll = false;
  
  private destroy$ = new Subject<void>();
  private currentUser: any = null;

  constructor(
    private webSocketService: WebSocketService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.initializeNotifications();
    this.getCurrentUser();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  get visibleNotifications(): DisplayNotification[] {
    if (this.showAll) {
      return this.allNotifications;
    }
    return this.allNotifications.slice(0, this.maxVisible);
  }

  get hiddenNotifications(): DisplayNotification[] {
    if (this.showAll || this.allNotifications.length <= this.maxVisible) {
      return [];
    }
    return this.allNotifications.slice(this.maxVisible);
  }

  private getCurrentUser(): void {
    this.authService.getCurrentUser()
      .pipe(takeUntil(this.destroy$))
      .subscribe(user => {
        this.currentUser = user;
      });
  }

  private initializeNotifications(): void {
    // Monitor connection status
    combineLatest([
      this.webSocketService.getConnectionStatus(),
      this.webSocketService.connectionStatus$
    ]).pipe(takeUntil(this.destroy$))
      .subscribe(([connected]) => {
        this.isConnected = connected;
        this.connectionStats = this.webSocketService.getConnectionStats();
        this.cdr.detectChanges();
      });

    // Subscribe to user notifications
    this.webSocketService.subscribeToUserNotifications(this.currentUser?.id || '')
      .pipe(takeUntil(this.destroy$))
      .subscribe(notification => {
        this.addNotification({
          id: notification.event_id || this.generateId(),
          title: notification.title || 'Notification',
          message: notification.message,
          type: this.mapPriorityToType(notification.priority),
          priority: notification.priority || WebSocketEventPriority.NORMAL,
          timestamp: new Date(notification.timestamp),
          dismissible: true,
          autoHide: this.enableAutoHide && notification.priority !== WebSocketEventPriority.CRITICAL,
          duration: this.autoHideDuration / 1000
        });
      });

    // Subscribe to system announcements
    this.webSocketService.subscribeToSystemAnnouncements()
      .pipe(takeUntil(this.destroy$))
      .subscribe(announcement => {
        this.addNotification({
          id: this.generateId(),
          title: 'System Announcement',
          message: announcement.message,
          type: this.mapPriorityToType(announcement.priority),
          priority: announcement.priority || WebSocketEventPriority.NORMAL,
          timestamp: new Date(announcement.timestamp),
          dismissible: true,
          autoHide: false, // System announcements should not auto-hide
        });
      });

    // Subscribe to maintenance alerts
    this.webSocketService.subscribeToMaintenanceAlerts()
      .pipe(takeUntil(this.destroy$))
      .subscribe(alert => {
        this.addNotification({
          id: this.generateId(),
          title: 'Maintenance Alert',
          message: alert.message,
          type: 'warning',
          priority: alert.priority || WebSocketEventPriority.HIGH,
          timestamp: new Date(alert.timestamp),
          dismissible: true,
          autoHide: false, // Maintenance alerts should not auto-hide
        });
      });
  }

  private addNotification(notification: DisplayNotification): void {
    // Add to the beginning of the array
    this.allNotifications.unshift(notification);
    
    // Limit total notifications
    if (this.allNotifications.length > 20) {
      this.allNotifications = this.allNotifications.slice(0, 20);
    }

    // Set up auto-hide if enabled
    if (notification.autoHide && notification.duration) {
      setTimeout(() => {
        this.dismissNotification(notification.id);
      }, notification.duration * 1000);
    }

    this.cdr.detectChanges();
  }

  dismissNotification(id: string): void {
    this.allNotifications = this.allNotifications.filter(n => n.id !== id);
    this.cdr.detectChanges();
  }

  toggleShowAll(): void {
    this.showAll = !this.showAll;
    this.cdr.detectChanges();
  }

  clearAll(): void {
    this.allNotifications = [];
    this.showAll = false;
    this.cdr.detectChanges();
  }

  forceReconnect(): void {
    this.webSocketService.forceReconnect();
  }

  private mapPriorityToType(priority: WebSocketEventPriority): 'info' | 'success' | 'warning' | 'danger' {
    switch (priority) {
      case WebSocketEventPriority.CRITICAL:
        return 'danger';
      case WebSocketEventPriority.HIGH:
        return 'warning';
      case WebSocketEventPriority.NORMAL:
        return 'info';
      case WebSocketEventPriority.LOW:
        return 'info';
      default:
        return 'info';
    }
  }

  getPriorityIcon(priority: WebSocketEventPriority): string {
    switch (priority) {
      case WebSocketEventPriority.CRITICAL:
        return 'fa-exclamation-triangle text-danger';
      case WebSocketEventPriority.HIGH:
        return 'fa-exclamation-circle text-warning';
      case WebSocketEventPriority.NORMAL:
        return 'fa-info-circle text-info';
      case WebSocketEventPriority.LOW:
        return 'fa-circle text-secondary';
      default:
        return 'fa-bell text-info';
    }
  }

  getTimeAgo(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (seconds < 30) {
      return 'just now';
    } else if (seconds < 60) {
      return `${seconds}s ago`;
    } else if (minutes < 60) {
      return `${minutes}m ago`;
    } else {
      return `${hours}h ago`;
    }
  }

  private generateId(): string {
    return Date.now().toString() + Math.random().toString(36).substr(2, 9);
  }
}
