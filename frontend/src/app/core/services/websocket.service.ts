import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, interval, Subject } from 'rxjs';
import { takeUntil, switchMap, catchError, filter, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { ParkingService } from '../../features/parking/services/parking.service';
import { AvailabilityResponse } from '../models/parking.model';

// WebSocket Event Types (matching backend)
export enum WebSocketEventType {
  CLIENT_CONNECTED = 'client_connected',
  CLIENT_DISCONNECTED = 'client_disconnected',
  AVAILABILITY_UPDATE = 'availability_update',
  SLOT_STATUS_CHANGED = 'slot_status_changed',
  LOT_CAPACITY_CHANGED = 'lot_capacity_changed',
  BOOKING_CREATED = 'booking_created',
  BOOKING_CONFIRMED = 'booking_confirmed',
  BOOKING_CANCELLED = 'booking_cancelled',
  BOOKING_CHECKED_IN = 'booking_checked_in',
  BOOKING_CHECKED_OUT = 'booking_checked_out',
  BOOKING_EXPIRED = 'booking_expired',
  USER_NOTIFICATION = 'user_notification',
  SYSTEM_ANNOUNCEMENT = 'system_announcement',
  MAINTENANCE_ALERT = 'maintenance_alert',
  ADMIN_ALERT = 'admin_alert',
  REVENUE_UPDATE = 'revenue_update',
  OCCUPANCY_UPDATE = 'occupancy_update',
  SYSTEM_STATUS = 'system_status',
  ERROR_NOTIFICATION = 'error_notification',
  HEARTBEAT = 'heartbeat'
}

export enum WebSocketEventPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface WebSocketEvent {
  event_id: string;
  event_type: WebSocketEventType;
  priority: WebSocketEventPriority;
  timestamp: string;
  source: string;
  target_users?: string[];
  target_roles?: string[];
  target_lots?: string[];
  data: any;
  message?: string;
}

export interface RealtimeUpdate {
  type: 'availability' | 'booking' | 'notification' | 'system' | 'maintenance';
  data: any;
  timestamp: Date;
  priority?: WebSocketEventPriority;
  event_id?: string;
}

export interface ConnectionConfig {
  url?: string;
  token?: string;
  user_id?: string;
  user_role?: string;
  lot_subscriptions?: string[];
  reconnect?: boolean;
  max_reconnect_attempts?: number;
  reconnect_interval?: number;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService implements OnDestroy {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 5000;
  private isConnected = false;
  private connectionConfig: ConnectionConfig = {};
  
  // Enhanced subjects for different event types
  private updatesSubject = new BehaviorSubject<RealtimeUpdate | null>(null);
  private connectionStatusSubject = new BehaviorSubject<boolean>(false);
  private destroy$ = new Subject<void>();
  
  // Event-specific subjects
  private availabilityUpdatesSubject = new BehaviorSubject<any>(null);
  private bookingUpdatesSubject = new BehaviorSubject<any>(null);
  private notificationsSubject = new BehaviorSubject<any>(null);
  private maintenanceAlertsSubject = new BehaviorSubject<any>(null);
  private systemAnnouncementsSubject = new BehaviorSubject<any>(null);

  // Polling fallback
  private pollingInterval = 30000; // 30 seconds
  private pollingSubject = new Subject<void>();

  // Public observables
  public updates$ = this.updatesSubject.asObservable();
  public connectionStatus$ = this.connectionStatusSubject.asObservable();
  public availabilityUpdates$ = this.availabilityUpdatesSubject.asObservable().pipe(filter(update => update !== null));
  public bookingUpdates$ = this.bookingUpdatesSubject.asObservable().pipe(filter(update => update !== null));
  public notifications$ = this.notificationsSubject.asObservable().pipe(filter(update => update !== null));
  public maintenanceAlerts$ = this.maintenanceAlertsSubject.asObservable().pipe(filter(update => update !== null));
  public systemAnnouncements$ = this.systemAnnouncementsSubject.asObservable().pipe(filter(update => update !== null));

  constructor(private parkingService: ParkingService) {}

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.disconnect();
  }

  connect(config?: ConnectionConfig): void {
    // Store configuration
    this.connectionConfig = {
      url: config?.url || environment.wsUrl,
      token: config?.token,
      user_id: config?.user_id,
      user_role: config?.user_role,
      lot_subscriptions: config?.lot_subscriptions || [],
      reconnect: config?.reconnect !== false,
      max_reconnect_attempts: config?.max_reconnect_attempts || 5,
      reconnect_interval: config?.reconnect_interval || 5000,
      ...config
    };

    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      // Build WebSocket URL with parameters
      const wsUrl = this.buildWebSocketUrl();
      
      this.socket = new WebSocket(wsUrl);
      
      this.socket.onopen = () => {
        console.log('WebSocket connected to backend');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.connectionStatusSubject.next(true);
        
        // Subscribe to lot updates if specified
        if (this.connectionConfig.lot_subscriptions?.length) {
          this.subscribeToLots(this.connectionConfig.lot_subscriptions);
        }
      };

      this.socket.onmessage = (event) => {
        try {
          const webSocketEvent: WebSocketEvent = JSON.parse(event.data);
          this.handleWebSocketEvent(webSocketEvent);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.socket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        this.connectionStatusSubject.next(false);
        
        // Attempt to reconnect if enabled and not a normal closure
        if (this.connectionConfig.reconnect && 
            event.code !== 1000 && 
            this.reconnectAttempts < (this.connectionConfig.max_reconnect_attempts || 5)) {
          setTimeout(() => {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.connectionConfig.max_reconnect_attempts})`);
            this.connect(this.connectionConfig);
          }, this.connectionConfig.reconnect_interval || 5000);
        } else if (this.reconnectAttempts >= (this.connectionConfig.max_reconnect_attempts || 5)) {
          console.log('Max reconnect attempts reached, starting polling fallback');
          this.startPolling();
        }
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      this.startPolling();
    }
  }

  private buildWebSocketUrl(): string {
    const config = this.connectionConfig;
    let url = config.url || environment.wsUrl;
    
    const params: string[] = [];
    
    if (config.token) {
      params.push(`token=${encodeURIComponent(config.token)}`);
    }
    
    if (config.user_id) {
      params.push(`user_id=${encodeURIComponent(config.user_id)}`);
    }
    
    if (config.user_role) {
      params.push(`user_role=${encodeURIComponent(config.user_role)}`);
    }
    
    if (params.length > 0) {
      url += (url.includes('?') ? '&' : '?') + params.join('&');
    }
    
    return url;
  }

  private handleWebSocketEvent(event: WebSocketEvent): void {
    // Convert backend event to frontend format
    const update: RealtimeUpdate = {
      type: this.mapEventTypeToUpdateType(event.event_type),
      data: event.data,
      timestamp: new Date(event.timestamp),
      priority: event.priority,
      event_id: event.event_id
    };

    // Emit to main updates stream
    this.updatesSubject.next(update);

    // Route to specific event streams
    switch (event.event_type) {
      case WebSocketEventType.AVAILABILITY_UPDATE:
      case WebSocketEventType.SLOT_STATUS_CHANGED:
      case WebSocketEventType.LOT_CAPACITY_CHANGED:
        this.availabilityUpdatesSubject.next({
          ...update,
          lot_id: event.data.lot_id,
          vehicle_type: event.data.vehicle_type,
          available_slots: event.data.available_slots,
          total_slots: event.data.total_slots
        });
        break;

      case WebSocketEventType.BOOKING_CREATED:
      case WebSocketEventType.BOOKING_CONFIRMED:
      case WebSocketEventType.BOOKING_CANCELLED:
      case WebSocketEventType.BOOKING_CHECKED_IN:
      case WebSocketEventType.BOOKING_CHECKED_OUT:
      case WebSocketEventType.BOOKING_EXPIRED:
        this.bookingUpdatesSubject.next({
          ...update,
          booking_id: event.data.booking_id,
          user_id: event.data.user_id,
          lot_id: event.data.lot_id,
          slot_id: event.data.slot_id
        });
        break;

      case WebSocketEventType.USER_NOTIFICATION:
        this.notificationsSubject.next({
          ...update,
          title: event.data.title,
          message: event.message,
          notification_type: event.data.notification_type
        });
        break;

      case WebSocketEventType.MAINTENANCE_ALERT:
        this.maintenanceAlertsSubject.next({
          ...update,
          lot_id: event.data.lot_id,
          slot_id: event.data.slot_id,
          maintenance_type: event.data.maintenance_type,
          message: event.message
        });
        break;

      case WebSocketEventType.SYSTEM_ANNOUNCEMENT:
        this.systemAnnouncementsSubject.next({
          ...update,
          message: event.message,
          announcement_type: event.data.announcement_type
        });
        break;

      case WebSocketEventType.HEARTBEAT:
        // Handle heartbeat silently
        console.debug('WebSocket heartbeat received');
        break;

      default:
        console.log('Unhandled WebSocket event type:', event.event_type);
    }
  }

  private mapEventTypeToUpdateType(eventType: WebSocketEventType): 'availability' | 'booking' | 'notification' | 'system' | 'maintenance' {
    switch (eventType) {
      case WebSocketEventType.AVAILABILITY_UPDATE:
      case WebSocketEventType.SLOT_STATUS_CHANGED:
      case WebSocketEventType.LOT_CAPACITY_CHANGED:
        return 'availability';
      
      case WebSocketEventType.BOOKING_CREATED:
      case WebSocketEventType.BOOKING_CONFIRMED:
      case WebSocketEventType.BOOKING_CANCELLED:
      case WebSocketEventType.BOOKING_CHECKED_IN:
      case WebSocketEventType.BOOKING_CHECKED_OUT:
      case WebSocketEventType.BOOKING_EXPIRED:
        return 'booking';
      
      case WebSocketEventType.USER_NOTIFICATION:
        return 'notification';
      
      case WebSocketEventType.MAINTENANCE_ALERT:
        return 'maintenance';
      
      case WebSocketEventType.SYSTEM_ANNOUNCEMENT:
      case WebSocketEventType.SYSTEM_STATUS:
      case WebSocketEventType.HEARTBEAT:
      default:
        return 'system';
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
    this.isConnected = false;
    this.connectionStatusSubject.next(false);
    this.stopPolling();
  }

  // Enhanced subscription methods
  subscribeToLots(lotIds: string[]): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      lotIds.forEach(lotId => {
        this.sendMessage('subscribe_lot', { lot_id: lotId });
      });
    }
  }

  unsubscribeFromLots(lotIds: string[]): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      lotIds.forEach(lotId => {
        this.sendMessage('unsubscribe_lot', { lot_id: lotId });
      });
    }
  }

  subscribeToUserUpdates(userId: string): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.sendMessage('subscribe_user', { user_id: userId });
    }
  }

  private subscribe(channels: string[]): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      const message = {
        type: 'subscribe',
        channels: channels
      };
      this.socket.send(JSON.stringify(message));
    }
  }

  // Fallback polling mechanism
  private startPolling(): void {
    console.log('Starting polling fallback for real-time updates');
    
    interval(this.pollingInterval)
      .pipe(
        takeUntil(this.destroy$),
        takeUntil(this.pollingSubject),
        switchMap(() => this.pollForUpdates()),
        catchError(error => {
          console.error('Polling error:', error);
          return [];
        })
      )
      .subscribe();
  }

  private stopPolling(): void {
    this.pollingSubject.next();
  }

  private pollForUpdates(): Observable<any> {
    // This would typically call multiple endpoints to check for updates
    return new Observable(observer => {
      // For now, we'll just indicate that polling is active
      // In a real implementation, you'd call various API endpoints here
      observer.next({
        type: 'polling',
        message: 'Polling for updates...'
      });
      observer.complete();
    });
  }

  // Enhanced public methods for specific real-time features
  subscribeToLotAvailability(lotId: string): Observable<any> {
    // Subscribe to the lot on WebSocket if connected
    if (this.isConnected) {
      this.subscribeToLots([lotId]);
    }

    return this.availabilityUpdates$.pipe(
      filter(update => update?.lot_id === lotId),
      map(update => ({
        lot_id: update.lot_id,
        vehicle_type: update.vehicle_type,
        available_slots: update.available_slots,
        total_slots: update.total_slots,
        timestamp: update.timestamp,
        event_id: update.event_id
      }))
    );
  }

  subscribeToBookingUpdates(userId: string): Observable<any> {
    // Subscribe to user updates on WebSocket if connected
    if (this.isConnected) {
      this.subscribeToUserUpdates(userId);
    }

    return this.bookingUpdates$.pipe(
      filter(update => update?.user_id === userId),
      map(update => ({
        booking_id: update.booking_id,
        user_id: update.user_id,
        lot_id: update.lot_id,
        slot_id: update.slot_id,
        event_type: update.type,
        timestamp: update.timestamp,
        data: update.data
      }))
    );
  }

  subscribeToUserNotifications(userId: string): Observable<any> {
    return this.notifications$.pipe(
      filter(update => !update.data?.user_id || update.data.user_id === userId),
      map(update => ({
        title: update.title,
        message: update.message,
        notification_type: update.notification_type,
        priority: update.priority,
        timestamp: update.timestamp,
        event_id: update.event_id
      }))
    );
  }

  subscribeToMaintenanceAlerts(): Observable<any> {
    return this.maintenanceAlerts$.pipe(
      map(update => ({
        lot_id: update.lot_id,
        slot_id: update.slot_id,
        maintenance_type: update.maintenance_type,
        message: update.message,
        priority: update.priority,
        timestamp: update.timestamp
      }))
    );
  }

  subscribeToSystemAnnouncements(): Observable<any> {
    return this.systemAnnouncements$.pipe(
      map(update => ({
        message: update.message,
        announcement_type: update.announcement_type,
        priority: update.priority,
        timestamp: update.timestamp
      }))
    );
  }

  // Send messages through WebSocket
  sendMessage(type: string, data: any): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      const message = {
        type,
        data,
        timestamp: new Date().toISOString()
      };
      this.socket.send(JSON.stringify(message));
    }
  }

  // Enhanced utility methods
  isConnectedToWebSocket(): boolean {
    return this.isConnected;
  }

  getConnectionStatus(): Observable<boolean> {
    return this.connectionStatus$;
  }

  getConnectionConfig(): ConnectionConfig {
    return { ...this.connectionConfig };
  }

  updateConnectionConfig(config: Partial<ConnectionConfig>): void {
    this.connectionConfig = { ...this.connectionConfig, ...config };
  }

  // Get connection statistics
  getConnectionStats(): any {
    return {
      isConnected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.connectionConfig.max_reconnect_attempts || 5,
      connectionConfig: this.getConnectionConfig(),
      socketState: this.socket?.readyState,
      socketUrl: this.socket?.url
    };
  }

  // Force reconnection
  forceReconnect(): void {
    console.log('Forcing WebSocket reconnection');
    this.disconnect();
    setTimeout(() => {
      this.reconnectAttempts = 0;
      this.connect(this.connectionConfig);
    }, 1000);
  }

  // Test connection
  testConnection(): Observable<boolean> {
    return new Observable(observer => {
      if (!this.isConnected) {
        observer.next(false);
        observer.complete();
        return;
      }

      // Send ping message and wait for response
      const testMessage = {
        type: 'ping',
        timestamp: new Date().toISOString()
      };

      const timeout = setTimeout(() => {
        observer.next(false);
        observer.complete();
      }, 5000);

      // Listen for any response (indicating connection is working)
      const subscription = this.updates$.pipe(
        filter(update => update !== null),
        takeUntil(interval(5000))
      ).subscribe(() => {
        clearTimeout(timeout);
        observer.next(true);
        observer.complete();
        subscription.unsubscribe();
      });

      this.sendMessage('ping', testMessage);
    });
  }

  // Get filtered updates by type
  getUpdatesByType(type: 'availability' | 'booking' | 'notification' | 'system' | 'maintenance'): Observable<RealtimeUpdate> {
    return this.updates$.pipe(
      filter((update): update is RealtimeUpdate => update !== null && update.type === type)
    );
  }

  // Get filtered updates by priority
  getUpdatesByPriority(priority: WebSocketEventPriority): Observable<RealtimeUpdate> {
    return this.updates$.pipe(
      filter((update): update is RealtimeUpdate => update !== null && update.priority === priority)
    );
  }
}
