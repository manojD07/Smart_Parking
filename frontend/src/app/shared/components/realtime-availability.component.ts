import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil, interval, startWith } from 'rxjs';
import { WebSocketService } from '../../core/services/websocket.service';
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
    </style>
  `
})
export class RealtimeAvailabilityComponent implements OnInit, OnDestroy {
  @Input() lotId!: string;
  @Input() vehicleType: string = 'car';
  @Input() refreshInterval: number = 30000; // 30 seconds

  availability: AvailabilityResponse | null = null;
  loading = true;
  isConnected = false;
  lastUpdated: Date | null = null;
  
  private destroy$ = new Subject<void>();

  constructor(
    private webSocketService: WebSocketService,
    private parkingService: ParkingService
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
    // Monitor WebSocket connection status
    this.webSocketService.getConnectionStatus()
      .pipe(takeUntil(this.destroy$))
      .subscribe(connected => {
        this.isConnected = connected;
      });

    // Subscribe to real-time availability updates for this lot
    this.webSocketService.subscribeToLotAvailability(this.lotId)
      .pipe(takeUntil(this.destroy$))
      .subscribe(availability => {
        this.availability = availability;
        this.lastUpdated = new Date();
        this.loading = false;
      });

    // Initial load
    this.loadAvailability();
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
}
