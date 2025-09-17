import { Component, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil, interval } from 'rxjs';
import { TimeChunk, SlotAvailability, ChunkReservation, BookingSession } from '../../../core/models/slot-chunks.model';
import { BookingService } from '../services/booking.service';
import { ParkingService } from '../../parking/services/parking.service';

@Component({
  selector: 'app-chunk-selector',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="chunk-selector">
      <!-- Reservation Timer -->
      <div class="alert alert-warning" *ngIf="currentSession && timeRemaining > 0">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <i class="fas fa-clock me-2"></i>
            <strong>Reservation Active:</strong> Complete booking in {{ formatTimeRemaining(timeRemaining) }}
          </div>
          <button class="btn btn-sm btn-outline-warning" (click)="extendReservation()">
            <i class="fas fa-plus me-1"></i>
            Extend (+5 min)
          </button>
        </div>
        <div class="progress mt-2" style="height: 4px;">
          <div 
            class="progress-bar bg-warning" 
            [style.width.%]="(timeRemaining / 600) * 100">
          </div>
        </div>
      </div>

      <!-- Expired Reservation -->
      <div class="alert alert-danger" *ngIf="currentSession && timeRemaining <= 0">
        <i class="fas fa-exclamation-triangle me-2"></i>
        <strong>Reservation Expired!</strong> Please select time slots again.
        <button class="btn btn-sm btn-outline-danger ms-2" (click)="clearExpiredSession()">
          Start Over
        </button>
      </div>

      <!-- Slot Information -->
      <div class="card mb-3" *ngIf="slotId">
        <div class="card-header">
          <h5 class="mb-0">
            <i class="fas fa-parking me-2"></i>
            Parking Slot - Time Selection
          </h5>
        </div>
        <div class="card-body">
          <!-- Time Chunk Grid -->
          <div class="row">
            <div class="col-12">
              <h6 class="mb-3">Select continuous 30-minute time slots:</h6>
              <!-- Compact Color Legend -->
              <div class="color-legend-compact mb-2 p-2 bg-light border rounded d-flex align-items-center justify-content-center flex-wrap">
                <small class="text-muted me-3 mb-1">
                  <i class="fas fa-palette me-1"></i>Colors:
                </small>
                <div class="legend-item-compact me-3 mb-1">
                  <div class="legend-color-compact available"></div>
                  <small>Available</small>
                </div>
                <div class="legend-item-compact me-3 mb-1">
                  <div class="legend-color-compact partial"></div>
                  <small>Partial</small>
                </div>
                <div class="legend-item-compact me-3 mb-1">
                  <div class="legend-color-compact reserved"></div>
                  <small>Reserved</small>
                </div>
                <div class="legend-item-compact mb-1">
                  <div class="legend-color-compact selected"></div>
                  <small>Selected</small>
                </div>
              </div>
              <div class="chunk-container">
                <div *ngFor="let dateGroup of getDateGroups()" class="date-group mb-3">
                  <!-- Date Header -->
                  <div class="date-header bg-white border-bottom pb-2 mb-2">
                    <h6 class="mb-1 text-primary">
                      <i class="fas fa-calendar-day me-2"></i>
                      {{ dateGroup.label }}
                      <span class="badge bg-light text-dark ms-2">{{ dateGroup.chunks.length }} slots</span>
                    </h6>
                  </div>
                  
                  <!-- Chunks Grid for this date -->
                  <div class="chunk-grid-compact">
                    <div 
                      *ngFor="let chunk of dateGroup.chunks; trackBy: trackChunk"
                      class="chunk-item-compact"
                      [class.available]="chunk.status === 'available'"
                      [class.booked]="chunk.status === 'booked'"
                      [class.temp-reserved]="chunk.status === 'temp_reserved'"
                      [class.partial-slot]="isPartialSlot(chunk)"
                      [class.selected]="isChunkSelected(chunk)"
                      [class.selectable]="isChunkSelectable(chunk)"
                      (click)="toggleChunk(chunk)"
                    >
                      <div class="chunk-time-compact">
                        {{ formatChunkTime(chunk.start_time) }}
                      </div>
                      <div class="chunk-end-time">
                        {{ formatChunkTime(chunk.end_time) }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Selection Summary -->
          <div class="mt-4" *ngIf="selectedChunks.length > 0">
            <div class="card bg-light">
              <div class="card-body">
                <h6 class="card-title">
                  <i class="fas fa-clock me-2"></i>
                  Selected Time Slots
                </h6>
                <div class="row">
                  <div class="col-md-4">
                    <small class="text-muted">Duration:</small>
                    <div class="fw-bold">{{ selectedChunks.length * 0.5 }} hour(s)</div>
                  </div>
                  <div class="col-md-4">
                    <small class="text-muted">Time Range:</small>
                    <div class="fw-bold">
                      {{ getFirstChunk()?.start_time ? formatChunkTime(getFirstChunk()!.start_time) : '' }} - 
                      {{ getLastChunk()?.end_time ? formatChunkTime(getLastChunk()!.end_time) : '' }}
                    </div>
                  </div>
                  <div class="col-md-4">
                    <small class="text-muted">Status:</small>
                    <div class="fw-bold" 
                         [class.text-success]="isContinuousSelection()"
                         [class.text-danger]="!isContinuousSelection()">
                      {{ isContinuousSelection() ? 'Valid Selection' : 'Select Continuous Slots' }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="mt-4 d-flex gap-2">
            <button 
              class="btn btn-primary"
              [disabled]="!canReserve()"
              (click)="reserveChunks()"
              *ngIf="!currentSession"
            >
              <i class="fas fa-lock me-2"></i>
              Reserve Selected Slots (10 min)
            </button>
            
            <button 
              class="btn btn-success"
              [disabled]="!canConfirmBooking()"
              (click)="confirmBooking()"
              *ngIf="currentSession && timeRemaining > 0"
            >
              <i class="fas fa-check me-2"></i>
              Confirm Booking
            </button>
            
            <button 
              class="btn btn-outline-secondary"
              (click)="clearSelection()"
            >
              <i class="fas fa-times me-2"></i>
              Clear Selection
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .chunk-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 10px;
      margin-bottom: 1rem;
    }
    
    .chunk-item {
      border: 2px solid #dee2e6;
      border-radius: 8px;
      padding: 10px;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s ease;
      min-height: 80px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    
    .chunk-item.available {
      border-color: #28a745;
      background-color: #f8fff9;
    }
    
    .chunk-item.available:hover {
      background-color: #e8f5e8;
      border-color: #20c997;
    }
    
    .chunk-item.booked {
      border-color: #dc3545;
      background-color: #fff5f5;
      cursor: not-allowed;
      opacity: 0.7;
    }
    
    .chunk-item.temp-reserved {
      border-color: #ffc107;
      background-color: #fffbf0;
      cursor: not-allowed;
      opacity: 0.8;
    }
    
    .chunk-item.selected {
      border-color: #007bff;
      background-color: #e7f3ff;
      border-width: 3px;
    }

    .chunk-item.partial-slot {
      border-color: #17a2b8;
      background-color: #f0f9ff;
      border-style: dashed;
    }
    
    .chunk-item.selectable {
      cursor: pointer;
    }
    
    .chunk-time {
      font-weight: 600;
      font-size: 0.9rem;
      margin-bottom: 5px;
    }
    
    .chunk-status .badge {
      font-size: 0.7rem;
    }

    /* New compact layout styles */
    .chunk-container {
      max-height: 400px;
      overflow-y: auto;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      background-color: #fafafa;
      padding: 15px;
      scroll-behavior: smooth;
    }

    .date-header {
      margin: 0 -15px 10px -15px;
      padding: 10px 15px;
      border-radius: 6px 6px 0 0;
    }

    .chunk-grid-compact {
      display: grid;
      grid-template-columns: repeat(8, 1fr); /* 8 columns for desktop */
      gap: 4px;
      padding: 5px;
      /* Removed individual scrolling - let main container handle all scrolling */
    }

    .date-group {
      border-radius: 8px;
      background-color: #ffffff;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      margin-bottom: 15px !important;
    }

    .chunk-item-compact {
      border: 1px solid #dee2e6;
      border-radius: 4px;
      padding: 2px;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s ease;
      min-height: 35px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      font-size: 0.7rem;
      min-width: 0; /* Allow grid items to shrink */
    }

    .chunk-item-compact.available {
      border-color: #28a745;
      background-color: #f8fff9;
    }

    .chunk-item-compact.available:hover {
      background-color: #e8f5e8;
      border-color: #20c997;
    }

    .chunk-item-compact.booked {
      border-color: #dc3545;
      background-color: #fff5f5;
      cursor: not-allowed;
      opacity: 0.7;
    }

    .chunk-item-compact.temp-reserved {
      border-color: #ffc107;
      background-color: #fffbf0;
      cursor: not-allowed;
      opacity: 0.8;
    }

    .chunk-item-compact.selected {
      border-color: #007bff;
      background-color: #e7f3ff;
      border-width: 3px;
    }

    .chunk-item-compact.partial-slot {
      border-color: #17a2b8;
      background-color: #f0f9ff;
      border-style: dashed;
    }

    .chunk-item-compact.selectable {
      cursor: pointer;
    }

    .chunk-time-compact {
      font-weight: 600;
      font-size: 0.65rem;
      margin-bottom: 1px;
      line-height: 1.0;
    }

    .chunk-end-time {
      font-size: 0.6rem;
      color: #6c757d;
      font-weight: 500;
      line-height: 1.0;
    }

    /* Compact Color Legend Styles */
    .color-legend-compact {
      background-color: #f8f9fa !important;
      min-height: 35px;
    }

    .legend-item-compact {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .legend-color-compact {
      width: 12px;
      height: 12px;
      border-radius: 3px;
      border: 2px solid;
      flex-shrink: 0;
    }

    .legend-color-compact.available {
      background-color: #f8fff9;
      border-color: #28a745;
    }

    .legend-color-compact.partial {
      background-color: #f0f9ff;
      border-color: #17a2b8;
      border-style: dashed;
    }

    .legend-color-compact.reserved {
      background-color: #fffbf0;
      border-color: #ffc107;
    }

    .legend-color-compact.selected {
      background-color: #e7f3ff;
      border-color: #007bff;
      border-width: 2px;
    }
    
    @media (max-width: 768px) {
      .chunk-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
      }
      
      .chunk-item {
        min-height: 70px;
        padding: 8px;
      }

      .chunk-grid-compact {
        grid-template-columns: repeat(4, 1fr); /* 4 columns on mobile */
        gap: 3px;
        /* Removed individual scrolling on mobile too */
      }

      .chunk-item-compact {
        min-height: 32px;
        padding: 2px;
        font-size: 0.65rem;
      }

      .chunk-time-compact {
        font-size: 0.6rem;
        margin-bottom: 0px;
      }

      .chunk-end-time {
        font-size: 0.55rem;
      }

      .legend-color-compact {
        width: 10px;
        height: 10px;
      }

      .color-legend-compact {
        min-height: 30px;
        padding: 8px !important;
      }

      .legend-item-compact {
        gap: 3px;
      }

      .chunk-container {
        max-height: 350px;
        padding: 10px;
      }

      .date-group {
        margin-bottom: 12px !important;
      }
    }
  `]
})
export class ChunkSelectorComponent implements OnInit, OnDestroy {
  @Input() slotId!: string;  // This will be the parking lot ID initially
  @Input() vehicleType!: string;
  
  // Internal properties for slot management
  private actualSlotId: string | null = null;
  private availableSlots: any[] = [];
  @Input() requestedStartTime?: string;
  @Input() requestedEndTime?: string;
  @Output() chunksSelected = new EventEmitter<TimeChunk[]>();
  @Output() timeRangeChanged = new EventEmitter<{startTime: string, endTime: string, sessionId?: string}>();
  @Output() bookingConfirmed = new EventEmitter<any>();
  @Output() reservationCancelled = new EventEmitter<void>();

  availableChunks: TimeChunk[] = [];
  groupedChunks: { [date: string]: TimeChunk[] } = {};
  selectedChunks: TimeChunk[] = [];
  currentSession: BookingSession | null = null;
  timeRemaining = 0;
  loading = false;
  
  private destroy$ = new Subject<void>();
  private timerSubscription?: any;

  constructor(
    private bookingService: BookingService,
    private parkingService: ParkingService
  ) {}

  ngOnInit(): void {
    this.loadChunkAvailability();
    this.startReservationTimer();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    if (this.timerSubscription) {
      this.timerSubscription.unsubscribe();
    }
  }

  loadChunkAvailability(): void {
    if (!this.slotId || !this.vehicleType) {
      console.warn('ChunkSelector: Missing slotId or vehicleType', { slotId: this.slotId, vehicleType: this.vehicleType });
      return;
    }
    
    this.loading = true;
    
    console.log('ChunkSelector: Loading slots for parking lot', { lotId: this.slotId, vehicleType: this.vehicleType });
    
    // First, get available slots from the parking lot
    this.parkingService.getParkingSlots(this.slotId, { 
      vehicle_type: this.vehicleType, 
      status: 'available' 
    }).pipe(takeUntil(this.destroy$)).subscribe({
      next: (slots: any[]) => {
        console.log('ChunkSelector: Received slots', slots);
        
        // Filter slots by vehicle type and availability
        this.availableSlots = slots.filter(slot => 
          slot.slot_type === this.vehicleType && 
          slot.status === 'available'
        );
        
        if (this.availableSlots.length === 0) {
          console.warn('ChunkSelector: No available slots for vehicle type', this.vehicleType);
          this.loading = false;
          return;
        }
        
        // Use the first available slot
        this.actualSlotId = this.availableSlots[0].id;
        console.log('ChunkSelector: Selected slot', this.actualSlotId);
        
        // Now load chunk availability for the selected slot
        this.loadChunksForSlot();
      },
      error: (error) => {
        console.error('ChunkSelector: Failed to load parking slots:', error);
        this.loading = false;
      }
    });
  }

  private loadChunksForSlot(): void {
    if (!this.actualSlotId) {
      console.error('ChunkSelector: No actual slot ID available');
      this.loading = false;
      return;
    }
    
    // Generate extended time range
    const now = new Date();
    
    // Start time: 30 minutes before current time to include one slot that has started
    const startTime = this.requestedStartTime || new Date(now.getTime() - 30 * 60 * 1000).toISOString();
    
    // End time: Next day 11:30 AM
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(11, 30, 0, 0);
    const endTime = this.requestedEndTime || tomorrow.toISOString();
    
    console.log('ChunkSelector: Loading chunks for slot', { 
      slotId: this.actualSlotId, 
      startTime, 
      endTime,
      timeRange: `${this.formatTime(startTime)} to ${this.formatTime(endTime)}`
    });
    
    // Call backend to get chunk availability
    this.bookingService.getSlotChunkAvailability(
      this.actualSlotId,
      startTime,
      endTime
    ).pipe(takeUntil(this.destroy$)).subscribe({
      next: (availability: SlotAvailability) => {
        console.log('ChunkSelector: Received availability data', availability);
        
        // Filter chunks to show:
        // 1. Chunks that haven't started yet (normal case)
        // 2. One chunk that has started but not ended (partial slot)
        const currentTime = new Date();
        const filteredChunks = availability.chunks.filter(chunk => {
          const chunkStart = new Date(chunk.start_time);
          const chunkEnd = new Date(chunk.end_time);
          
          // Include if chunk hasn't started yet OR if it's started but not ended
          return chunkEnd > currentTime;
        });
        
        this.availableChunks = filteredChunks;
        this.groupChunksByDate();
        this.loading = false;
        
        console.log('ChunkSelector: Filtered chunks', {
          total: availability.chunks.length,
          filtered: filteredChunks.length,
          grouped: Object.keys(this.groupedChunks).length + ' dates',
          timeRange: `${this.formatTime(startTime)} to ${this.formatTime(endTime)}`
        });
      },
      error: (error) => {
        console.error('ChunkSelector: Failed to load chunk availability:', error);
        this.loading = false;
      }
    });
  }

  private formatTime(isoString: string): string {
    return new Date(isoString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  }

  toggleChunk(chunk: TimeChunk): void {
    if (!this.isChunkSelectable(chunk)) return;
    
    const index = this.selectedChunks.findIndex(c => c.id === chunk.id);
    if (index > -1) {
      this.selectedChunks.splice(index, 1);
    } else {
      this.selectedChunks.push(chunk);
    }
    
    // Sort selected chunks by time
    this.selectedChunks.sort((a, b) => 
      new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    );
    
    this.chunksSelected.emit(this.selectedChunks);
    
    // Emit time range change
    if (this.selectedChunks.length > 0) {
      const sortedChunks = [...this.selectedChunks].sort((a, b) => 
        new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
      );
      
      this.timeRangeChanged.emit({
        startTime: sortedChunks[0].start_time,
        endTime: sortedChunks[sortedChunks.length - 1].end_time
      });
    }
  }

  isChunkSelected(chunk: TimeChunk): boolean {
    return this.selectedChunks.some(c => c.id === chunk.id);
  }

  isChunkSelectable(chunk: TimeChunk): boolean {
    return chunk.status === 'available' && !this.currentSession;
  }

  isContinuousSelection(): boolean {
    if (this.selectedChunks.length <= 1) return true;
    
    const sorted = [...this.selectedChunks].sort((a, b) => 
      new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    );
    
    for (let i = 0; i < sorted.length - 1; i++) {
      const currentEnd = new Date(sorted[i].end_time);
      const nextStart = new Date(sorted[i + 1].start_time);
      
      if (currentEnd.getTime() !== nextStart.getTime()) {
        return false;
      }
    }
    
    return true;
  }

  canReserve(): boolean {
    return this.selectedChunks.length > 0 && 
           this.isContinuousSelection() && 
           !this.currentSession;
  }

  canConfirmBooking(): boolean {
    return this.currentSession !== null && 
           this.timeRemaining > 0 && 
           this.currentSession.status === 'reserved';
  }

  async reserveChunks(): Promise<void> {
    if (!this.canReserve() || !this.actualSlotId) return;
    
    this.loading = true;
    
    try {
      const reservation = await this.bookingService.reserveSlotChunks({
        slot_id: this.actualSlotId,
        chunk_ids: this.selectedChunks.map(c => c.id),
        start_time: this.getFirstChunk()?.start_time || '',
        end_time: this.getLastChunk()?.end_time || ''
      }).toPromise();
      
      this.currentSession = {
        session_id: reservation.session_id,
        slot_id: this.actualSlotId,
        selected_chunks: this.selectedChunks,
        total_hours: this.selectedChunks.length,
        total_amount: 0, // Will be calculated
        expires_at: reservation.reserved_until,
        status: 'reserved'
      };
      
      this.timeRemaining = 600; // 10 minutes
      this.startCountdown();
      
    } catch (error: any) {
      alert('Failed to reserve slots: ' + error.message);
    } finally {
      this.loading = false;
    }
  }

  async confirmBooking(): Promise<void> {
    if (!this.currentSession) return;
    
    this.currentSession.status = 'confirming';
    
    try {
      const booking = await this.bookingService.confirmChunkBooking({
        session_id: this.currentSession.session_id,
        vehicle_number: 'TEMP123' // This should come from parent form
      }).toPromise();
      
      this.currentSession.status = 'confirmed';
      this.bookingConfirmed.emit(booking);
      
    } catch (error: any) {
      this.currentSession.status = 'reserved';
      alert('Failed to confirm booking: ' + error.message);
    }
  }

  async extendReservation(): Promise<void> {
    if (!this.currentSession) return;
    
    try {
      await this.bookingService.extendReservation(this.currentSession.session_id).toPromise();
      this.timeRemaining += 300; // Add 5 minutes
      
    } catch (error: any) {
      alert('Failed to extend reservation: ' + error.message);
    }
  }

  clearSelection(): void {
    this.selectedChunks = [];
    this.chunksSelected.emit(this.selectedChunks);
    
    // Emit empty time range
    this.timeRangeChanged.emit({
      startTime: '',
      endTime: ''
    });
  }

  clearExpiredSession(): void {
    this.currentSession = null;
    this.timeRemaining = 0;
    this.clearSelection();
    this.loadChunkAvailability(); // Refresh availability
    this.reservationCancelled.emit();
  }

  private startReservationTimer(): void {
    this.timerSubscription = interval(1000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        if (this.timeRemaining > 0) {
          this.timeRemaining--;
        }
      });
  }

  private startCountdown(): void {
    if (this.currentSession) {
      const expiryTime = new Date(this.currentSession.expires_at);
      const updateTimer = () => {
        const now = new Date();
        const remaining = Math.max(0, Math.floor((expiryTime.getTime() - now.getTime()) / 1000));
        this.timeRemaining = remaining;
        
        if (remaining <= 0 && this.currentSession) {
          this.clearExpiredSession();
        }
      };
      
      updateTimer();
      setInterval(updateTimer, 1000);
    }
  }

  getFirstChunk(): TimeChunk | undefined {
    return this.selectedChunks.length > 0 ? 
      this.selectedChunks.sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())[0] : 
      undefined;
  }

  getLastChunk(): TimeChunk | undefined {
    return this.selectedChunks.length > 0 ? 
      this.selectedChunks.sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime())[0] : 
      undefined;
  }

  formatChunkTime(timeString: string): string {
    return new Date(timeString).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  }

  formatTimeRemaining(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  trackChunk(index: number, chunk: TimeChunk): string {
    return chunk.id;
  }

  formatChunkDate(dateTime: string): string {
    return new Date(dateTime).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  }

  isPartialSlot(chunk: TimeChunk): boolean {
    const now = new Date();
    const chunkStart = new Date(chunk.start_time);
    const chunkEnd = new Date(chunk.end_time);
    
    // Partial slot: started but not ended
    return chunkStart <= now && chunkEnd > now && chunk.status === 'available';
  }

  isNextDay(chunk: TimeChunk): boolean {
    const now = new Date();
    const chunkStart = new Date(chunk.start_time);
    
    return chunkStart.getDate() !== now.getDate() || chunkStart.getMonth() !== now.getMonth();
  }

  private groupChunksByDate(): void {
    this.groupedChunks = {};
    
    this.availableChunks.forEach(chunk => {
      const chunkDate = new Date(chunk.start_time);
      const dateKey = chunkDate.toDateString(); // e.g., "Mon Sep 17 2025"
      
      if (!this.groupedChunks[dateKey]) {
        this.groupedChunks[dateKey] = [];
      }
      
      this.groupedChunks[dateKey].push(chunk);
    });
  }

  getDateGroups(): { label: string; chunks: TimeChunk[] }[] {
    const now = new Date();
    const today = now.toDateString();
    const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000).toDateString();
    
    return Object.keys(this.groupedChunks)
      .sort((a, b) => new Date(a).getTime() - new Date(b).getTime())
      .map(dateKey => {
        let label: string;
        
        if (dateKey === today) {
          label = 'Today';
        } else if (dateKey === tomorrow) {
          label = 'Tomorrow';
        } else {
          const date = new Date(dateKey);
          label = date.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'short',
            day: 'numeric'
          });
        }
        
        return {
          label,
          chunks: this.groupedChunks[dateKey].sort((a, b) => 
            new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
          )
        };
      });
  }
}
