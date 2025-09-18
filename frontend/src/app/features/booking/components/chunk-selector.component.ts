import { Component, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { 
  TimeChunk, 
  ChunkStatus, 
  SlotChunkAvailability, 
  ChunkSelectionEvent, 
  DateGroup, 
  ChunkColorConfig 
} from '../../../core/models/slot-chunks.model';
import { BookingService } from '../services/booking.service';
import { interval, Subscription } from 'rxjs';
import { 
  parseBackendDate, 
  formatIST, 
  nowIST,
  toBackendDate 
} from '../../../core/utils/timezone.util';

@Component({
  selector: 'app-chunk-selector',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="chunk-selector-container">
      <!-- Color Legend -->
      <div class="color-legend mb-3">
        <div class="legend-item">
          <span class="color-box available"></span>
          <small>Available</small>
        </div>
        <div class="legend-item">
          <span class="color-box booked"></span>
          <small>Booked</small>
        </div>
        <div class="legend-item">
          <span class="color-box temp-reserved"></span>
          <small>Reserved</small>
        </div>
        <div class="legend-item">
          <span class="color-box selected"></span>
          <small>Selected</small>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="isLoading" class="text-center py-4">
        <div class="spinner-border spinner-border-sm me-2" role="status"></div>
        Loading time slots...
      </div>

      <!-- Error State -->
      <div *ngIf="errorMessage" class="alert alert-danger" role="alert">
        {{ errorMessage }}
      </div>

      <!-- Chunk Selection Grid -->
      <div *ngIf="!isLoading && !errorMessage" class="chunk-grid-container">
        <div *ngFor="let dateGroup of dateGroups" class="date-group mb-4">
          <!-- Date Header -->
          <div class="date-header sticky-top bg-light py-2 px-3 border-bottom">
            <h6 class="mb-0 text-primary">{{ dateGroup.displayDate }}</h6>
          </div>
          
          <!-- Chunks Grid -->
          <div class="chunks-grid p-3">
            <div 
              *ngFor="let chunk of dateGroup.chunks" 
              class="chunk-slot"
              [class]="getChunkClass(chunk)"
              [attr.disabled]="!isChunkSelectable(chunk)"
              (click)="toggleChunk(chunk)"
              [title]="getChunkTooltip(chunk)">
              <div class="chunk-time">
                {{ formatChunkTime(chunk.start_time) }}
              </div>
              <div class="chunk-end-time">
                {{ formatChunkTime(chunk.end_time) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Selection Summary -->
      <div *ngIf="selectedChunks.length > 0" class="selection-summary mt-3 p-3 bg-light rounded">
        <h6>Selected Time Slots ({{ selectedChunks.length }})</h6>
        <div class="selected-range">
          <strong>{{ getSelectionTimeRange() }}</strong>
        </div>
        <button 
          class="btn btn-outline-danger btn-sm mt-2" 
          (click)="clearSelection()">
          Clear Selection
        </button>
      </div>
    </div>
  `,
  styles: [`
    .chunk-selector-container {
      max-height: 500px;
      overflow-y: auto;
      border: 1px solid #dee2e6;
      border-radius: 0.375rem;
    }

    .color-legend {
      display: flex;
      justify-content: center;
      gap: 1rem;
      padding: 0.75rem;
      background-color: #f8f9fa;
      border-bottom: 1px solid #dee2e6;
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .color-box {
      width: 12px;
      height: 12px;
      border-radius: 2px;
      border: 1px solid #ccc;
    }

    .color-box.available { background-color: #28a745; }
    .color-box.booked { background-color: #dc3545; }
    .color-box.temp-reserved { background-color: #ffc107; }
    .color-box.selected { background-color: #007bff; }

    .date-header {
      position: sticky;
      top: 0;
      z-index: 10;
      border-bottom: 2px solid #007bff !important;
    }

    .chunks-grid {
      display: grid;
      grid-template-columns: repeat(8, 1fr);
      gap: 0.5rem;
      max-height: 200px;
      overflow-y: auto;
    }

    .chunk-slot {
      aspect-ratio: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      border: 1px solid #ccc;
      border-radius: 0.25rem;
      cursor: pointer;
      transition: all 0.2s ease;
      font-size: 0.75rem;
      padding: 0.25rem;
      text-align: center;
    }

    .chunk-slot:hover:not([disabled]) {
      transform: scale(1.05);
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .chunk-slot[disabled] {
      cursor: not-allowed;
      opacity: 0.6;
    }

    .chunk-slot.available {
      background-color: #28a745;
      color: white;
      border-color: #1e7e34;
    }

    .chunk-slot.booked {
      background-color: #dc3545;
      color: white;
      border-color: #c82333;
    }

    .chunk-slot.temp-reserved {
      background-color: #ffc107;
      color: #212529;
      border-color: #e0a800;
    }

    .chunk-slot.selected {
      background-color: #007bff;
      color: white;
      border-color: #0056b3;
      transform: scale(1.1);
      box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
    }

    .chunk-time {
      font-weight: 600;
      line-height: 1;
    }

    .chunk-end-time {
      font-size: 0.65rem;
      opacity: 0.8;
      line-height: 1;
    }

    .selection-summary {
      border-left: 4px solid #007bff;
    }

    /* Mobile Responsive */
    @media (max-width: 768px) {
      .chunks-grid {
        grid-template-columns: repeat(4, 1fr);
      }
      
      .color-legend {
        gap: 0.5rem;
        font-size: 0.875rem;
      }
    }

    @media (max-width: 576px) {
      .chunks-grid {
        grid-template-columns: repeat(3, 1fr);
      }
    }
  `]
})
export class ChunkSelectorComponent implements OnInit, OnDestroy {
  @Input() slotId: string = '';
  @Input() vehicleType: string = '';
  @Output() selectionChanged = new EventEmitter<ChunkSelectionEvent>();
  @Output() timeRangeChanged = new EventEmitter<{ startTime: string; endTime: string; sessionId?: string }>();

  selectedChunks: TimeChunk[] = [];
  dateGroups: DateGroup[] = [];
  isLoading = false;
  errorMessage = '';
  
  private refreshSubscription?: Subscription;

  colorConfig: ChunkColorConfig = {
    available: '#28a745',
    booked: '#dc3545', 
    temp_reserved: '#ffc107',
    selected: '#007bff'
  };

  constructor(private bookingService: BookingService) {}

  ngOnInit() {
    this.loadChunks();
    
    // Auto-refresh every 30 seconds to show real-time updates
    this.refreshSubscription = interval(30000).subscribe(() => {
      this.loadChunks();
    });
  }

  ngOnDestroy() {
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
    }
  }

  async loadChunks() {
    if (!this.slotId) return;

    this.isLoading = true;
    this.errorMessage = '';

    try {
      // Get chunks from now until next day 12:00 AM (IST to UTC conversion)
      const now = nowIST();
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(0, 0, 0, 0); // Next day 12:00 AM

      const startTime = toBackendDate(now);     // Convert IST to UTC for backend
      const endTime = toBackendDate(tomorrow);  // Convert IST to UTC for backend

      console.log('🔄 Loading chunks for slot:', this.slotId);
      console.log('- Start time (UTC):', startTime);
      console.log('- End time (UTC):', endTime);

      const availability = await this.bookingService.getSlotChunkAvailability(
        this.slotId,
        startTime,
        endTime
      ).toPromise();

      console.log('✅ Chunks loaded:', availability);
      this.processChunks(availability.chunks);
      
    } catch (error) {
      console.error('Failed to load chunks:', error);
      this.errorMessage = 'Failed to load time slots. Please try again.';
    } finally {
      this.isLoading = false;
    }
  }

  private processChunks(chunks: TimeChunk[]) {
    // Filter chunks: show if end time is in future OR start time is passed but end time is future
    const now = nowIST();
    const validChunks = chunks.filter(chunk => {
      const endTime = parseBackendDate(chunk.end_time);
      return endTime > now;
    });

    // Group by date
    const grouped = new Map<string, TimeChunk[]>();
    
    validChunks.forEach(chunk => {
      const chunkDate = parseBackendDate(chunk.start_time);
      const dateKey = chunkDate.toDateString();
      
      if (!grouped.has(dateKey)) {
        grouped.set(dateKey, []);
      }
      grouped.get(dateKey)!.push(chunk);
    });

    // Convert to DateGroup array
    this.dateGroups = Array.from(grouped.entries()).map(([dateStr, chunks]) => {
      const date = new Date(dateStr);
      const today = nowIST();
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      
      let displayDate = dateStr;
      if (date.toDateString() === today.toDateString()) {
        displayDate = `Today - ${date.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' })}`;
      } else if (date.toDateString() === tomorrow.toDateString()) {
        displayDate = `Tomorrow - ${date.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' })}`;
      }

      // Sort chunks by time
      chunks.sort((a, b) => parseBackendDate(a.start_time).getTime() - parseBackendDate(b.start_time).getTime());

      return {
        date: dateStr,
        displayDate,
        chunks
      };
    });
  }

  toggleChunk(chunk: TimeChunk) {
    if (!this.isChunkSelectable(chunk)) return;

    const index = this.selectedChunks.findIndex(c => c.id === chunk.id);
    
    if (index > -1) {
      // Deselect
      this.selectedChunks.splice(index, 1);
    } else {
      // Select - maintain continuous selection
      this.selectedChunks.push(chunk);
      this.selectedChunks.sort((a, b) => 
        parseBackendDate(a.start_time).getTime() - parseBackendDate(b.start_time).getTime()
      );
    }

    this.emitSelectionChange();
  }

  clearSelection() {
    this.selectedChunks = [];
    this.emitSelectionChange();
  }

  private emitSelectionChange() {
    const event: ChunkSelectionEvent = {
      selectedChunks: [...this.selectedChunks],
      startTime: this.selectedChunks.length > 0 ? this.selectedChunks[0].start_time : '',
      endTime: this.selectedChunks.length > 0 ? this.selectedChunks[this.selectedChunks.length - 1].end_time : ''
    };

    this.selectionChanged.emit(event);
    
    if (this.selectedChunks.length > 0) {
      this.timeRangeChanged.emit({
        startTime: event.startTime,
        endTime: event.endTime
      });
    }
  }

  isChunkSelectable(chunk: TimeChunk): boolean {
    return chunk.status === ChunkStatus.AVAILABLE;
  }

  getChunkClass(chunk: TimeChunk): string {
    const isSelected = this.selectedChunks.some(c => c.id === chunk.id);
    
    if (isSelected) return 'selected';
    
    switch (chunk.status) {
      case ChunkStatus.AVAILABLE: return 'available';
      case ChunkStatus.BOOKED: return 'booked';
      case ChunkStatus.TEMP_RESERVED: return 'temp-reserved';
      default: return 'available';
    }
  }

  getChunkTooltip(chunk: TimeChunk): string {
    const startTime = this.formatChunkTime(chunk.start_time);
    const endTime = this.formatChunkTime(chunk.end_time);
    const status = chunk.status.replace('_', ' ').toUpperCase();
    
    return `${startTime} - ${endTime} (${status})`;
  }

  formatChunkTime(isoTime: string): string {
    const date = parseBackendDate(isoTime);  // Convert UTC to IST
    return date.toLocaleTimeString('en-IN', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true,
      timeZone: 'Asia/Kolkata'
    });
  }

  getSelectionTimeRange(): string {
    if (this.selectedChunks.length === 0) return '';
    
    const startTime = this.formatChunkTime(this.selectedChunks[0].start_time);
    const endTime = this.formatChunkTime(this.selectedChunks[this.selectedChunks.length - 1].end_time);
    
    return `${startTime} - ${endTime}`;
  }
}
