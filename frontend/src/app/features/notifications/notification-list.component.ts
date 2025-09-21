import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { 
  NotificationService, 
  Notification, 
  NotificationStats, 
  NotificationListResponse 
} from '../../core/services/notification.service';

@Component({
  selector: 'app-notification-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="container py-4">
      <div class="row">
        <div class="col-12">
          <!-- Header -->
          <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h2 class="mb-1">
                <i class="fas fa-bell me-2 text-primary"></i>
                Notifications
              </h2>
              <p class="text-muted mb-0" *ngIf="stats">
                {{ stats.unread_count }} unread of {{ stats.total_notifications }} total
              </p>
            </div>
            <div class="d-flex gap-2">
              <button 
                class="btn btn-outline-primary"
                (click)="markAllAsRead()"
                [disabled]="loading || (stats?.unread_count || 0) === 0">
                <i class="fas fa-check-double me-1" [class.fa-spin]="loading"></i>
                Mark All Read
              </button>
              <button 
                class="btn btn-outline-secondary"
                (click)="refreshNotifications()"
                [disabled]="loading">
                <i class="fas fa-sync-alt me-1" [class.fa-spin]="loading"></i>
                Refresh
              </button>
            </div>
          </div>
          
          <!-- Statistics Cards -->
          <div class="row mb-4" *ngIf="stats">
            <div class="col-md-3 mb-3">
              <div class="card border-primary">
                <div class="card-body text-center">
                  <i class="fas fa-bell fa-2x text-primary mb-2"></i>
                  <h4 class="mb-0 text-primary">{{ stats.total_notifications }}</h4>
                  <small class="text-muted">Total Notifications</small>
                </div>
              </div>
            </div>
            <div class="col-md-3 mb-3">
              <div class="card border-warning">
                <div class="card-body text-center">
                  <i class="fas fa-envelope fa-2x text-warning mb-2"></i>
                  <h4 class="mb-0 text-warning">{{ stats.unread_count }}</h4>
                  <small class="text-muted">Unread</small>
                </div>
              </div>
            </div>
            <div class="col-md-3 mb-3">
              <div class="card border-success">
                <div class="card-body text-center">
                  <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
                  <h4 class="mb-0 text-success">{{ stats.read_count }}</h4>
                  <small class="text-muted">Read</small>
                </div>
              </div>
            </div>
            <div class="col-md-3 mb-3">
              <div class="card border-info">
                <div class="card-body text-center">
                  <i class="fas fa-calendar-day fa-2x text-info mb-2"></i>
                  <h4 class="mb-0 text-info">{{ stats.today_count }}</h4>
                  <small class="text-muted">Today</small>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Filters -->
          <div class="card mb-4">
            <div class="card-body">
              <div class="row g-3">
                <div class="col-md-3">
                  <label class="form-label fw-semibold">Filter by Type</label>
                  <select class="form-select" [(ngModel)]="selectedType" (change)="onFilterChange()">
                    <option value="">All Types</option>
                    <option value="booking_confirmation">Booking Confirmations</option>
                    <option value="booking_reminder_start">Start Reminders</option>
                    <option value="booking_reminder_end">End Reminders</option>
                    <option value="checkin_available">Check-in Available</option>
                    <option value="checkin_reminder">Check-in Reminders</option>
                    <option value="checkout_reminder">Check-out Reminders</option>
                    <option value="checkin_overdue">Check-in Overdue</option>
                    <option value="booking_cancelled">Cancellations</option>
                    <option value="payment_confirmation">Payment Confirmations</option>
                  </select>
                </div>
                <div class="col-md-3">
                  <label class="form-label fw-semibold">Filter by Status</label>
                  <select class="form-select" [(ngModel)]="selectedStatus" (change)="onFilterChange()">
                    <option value="">All</option>
                    <option value="unread">Unread Only</option>
                    <option value="read">Read Only</option>
                  </select>
                </div>
                <div class="col-md-3">
                  <label class="form-label fw-semibold">Filter by Priority</label>
                  <select class="form-select" [(ngModel)]="selectedPriority" (change)="onFilterChange()">
                    <option value="">All Priorities</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="normal">Normal</option>
                    <option value="low">Low</option>
                  </select>
                </div>
                <div class="col-md-3 d-flex align-items-end">
                  <button 
                    class="btn btn-outline-secondary w-100"
                    (click)="clearFilters()">
                    <i class="fas fa-times me-1"></i>
                    Clear Filters
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Loading State -->
          <div *ngIf="loading && notifications.length === 0" class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-muted">Loading notifications...</p>
          </div>
          
          <!-- Notifications List -->
          <div class="notification-list" *ngIf="!loading || notifications.length > 0">
            <div 
              *ngFor="let notification of notifications; let i = index; trackBy: trackByNotificationId" 
              class="card mb-3 notification-card"
              [class.unread]="!notification.is_read"
              [class.border-danger]="notification.priority === 'critical'"
              [class.border-warning]="notification.priority === 'high'"
              [style.animation-delay.ms]="i * 100">
              
              <div class="card-body">
                <div class="d-flex align-items-start">
                  <!-- Notification Icon -->
                  <div class="notification-icon me-3">
                    <div class="icon-wrapper rounded-circle d-flex align-items-center justify-content-center"
                         [class]="getIconWrapperClass(notification.priority)">
                      <i class="fas" 
                         [class]="getNotificationIcon(notification.type)"
                         class="text-white"></i>
                    </div>
                  </div>
                  
                  <!-- Notification Content -->
                  <div class="notification-content flex-grow-1 min-w-0">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                      <h5 class="notification-title mb-0" 
                          [class.fw-bold]="!notification.is_read"
                          [class.text-muted]="notification.is_read">
                        {{ notification.title }}
                      </h5>
                      <div class="d-flex align-items-center gap-2">
                        <!-- Priority Badge -->
                        <span 
                          *ngIf="notification.priority !== 'normal'"
                          class="badge"
                          [class]="getPriorityBadgeClass(notification.priority)">
                          {{ notification.priority | titlecase }}
                        </span>
                        
                        <!-- Time -->
                        <small class="text-muted">
                          {{ formatNotificationTime(notification.created_at) }}
                        </small>
                      </div>
                    </div>
                    
                    <p class="notification-message mb-2 text-muted">
                      {{ notification.message }}
                    </p>
                    
                    <!-- Metadata -->
                    <div class="notification-metadata" *ngIf="getMetadata(notification)">
                      <div class="row g-2">
                        <div class="col-auto" *ngIf="getMetadata(notification)?.booking_reference">
                          <small class="badge bg-light text-dark">
                            <i class="fas fa-ticket-alt me-1"></i>
                            {{ getMetadata(notification).booking_reference }}
                          </small>
                        </div>
                        <div class="col-auto" *ngIf="getMetadata(notification)?.lot_name">
                          <small class="badge bg-light text-dark">
                            <i class="fas fa-map-marker-alt me-1"></i>
                            {{ getMetadata(notification).lot_name }}
                          </small>
                        </div>
                        <div class="col-auto" *ngIf="getMetadata(notification)?.total_amount">
                          <small class="badge bg-light text-dark">
                            <i class="fas fa-dollar-sign me-1"></i>
                            {{ getMetadata(notification).total_amount | currency:'USD':'symbol':'1.2-2' }}
                          </small>
                        </div>
                      </div>
                    </div>
                    
                    <!-- Actions -->
                    <div class="notification-actions mt-3">
                      <div class="d-flex justify-content-between align-items-center">
                        <div class="notification-status">
                          <i *ngIf="!notification.is_read" 
                             class="fas fa-circle text-primary me-1" 
                             style="font-size: 0.5rem;"></i>
                          <i *ngIf="notification.is_read" 
                             class="fas fa-check-circle text-success me-1" 
                             style="font-size: 0.75rem;"></i>
                          <small class="text-muted">
                            {{ notification.is_read ? 'Read' : 'Unread' }}
                            <span *ngIf="notification.read_at"> on {{ formatNotificationTime(notification.read_at) }}</span>
                          </small>
                        </div>
                        
                        <div class="d-flex gap-1">
                          <button 
                            *ngIf="!notification.is_read"
                            class="btn btn-sm btn-outline-primary"
                            (click)="markAsRead(notification.id)"
                            title="Mark as read">
                            <i class="fas fa-check"></i>
                          </button>
                          <button 
                            class="btn btn-sm btn-outline-danger"
                            (click)="deleteNotification(notification.id)"
                            title="Delete notification">
                            <i class="fas fa-trash"></i>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Empty State -->
            <div *ngIf="notifications.length === 0 && !loading" class="text-center py-5">
              <div class="empty-state">
                <i class="fas fa-bell-slash fa-4x text-muted mb-3"></i>
                <h4 class="text-muted">No Notifications</h4>
                <p class="text-muted">You don't have any notifications yet.</p>
                <button class="btn btn-primary" (click)="refreshNotifications()">
                  <i class="fas fa-sync-alt me-2"></i>
                  Refresh
                </button>
              </div>
            </div>
          </div>
          
          <!-- Pagination -->
          <div class="d-flex justify-content-between align-items-center mt-4" *ngIf="totalPages > 1">
            <div class="pagination-info">
              <small class="text-muted">
                Showing {{ (currentPage - 1) * pageSize + 1 }} to {{ Math.min(currentPage * pageSize, totalItems) }} 
                of {{ totalItems }} notifications
              </small>
            </div>
            
            <nav aria-label="Notification pagination">
              <ul class="pagination pagination-sm mb-0">
                <li class="page-item" [class.disabled]="currentPage === 1">
                  <button class="page-link" (click)="goToPage(currentPage - 1)" [disabled]="currentPage === 1">
                    <i class="fas fa-chevron-left"></i>
                  </button>
                </li>
                
                <li class="page-item" 
                    *ngFor="let page of getPageNumbers()" 
                    [class.active]="page === currentPage">
                  <button class="page-link" (click)="goToPage(page)">{{ page }}</button>
                </li>
                
                <li class="page-item" [class.disabled]="currentPage === totalPages">
                  <button class="page-link" (click)="goToPage(currentPage + 1)" [disabled]="currentPage === totalPages">
                    <i class="fas fa-chevron-right"></i>
                  </button>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .notification-card {
      border-radius: 12px;
      border: 1px solid #e9ecef;
      transition: all 0.3s ease;
      animation: slideInUp 0.3s ease-out;
    }

    .notification-card:hover {
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
      transform: translateY(-2px);
    }

    .notification-card.unread {
      border-left: 4px solid #ffc107;
      background-color: #fffbf0;
    }

    .notification-card.unread:hover {
      background-color: #fff8e1;
    }

    .notification-icon .icon-wrapper {
      width: 40px;
      height: 40px;
    }

    .icon-wrapper.bg-primary {
      background: linear-gradient(135deg, #007bff, #0056b3);
    }

    .icon-wrapper.bg-warning {
      background: linear-gradient(135deg, #ffc107, #d39e00);
    }

    .icon-wrapper.bg-danger {
      background: linear-gradient(135deg, #dc3545, #a71e2a);
    }

    .icon-wrapper.bg-info {
      background: linear-gradient(135deg, #17a2b8, #117a8b);
    }

    .notification-title {
      font-size: 1.1rem;
      line-height: 1.3;
    }

    .notification-message {
      font-size: 0.95rem;
      line-height: 1.4;
    }

    .notification-metadata .badge {
      font-size: 0.7rem;
      padding: 0.25rem 0.5rem;
    }

    .empty-state {
      padding: 3rem 0;
    }

    .empty-state i {
      opacity: 0.3;
    }

    /* Animations */
    @keyframes slideInUp {
      from {
        transform: translateY(20px);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }

    .pagination .page-link {
      border-radius: 6px;
      margin: 0 2px;
      border: 1px solid #dee2e6;
    }

    .pagination .page-item.active .page-link {
      background-color: #007bff;
      border-color: #007bff;
    }

    /* Responsive design */
    @media (max-width: 768px) {
      .d-flex.justify-content-between {
        flex-direction: column;
        gap: 1rem;
      }
      
      .notification-title {
        font-size: 1rem;
      }
      
      .notification-message {
        font-size: 0.9rem;
      }
      
      .notification-metadata .badge {
        font-size: 0.65rem;
      }
    }
  `]
})
export class NotificationListComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  // Data
  notifications: Notification[] = [];
  stats: NotificationStats | null = null;

  // Filters
  selectedType = '';
  selectedStatus = '';
  selectedPriority = '';

  // Pagination
  currentPage = 1;
  pageSize = 20;
  totalItems = 0;
  totalPages = 0;

  // UI State
  loading = false;

  constructor(private notificationService: NotificationService) {}

  ngOnInit(): void {
    this.initializeComponent();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeComponent(): void {
    // Subscribe to loading state
    this.notificationService.isLoading()
      .pipe(takeUntil(this.destroy$))
      .subscribe(loading => {
        this.loading = loading;
      });

    // Subscribe to stats
    this.notificationService.getStats()
      .pipe(takeUntil(this.destroy$))
      .subscribe(stats => {
        this.stats = stats;
      });

    // Initial load
    this.loadNotifications();
    this.loadStats();
  }

  async loadNotifications(): Promise<void> {
    try {
      const skip = (this.currentPage - 1) * this.pageSize;
      const unreadOnly = this.selectedStatus === 'unread';
      
      const response = await this.notificationService.loadNotifications(
        skip,
        this.pageSize,
        unreadOnly,
        this.selectedType || undefined
      );

      this.notifications = response.notifications;
      this.totalItems = response.total;
      this.totalPages = response.pages;

    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  }

  async loadStats(): Promise<void> {
    try {
      await this.notificationService.loadStats();
    } catch (error) {
      console.error('Failed to load notification stats:', error);
    }
  }

  async markAsRead(notificationId: string): Promise<void> {
    try {
      await this.notificationService.markAsRead(notificationId);
      // Reload current page to reflect changes
      await this.loadNotifications();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }

  async markAllAsRead(): Promise<void> {
    try {
      await this.notificationService.markAllAsRead();
      // Reload current page and stats
      await this.loadNotifications();
      await this.loadStats();
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  }

  async deleteNotification(notificationId: string): Promise<void> {
    try {
      const confirmed = confirm('Are you sure you want to delete this notification?');
      if (!confirmed) return;

      await this.notificationService.deleteNotification(notificationId);
      // Reload current page and stats
      await this.loadNotifications();
      await this.loadStats();
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  }

  refreshNotifications(): void {
    this.loadNotifications();
    this.loadStats();
  }

  onFilterChange(): void {
    this.currentPage = 1; // Reset to first page
    this.loadNotifications();
  }

  clearFilters(): void {
    this.selectedType = '';
    this.selectedStatus = '';
    this.selectedPriority = '';
    this.currentPage = 1;
    this.loadNotifications();
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadNotifications();
    }
  }

  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxVisible = 5;
    
    let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(this.totalPages, start + maxVisible - 1);
    
    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    return pages;
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

  getIconWrapperClass(priority: string): string {
    switch (priority) {
      case 'critical':
        return 'bg-danger';
      case 'high':
        return 'bg-warning';
      case 'normal':
        return 'bg-primary';
      case 'low':
        return 'bg-info';
      default:
        return 'bg-primary';
    }
  }

  formatNotificationTime(dateString: string): string {
    return this.notificationService.formatNotificationTime(dateString);
  }

  getMetadata(notification: Notification): any {
    try {
      return notification.metadata ? JSON.parse(notification.metadata) : null;
    } catch {
      return null;
    }
  }

  trackByNotificationId(index: number, notification: Notification): string {
    return notification.id;
  }

  // Expose Math for template
  Math = Math;
}
