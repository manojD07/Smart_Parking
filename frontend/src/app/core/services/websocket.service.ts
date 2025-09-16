import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, interval, Subject } from 'rxjs';
import { takeUntil, switchMap, catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { ParkingService } from '../../features/parking/services/parking.service';
import { AvailabilityResponse } from '../models/parking.model';

export interface RealtimeUpdate {
  type: 'availability' | 'booking' | 'notification';
  data: any;
  timestamp: Date;
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
  
  private updatesSubject = new BehaviorSubject<RealtimeUpdate | null>(null);
  private connectionStatusSubject = new BehaviorSubject<boolean>(false);
  private destroy$ = new Subject<void>();

  // Polling fallback
  private pollingInterval = 30000; // 30 seconds
  private pollingSubject = new Subject<void>();

  public updates$ = this.updatesSubject.asObservable();
  public connectionStatus$ = this.connectionStatusSubject.asObservable();

  constructor(private parkingService: ParkingService) {}

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.disconnect();
  }

  connect(token?: string): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const wsUrl = token 
        ? `${environment.wsUrl}?token=${token}`
        : environment.wsUrl;
      
      this.socket = new WebSocket(wsUrl);
      
      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.connectionStatusSubject.next(true);
        
        // Send initial subscription for real-time updates
        this.subscribe(['availability', 'booking']);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const update: RealtimeUpdate = {
            type: data.type || 'notification',
            data: data.data || data,
            timestamp: new Date()
          };
          
          this.updatesSubject.next(update);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.socket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        this.connectionStatusSubject.next(false);
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          setTimeout(() => {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            this.connect(token);
          }, this.reconnectInterval);
        } else {
          // Fallback to polling
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

  disconnect(): void {
    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
    this.isConnected = false;
    this.connectionStatusSubject.next(false);
    this.stopPolling();
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

  // Public methods for specific real-time features
  subscribeToLotAvailability(lotId: string): Observable<AvailabilityResponse> {
    return new Observable(observer => {
      // Subscribe to WebSocket updates for this specific lot
      const subscription = this.updates$.subscribe(update => {
        if (update && 
            update.type === 'availability' && 
            update.data.lot_id === lotId) {
          observer.next(update.data.availability);
        }
      });

      // Cleanup
      return () => subscription.unsubscribe();
    });
  }

  subscribeToBookingUpdates(userId: string): Observable<any> {
    return new Observable(observer => {
      const subscription = this.updates$.subscribe(update => {
        if (update && 
            update.type === 'booking' && 
            update.data.user_id === userId) {
          observer.next(update.data);
        }
      });

      return () => subscription.unsubscribe();
    });
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

  // Utility methods
  isConnectedToWebSocket(): boolean {
    return this.isConnected;
  }

  getConnectionStatus(): Observable<boolean> {
    return this.connectionStatus$;
  }
}
