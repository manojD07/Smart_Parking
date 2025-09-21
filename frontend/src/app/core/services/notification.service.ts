import { Injectable, OnDestroy } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { BehaviorSubject, Observable, Subject, interval, of } from 'rxjs';
import { takeUntil, catchError, tap, switchMap, filter, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { WebSocketService } from './websocket.service';
import { ToastService } from './toast.service';

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  priority: 'low' | 'normal' | 'high' | 'critical';
  title: string;
  message: string;
  is_read: boolean;
  is_sent: boolean;
  scheduled_at?: string;
  sent_at?: string;
  read_at?: string;
  created_at: string;
  updated_at: string;
  booking_id?: string;
  lot_id?: string;
  metadata?: string;
}

export interface NotificationStats {
  total_notifications: number;
  unread_count: number;
  read_count: number;
  today_count: number;
  this_week_count: number;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService implements OnDestroy {
  private apiUrl = `${environment.apiUrl}/notifications`;
  private destroy$ = new Subject<void>();
  
  // State management
  private notifications$ = new BehaviorSubject<Notification[]>([]);
  private unreadCount$ = new BehaviorSubject<number>(0);
  private stats$ = new BehaviorSubject<NotificationStats | null>(null);
  private loading$ = new BehaviorSubject<boolean>(false);
  
  // Auto-refresh interval
  private refreshInterval = 30000; // 30 seconds
  private autoRefresh$ = new Subject<void>();

  constructor(
    private http: HttpClient,
    private webSocketService: WebSocketService,
    private toastService: ToastService
  ) {
    this.initializeService();
    this.setupAutoRefresh();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.stopAutoRefresh();
  }

  // Public observables
  getNotifications(): Observable<Notification[]> {
    return this.notifications$.asObservable();
  }

  getUnreadCount(): Observable<number> {
    return this.unreadCount$.asObservable();
  }

  getStats(): Observable<NotificationStats | null> {
    return this.stats$.asObservable();
  }

  isLoading(): Observable<boolean> {
    return this.loading$.asObservable();
  }

  // API methods
  async loadNotifications(
    skip: number = 0,
    limit: number = 20,
    unreadOnly: boolean = false,
    notificationType?: string
  ): Promise<NotificationListResponse> {
    try {
      this.loading$.next(true);

      let params = new HttpParams()
        .set('skip', skip.toString())
        .set('limit', limit.toString())
        .set('unread_only', unreadOnly.toString());

      if (notificationType) {
        params = params.set('notification_type', notificationType);
      }

      const response = await this.http.get<NotificationListResponse>(
        this.apiUrl,
        { params }
      ).toPromise();

      if (response) {
        // Update notifications if this is the first page
        if (skip === 0) {
          this.notifications$.next(response.notifications);
        }
        return response;
      }

      throw new Error('No response received');

    } catch (error) {
      console.error('Failed to load notifications:', error);
      this.toastService.showError('Failed to load notifications');
      throw error;
    } finally {
      this.loading$.next(false);
    }
  }

  async loadStats(): Promise<NotificationStats> {
    try {
      const stats = await this.http.get<NotificationStats>(`${this.apiUrl}/stats`).toPromise();
      
      if (stats) {
        this.stats$.next(stats);
        this.unreadCount$.next(stats.unread_count);
        return stats;
      }

      throw new Error('No stats received');

    } catch (error) {
      console.error('Failed to load notification stats:', error);
      throw error;
    }
  }

  async markAsRead(notificationId: string): Promise<boolean> {
    try {
      await this.http.post(`${this.apiUrl}/${notificationId}/read`, {}).toPromise();

      // Update local state
      const notifications = this.notifications$.value;
      const updatedNotifications = notifications.map(n => 
        n.id === notificationId ? { ...n, is_read: true, read_at: new Date().toISOString() } : n
      );
      this.notifications$.next(updatedNotifications);

      // Update unread count
      const currentStats = this.stats$.value;
      if (currentStats) {
        const newStats = {
          ...currentStats,
          unread_count: Math.max(0, currentStats.unread_count - 1),
          read_count: currentStats.read_count + 1
        };
        this.stats$.next(newStats);
        this.unreadCount$.next(newStats.unread_count);
      }

      return true;

    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      this.toastService.showError('Failed to mark notification as read');
      return false;
    }
  }

  async markAllAsRead(): Promise<number> {
    try {
      const response = await this.http.post<{ updated_count: number }>(`${this.apiUrl}/read-all`, {}).toPromise();

      if (response) {
        // Update local state
        const notifications = this.notifications$.value;
        const updatedNotifications = notifications.map(n => ({ 
          ...n, 
          is_read: true, 
          read_at: new Date().toISOString() 
        }));
        this.notifications$.next(updatedNotifications);

        // Update stats
        const currentStats = this.stats$.value;
        if (currentStats) {
          const newStats = {
            ...currentStats,
            unread_count: 0,
            read_count: currentStats.total_notifications
          };
          this.stats$.next(newStats);
          this.unreadCount$.next(0);
        }

        this.toastService.showSuccess(`Marked ${response.updated_count} notifications as read`);
        return response.updated_count;
      }

      return 0;

    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
      this.toastService.showError('Failed to mark notifications as read');
      return 0;
    }
  }

  async deleteNotification(notificationId: string): Promise<boolean> {
    try {
      await this.http.delete(`${this.apiUrl}/${notificationId}`).toPromise();

      // Update local state
      const notifications = this.notifications$.value;
      const notification = notifications.find(n => n.id === notificationId);
      const updatedNotifications = notifications.filter(n => n.id !== notificationId);
      this.notifications$.next(updatedNotifications);

      // Update stats
      const currentStats = this.stats$.value;
      if (currentStats && notification) {
        const newStats = {
          ...currentStats,
          total_notifications: Math.max(0, currentStats.total_notifications - 1),
          unread_count: notification.is_read ? currentStats.unread_count : Math.max(0, currentStats.unread_count - 1),
          read_count: notification.is_read ? Math.max(0, currentStats.read_count - 1) : currentStats.read_count
        };
        this.stats$.next(newStats);
        this.unreadCount$.next(newStats.unread_count);
      }

      this.toastService.showSuccess('Notification deleted');
      return true;

    } catch (error) {
      console.error('Failed to delete notification:', error);
      this.toastService.showError('Failed to delete notification');
      return false;
    }
  }

  async getNotification(notificationId: string): Promise<Notification | null> {
    try {
      const notification = await this.http.get<Notification>(`${this.apiUrl}/${notificationId}`).toPromise();
      return notification || null;

    } catch (error) {
      console.error('Failed to get notification:', error);
      return null;
    }
  }

  // Utility methods
  refreshNotifications(): void {
    this.loadNotifications().catch(console.error);
    this.loadStats().catch(console.error);
  }

  startAutoRefresh(): void {
    this.autoRefresh$.next();
  }

  stopAutoRefresh(): void {
    this.autoRefresh$.next();
  }

  // Notification type helpers
  getNotificationIcon(type: string): string {
    switch (type) {
      case 'booking_confirmation':
        return 'fa-check-circle';
      case 'booking_reminder_start':
        return 'fa-clock';
      case 'booking_reminder_end':
        return 'fa-hourglass-end';
      case 'checkin_available':
        return 'fa-sign-in-alt';
      case 'checkin_reminder':
        return 'fa-door-open';
      case 'checkout_reminder':
        return 'fa-door-closed';
      case 'checkin_overdue':
        return 'fa-exclamation-triangle';
      case 'booking_cancelled':
        return 'fa-times-circle';
      case 'payment_confirmation':
        return 'fa-credit-card';
      case 'booking_expired':
        return 'fa-calendar-times';
      default:
        return 'fa-bell';
    }
  }

  getNotificationColor(priority: string): string {
    switch (priority) {
      case 'critical':
        return 'text-danger';
      case 'high':
        return 'text-warning';
      case 'normal':
        return 'text-info';
      case 'low':
        return 'text-secondary';
      default:
        return 'text-info';
    }
  }

  getPriorityBadgeClass(priority: string): string {
    switch (priority) {
      case 'critical':
        return 'bg-danger';
      case 'high':
        return 'bg-warning';
      case 'normal':
        return 'bg-info';
      case 'low':
        return 'bg-secondary';
      default:
        return 'bg-info';
    }
  }

  formatNotificationTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) {
      return 'just now';
    } else if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  }

  // Private methods
  private initializeService(): void {
    // Only setup WebSocket notifications, don't auto-load data
    // Data will be loaded when components explicitly request it
    this.setupWebSocketNotifications();
  }

  private setupWebSocketNotifications(): void {
    // Subscribe to user notifications via WebSocket
    this.webSocketService.subscribeToUserNotifications('')
      .pipe(
        takeUntil(this.destroy$),
        filter(notification => !!notification)
      )
      .subscribe(notification => {
        this.handleWebSocketNotification(notification);
      });
  }

  private handleWebSocketNotification(wsNotification: any): void {
    try {
      // Convert WebSocket notification to our format
      const notification: Notification = {
        id: wsNotification.notification_id || wsNotification.id,
        user_id: wsNotification.user_id,
        type: wsNotification.type,
        priority: wsNotification.priority || 'normal',
        title: wsNotification.title,
        message: wsNotification.message,
        is_read: false,
        is_sent: true,
        created_at: wsNotification.timestamp || new Date().toISOString(),
        updated_at: wsNotification.timestamp || new Date().toISOString(),
        booking_id: wsNotification.booking_id,
        lot_id: wsNotification.lot_id,
        metadata: wsNotification.metadata
      };

      // Add to notifications list
      const currentNotifications = this.notifications$.value;
      const updatedNotifications = [notification, ...currentNotifications];
      this.notifications$.next(updatedNotifications);

      // Update stats
      const currentStats = this.stats$.value;
      if (currentStats) {
        const newStats = {
          ...currentStats,
          total_notifications: currentStats.total_notifications + 1,
          unread_count: currentStats.unread_count + 1,
          today_count: currentStats.today_count + 1
        };
        this.stats$.next(newStats);
        this.unreadCount$.next(newStats.unread_count);
      }

      // Show toast notification for high/critical priority
      if (notification.priority === 'high' || notification.priority === 'critical') {
        this.toastService.showInfo(notification.message, 8000);
      }

      console.log('📱 Real-time notification received:', notification);

    } catch (error) {
      console.error('Failed to handle WebSocket notification:', error);
    }
  }

  private setupAutoRefresh(): void {
    // Auto-refresh notifications every 30 seconds
    interval(this.refreshInterval)
      .pipe(
        takeUntil(this.destroy$),
        takeUntil(this.autoRefresh$)
      )
      .subscribe(() => {
        this.loadStats().catch(console.error);
      });
  }
}
