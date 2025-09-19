import { Component, Input, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil, interval, startWith, combineLatest, filter } from 'rxjs';
import { WebSocketService, WebSocketEventPriority } from '../../core/services/websocket.service';
import { ParkingService } from '../../features/parking/services/parking.service';
import { AvailabilityResponse } from '../../core/models/parking.model';

@Component({
  selector: 'app-realtime-availability',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="realtime-availability">
      <!-- Connection Status -->
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h6 class="mb-0">
          <i class="fas fa-chart-bar me-2"></i>
          Live Availability
        </h6>
        <div class="connection-status">
          <span 
            class="badge" 
            [class]="isConnected ? 'bg-success' : 'bg-warning'"
          >
            <i class="fas" [class]="isConnected ? 'fa-wifi' : 'fa-sync-alt fa-spin'"></i>
            {{ isConnected ? 'Live' : 'Polling' }}
          </span>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading" class="text-center py-3">
        <div class="spinner-border spinner-border-sm text-primary"></div>
        <small class="ms-2">Loading availability...</small>
      </div>

      <!-- Availability Display -->
      <div *ngIf="!loading && availability">
        <div class="availability-card">
          <!-- Progress Bar -->
          <div class="progress mb-2" style="height: 8px;">
            <div
              class="progress-bar"
              [class.bg-success]="availability.occupancy_rate < 70"
              [class.bg-warning]="availability.occupancy_rate >= 70 && availability.occupancy_rate < 90"
              [class.bg-danger]="availability.occupancy_rate >= 90"
              [style.width.%]="availability.occupancy_rate"
            ></div>
          </div>

          <!-- Stats -->
          <div class="row text-center">
            <div class="col-4">
              <div class="stat-item">
                <div class="stat-value text-success">{{ availability.available_slots }}</div>
                <div class="stat-label">Available</div>
              </div>
            </div>
            <div class="col-4">
              <div class="stat-item">
                <div class="stat-value text-primary">{{ availability.occupied_slots }}</div>
                <div class="stat-label">Occupied</div>
              </div>
            </div>
            <div class="col-4">
              <div class="stat-item">
                <div class="stat-value text-secondary">{{ availability.total_slots }}</div>
                <div class="stat-label">Total</div>
              </div>
            </div>
          </div>

          <!-- Occupancy Rate -->
          <div class="text-center mt-2">
            <small class="text-muted">
              {{ availability.occupancy_rate.toFixed(1) }}% Occupied
            </small>
          </div>

          <!-- Last Updated -->
          <div class="text-center mt-2" *ngIf="lastUpdated">
            <small class="text-muted">
              <i class="fas fa-clock me-1"></i>
              Updated {{ getTimeAgo(lastUpdated) }}
            </small>
          </div>

          <!-- Real-time indicator -->
          <div class="realtime-indicator" *ngIf="isConnected">
            <div class="pulse-dot"></div>
            <small class="text-success">Live updates</small>
          </div>
        </div>

        <!-- Recent Updates Ticker -->
        <div class="recent-updates mt-3" *ngIf="recentUpdates.length > 0">
          <div class="update-ticker">
            <small class="text-muted">
              <i class="fas fa-history me-1"></i>
              <span *ngFor="let update of recentUpdates.slice(0, 3); let i = index">
                {{ update.message }}
                <span *ngIf="i < 2" class="mx-2">•</span>
              </span>
            </small>
          </div>
        </div>
      </div>

      <!-- Notifications -->
      <div class="notifications mt-3" *ngIf="showNotifications && notifications.length > 0">
        <div 
          *ngFor="let notification of notifications.slice(0, 2)" 
          class="alert alert-info alert-dismissible fade show py-2"
          [class.alert-warning]="notification.priority === 'high'"
          [class.alert-danger]="notification.priority === 'critical'"
        >
          <div class="d-flex align-items-start">
            <i class="fas fa-bell me-2 mt-1"></i>
            <div class="flex-grow-1">
              <div class="fw-bold" *ngIf="notification.title">{{ notification.title }}</div>
              <div class="small">{{ notification.message }}</div>
              <div class="text-muted small">{{ getTimeAgo(notification.timestamp) }}</div>
            </div>
            <button 
              type="button" 
              class="btn-close btn-close-sm" 
              (click)="dismissNotification(notification)"
            ></button>
          </div>
        </div>
      </div>

      <!-- Maintenance Alerts -->
      <div class="maintenance-alerts mt-3" *ngIf="showMaintenanceAlerts && maintenanceAlerts.length > 0">
        <div 
          *ngFor="let alert of maintenanceAlerts.slice(0, 2)" 
          class="alert alert-warning alert-dismissible fade show py-2"
        >
          <div class="d-flex align-items-start">
            <i class="fas fa-tools me-2 mt-1"></i>
            <div class="flex-grow-1">
              <div class="fw-bold">Maintenance Alert</div>
              <div class="small">{{ alert.message }}</div>
              <div class="text-muted small">
                Type: {{ alert.maintenance_type }} | {{ getTimeAgo(alert.timestamp) }}
              </div>
            </div>
            <button 
              type="button" 
              class="btn-close btn-close-sm" 
              (click)="dismissMaintenanceAlert(alert)"
            ></button>
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div *ngIf="!loading && !availability" class="text-center py-3">
        <i class="fas fa-exclamation-triangle text-warning mb-2"></i>
        <div class="small text-muted">Unable to load availability</div>
        <button 
          class="btn btn-sm btn-outline-primary mt-2" 
          (click)="refresh()"
          [disabled]="loading"
        >
          <i class="fas fa-sync-alt me-1" [class.fa-spin]="loading"></i>
          Retry
        </button>
      </div>

      <!-- Connection Debug Info (dev mode) -->
      <div class="debug-info mt-3" *ngIf="!isConnected && connectionStats.reconnectAttempts > 0">
        <small class="text-muted">
          <i class="fas fa-info-circle me-1"></i>
          Reconnect attempts: {{ connectionStats.reconnectAttempts }}/{{ connectionStats.maxReconnectAttempts }}
          <button 
            class="btn btn-sm btn-link p-0 ms-2" 
            (click)="forceReconnect()"
            title="Force reconnect"
          >
            <i class="fas fa-sync-alt"></i>
          </button>
        </small>
      </div>
    </div>

    <!-- Custom CSS -->
    <style>
      .realtime-availability {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        background: #fff;
      }

      .connection-status .badge {
        font-size: 0.7rem;
      }

      .availability-card {
        position: relative;
      }

      .stat-item {
        padding: 0.5rem 0;
      }

      .stat-value {
        font-size: 1.25rem;
        font-weight: bold;
        line-height: 1;
      }

      .stat-label {
        font-size: 0.75rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .realtime-indicator {
        position: absolute;
        top: -0.5rem;
        right: -0.5rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
        background: rgba(25, 135, 84, 0.1);
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-size: 0.7rem;
      }

      .pulse-dot {
        width: 6px;
        height: 6px;
        background: #198754;
        border-radius: 50%;
        animation: pulse 2s infinite;
      }

      @keyframes pulse {
        0% {
          transform: scale(0.95);
          box-shadow: 0 0 0 0 rgba(25, 135, 84, 0.7);
        }
        
        70% {
          transform: scale(1);
          box-shadow: 0 0 0 10px rgba(25, 135, 84, 0);
        }
        
        100% {
          transform: scale(0.95);
          box-shadow: 0 0 0 0 rgba(25, 135, 84, 0);
        }
      }

      .progress {
        background-color: #e9ecef;
      }

      .progress-bar {
        transition: width 0.6s ease;
      }

      .recent-updates {
        border-top: 1px solid #f1f3f4;
        padding-top: 0.75rem;
      }

      .update-ticker {
        overflow: hidden;
        white-space: nowrap;
      }

      .update-ticker span {
        animation: ticker 15s linear infinite;
      }

      @keyframes ticker {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
      }

      .notifications .alert,
      .maintenance-alerts .alert {
        margin-bottom: 0.5rem;
        border-radius: 6px;
      }

      .notifications .alert:last-child,
      .maintenance-alerts .alert:last-child {
        margin-bottom: 0;
      }

      .btn-close-sm {
        font-size: 0.7rem;
        padding: 0.2rem;
      }

      .debug-info {
        border-top: 1px solid #f1f3f4;
        padding-top: 0.5rem;
      }

      .btn-link {
        text-decoration: none;
        font-size: 0.75rem;
      }

      .btn-link:hover {
        text-decoration: underline;
      }
    </style>
  `
})
export class RealtimeAvailabilityComponent implements OnInit, OnDestroy {
  @Input() lotId!: string;
  @Input() vehicleType: string = 'car';
  @Input() refreshInterval: number = 30000; // 30 seconds
  @Input() showNotifications: boolean = true;
  @Input() showMaintenanceAlerts: boolean = true;

  availability: AvailabilityResponse | null = null;
  loading = true;
  isConnected = false;
  lastUpdated: Date | null = null;
  connectionStats: any = {};
  recentUpdates: any[] = [];
  notifications: any[] = [];
  maintenanceAlerts: any[] = [];
  
  private destroy$ = new Subject<void>();

  constructor(
    private webSocketService: WebSocketService,
    private parkingService: ParkingService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.initializeRealtimeUpdates();
    this.setupFallbackPolling();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeRealtimeUpdates(): void {
    // Monitor WebSocket connection status and stats
    combineLatest([
      this.webSocketService.getConnectionStatus(),
      interval(5000).pipe(startWith(0))
    ]).pipe(takeUntil(this.destroy$))
      .subscribe(([connected]) => {
        this.isConnected = connected;
        this.connectionStats = this.webSocketService.getConnectionStats();
        this.cdr.detectChanges();
      });

    // Subscribe to real-time availability updates for this lot
    this.webSocketService.subscribeToLotAvailability(this.lotId)
      .pipe(
        takeUntil(this.destroy$),
        filter(update => update?.lot_id === this.lotId)
      )
      .subscribe(update => {
        this.updateAvailabilityFromWebSocket(update);
        this.addRecentUpdate({
          message: `${update.vehicle_type} availability updated: ${update.available_slots} available`,
          timestamp: new Date(update.timestamp),
          type: 'availability'
        });
      });

    // Subscribe to notifications
    if (this.showNotifications) {
      this.webSocketService.subscribeToUserNotifications('')
        .pipe(takeUntil(this.destroy$))
        .subscribe(notification => {
          this.addNotification(notification);
        });
    }

    // Subscribe to maintenance alerts
    if (this.showMaintenanceAlerts) {
      this.webSocketService.subscribeToMaintenanceAlerts()
        .pipe(
          takeUntil(this.destroy$),
          filter(alert => !alert.lot_id || alert.lot_id === this.lotId)
        )
        .subscribe(alert => {
          this.addMaintenanceAlert(alert);
        });
    }

    // Subscribe to booking updates for real-time feedback
    this.webSocketService.getUpdatesByType('booking')
      .pipe(
        takeUntil(this.destroy$),
        filter(update => update.data?.lot_id === this.lotId)
      )
      .subscribe(update => {
        this.addRecentUpdate({
          message: this.formatBookingUpdate(update),
          timestamp: update.timestamp,
          type: 'booking'
        });
      });

    // Initial load
    this.loadAvailability();
  }

  private updateAvailabilityFromWebSocket(update: any): void {
    // Update availability from WebSocket event
    if (this.availability) {
      this.availability = {
        ...this.availability,
        available_slots: update.available_slots,
        total_slots: update.total_slots,
        occupied_slots: update.total_slots - update.available_slots,
        occupancy_rate: ((update.total_slots - update.available_slots) / update.total_slots) * 100
      };
    }
    this.lastUpdated = new Date(update.timestamp);
    this.loading = false;
    this.cdr.detectChanges();
  }

  private formatBookingUpdate(update: any): string {
    const eventType = update.data?.event_type || update.type;
    switch (eventType) {
      case 'booking_created':
        return 'New booking created';
      case 'booking_confirmed':
        return 'Booking confirmed';
      case 'booking_cancelled':
        return 'Booking cancelled';
      case 'booking_checked_in':
        return 'Vehicle checked in';
      case 'booking_checked_out':
        return 'Vehicle checked out';
      default:
        return 'Booking updated';
    }
  }

  private addRecentUpdate(update: any): void {
    this.recentUpdates.unshift(update);
    // Keep only last 10 updates
    if (this.recentUpdates.length > 10) {
      this.recentUpdates = this.recentUpdates.slice(0, 10);
    }
  }

  private addNotification(notification: any): void {
    this.notifications.unshift({
      ...notification,
      id: Date.now() + Math.random()
    });
    // Keep only last 5 notifications
    if (this.notifications.length > 5) {
      this.notifications = this.notifications.slice(0, 5);
    }
    this.cdr.detectChanges();
  }

  private addMaintenanceAlert(alert: any): void {
    this.maintenanceAlerts.unshift({
      ...alert,
      id: Date.now() + Math.random()
    });
    // Keep only last 3 alerts
    if (this.maintenanceAlerts.length > 3) {
      this.maintenanceAlerts = this.maintenanceAlerts.slice(0, 3);
    }
    this.cdr.detectChanges();
  }

  private setupFallbackPolling(): void {
    // Polling fallback when WebSocket is not connected
    interval(this.refreshInterval)
      .pipe(
        startWith(0), // Start immediately
        takeUntil(this.destroy$)
      )
      .subscribe(() => {
        // Only poll if WebSocket is not connected
        if (!this.isConnected) {
          this.loadAvailability();
        }
      });
  }

  private loadAvailability(): void {
    if (!this.lotId) return;
    
    this.parkingService.checkAvailability(this.lotId, this.vehicleType)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (availability) => {
          this.availability = availability;
          this.lastUpdated = new Date();
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading availability:', error);
          this.loading = false;
        }
      });
  }

  refresh(): void {
    this.loading = true;
    this.loadAvailability();
  }

  // UI event handlers
  dismissNotification(notification: any): void {
    this.notifications = this.notifications.filter(n => n.id !== notification.id);
    this.cdr.detectChanges();
  }

  dismissMaintenanceAlert(alert: any): void {
    this.maintenanceAlerts = this.maintenanceAlerts.filter(a => a.id !== alert.id);
    this.cdr.detectChanges();
  }

  forceReconnect(): void {
    this.webSocketService.forceReconnect();
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

  // Additional utility methods
  getPriorityColor(priority: string): string {
    switch (priority) {
      case 'critical': return 'danger';
      case 'high': return 'warning';
      case 'normal': return 'info';
      case 'low': return 'secondary';
      default: return 'info';
    }
  }

  getOccupancyStatus(): string {
    if (!this.availability) return 'unknown';
    const rate = this.availability.occupancy_rate;
    if (rate < 50) return 'low';
    if (rate < 80) return 'moderate';
    if (rate < 95) return 'high';
    return 'full';
  }

  getOccupancyIcon(): string {
    const status = this.getOccupancyStatus();
    switch (status) {
      case 'low': return 'fa-parking text-success';
      case 'moderate': return 'fa-parking text-warning';
      case 'high': return 'fa-parking text-danger';
      case 'full': return 'fa-ban text-danger';
      default: return 'fa-question text-muted';
    }
  }
}
