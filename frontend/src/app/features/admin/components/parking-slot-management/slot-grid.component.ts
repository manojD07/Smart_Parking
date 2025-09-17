import { Component, Input, Output, EventEmitter, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// Services
import { ParkingSlotService, ParkingSlot } from '../../../../core/services/parking-slot.service';
import { ToastService } from '../../../../core/services/toast.service';

// Components
import { SlotStatusLegendComponent } from './slot-status-legend.component';
import { LoadingStateComponent } from '../shared/loading-state.component';

@Component({
  selector: 'app-slot-grid',
  standalone: true,
  imports: [CommonModule, FormsModule, SlotStatusLegendComponent, LoadingStateComponent],
  template: `
    <div class="slot-grid-container">
      <!-- Header with Filters and Stats -->
      <div class="slot-grid-header">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <div>
            <h5 class="mb-1">
              <i class="fas fa-th-large me-2"></i>
              Parking Slots
            </h5>
            <p class="text-muted mb-0" *ngIf="lotName">{{ lotName }}</p>
          </div>
          
          <div class="d-flex gap-2">
            <button 
              class="btn btn-outline-primary btn-sm"
              (click)="refreshSlots()"
              [disabled]="loading">
              <i class="fas fa-sync-alt me-1" [class.fa-spin]="loading"></i>
              Refresh
            </button>
            <button 
              class="btn btn-primary btn-sm"
              (click)="openAddSlotsModal()">
              <i class="fas fa-plus me-1"></i>
              Add Slots
            </button>
          </div>
        </div>

        <!-- Filters -->
        <div class="filters-section mb-3">
          <div class="row g-2">
            <div class="col-md-3">
              <select class="form-select form-select-sm" [(ngModel)]="selectedVehicleType" (ngModelChange)="onFilterChange()">
                <option value="">All Vehicle Types</option>
                <option value="car">Cars Only</option>
                <option value="bike">Bikes Only</option>
              </select>
            </div>
            <div class="col-md-3">
              <select class="form-select form-select-sm" [(ngModel)]="selectedStatus" (ngModelChange)="onFilterChange()">
                <option value="">All Status</option>
                <option value="available">Available</option>
                <option value="occupied">Occupied</option>
                <option value="reserved">Reserved</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            <div class="col-md-6 d-flex align-items-center">
              <div class="form-check form-switch me-3">
                <input 
                  class="form-check-input" 
                  type="checkbox" 
                  id="autoRefresh"
                  [(ngModel)]="autoRefresh"
                  (ngModelChange)="toggleAutoRefresh()">
                <label class="form-check-label" for="autoRefresh">
                  Auto Refresh (30s)
                </label>
              </div>
              <small class="text-muted" *ngIf="lastUpdated">
                Last updated: {{ formatTime(lastUpdated) }}
              </small>
            </div>
          </div>
        </div>

        <!-- Status Legend -->
        <div class="mb-4">
          <app-slot-status-legend
            [compact]="true"
            [availableCount]="slotStats.available"
            [occupiedCount]="slotStats.occupied"
            [reservedCount]="slotStats.reserved"
            [inactiveCount]="slotStats.inactive">
          </app-slot-status-legend>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading && slots.length === 0">
        <app-loading-state 
          type="spinner" 
          loadingText="Loading parking slots..."
          size="lg">
        </app-loading-state>
      </div>

      <!-- Empty State -->
      <div *ngIf="!loading && slots.length === 0" class="empty-state">
        <div class="text-center py-5">
          <i class="fas fa-th-large fa-3x text-muted mb-3"></i>
          <h5>No Slots Found</h5>
          <p class="text-muted">This parking lot doesn't have any slots yet.</p>
          <button class="btn btn-primary" (click)="openAddSlotsModal()">
            <i class="fas fa-plus me-2"></i>Add First Slots
          </button>
        </div>
      </div>

      <!-- Slot Grids -->
      <div *ngIf="!loading && slots.length > 0">
        <!-- Car Slots Section -->
        <div *ngIf="groupedSlots.carSlots.length > 0" class="slot-section">
          <div class="section-header">
            <h6 class="section-title">
              <i class="fas fa-car text-primary me-2"></i>
              Car Slots ({{ groupedSlots.carSlots.length }})
            </h6>
          </div>
          
          <div class="slot-grid car-grid">
            <div 
              *ngFor="let slot of groupedSlots.carSlots; trackBy: trackBySlotId"
              class="slot-item car-slot"
              [class]="getSlotClass(slot)"
              [title]="getSlotTooltip(slot)"
              (click)="onSlotClick(slot)">
              
              <div class="slot-number">{{ slot.slot_number }}</div>
            </div>
          </div>
        </div>

        <!-- Bike Slots Section -->
        <div *ngIf="groupedSlots.bikeSlots.length > 0" class="slot-section">
          <div class="section-header">
            <h6 class="section-title">
              <i class="fas fa-motorcycle text-success me-2"></i>
              Bike Slots ({{ groupedSlots.bikeSlots.length }})
            </h6>
          </div>
          
          <div class="slot-grid bike-grid">
            <div 
              *ngFor="let slot of groupedSlots.bikeSlots; trackBy: trackBySlotId"
              class="slot-item bike-slot"
              [class]="getSlotClass(slot)"
              [title]="getSlotTooltip(slot)"
              (click)="onSlotClick(slot)">
              
              <div class="slot-number">{{ slot.slot_number }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Statistics Summary -->
      <div *ngIf="!loading && slots.length > 0" class="stats-summary mt-4">
        <div class="row g-3">
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-value">{{ slotStats.total }}</div>
              <div class="stat-label">Total Slots</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-value text-success">{{ slotStats.available }}</div>
              <div class="stat-label">Available</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-value text-danger">{{ slotStats.occupied }}</div>
              <div class="stat-label">Occupied</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-value text-primary">{{ slotStats.occupancyRate }}%</div>
              <div class="stat-label">Occupancy</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .slot-grid-container {
      background: #fff;
      border-radius: 12px;
      padding: 1.5rem;
      border: 1px solid #e9ecef;
    }

    .slot-grid-header {
      border-bottom: 1px solid #e9ecef;
      padding-bottom: 1rem;
      margin-bottom: 1.5rem;
    }

    .filters-section {
      background: #f8f9fa;
      padding: 1rem;
      border-radius: 8px;
      border: 1px solid #e9ecef;
    }

    .form-select-sm {
      font-size: 0.875rem;
    }

    .form-check-label {
      font-size: 0.875rem;
      color: #6c757d;
    }

    .slot-section {
      margin-bottom: 2rem;
    }

    .section-header {
      margin-bottom: 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 2px solid #e9ecef;
    }

    .section-title {
      margin: 0;
      font-weight: 600;
      color: #495057;
    }

    .slot-grid {
      display: grid;
      gap: 1rem;
      padding: 1rem;
      background: #f8f9fa;
      border-radius: 8px;
      border: 1px solid #e9ecef;
    }

    .car-grid {
      grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
    }

    .bike-grid {
      grid-template-columns: repeat(auto-fill, minmax(35px, 1fr));
    }

    .slot-item {
      position: relative;
      background: #fff;
      border: 2px solid #dee2e6;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s ease;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      height: 28px;
    }


    .slot-item:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .slot-number {
      font-weight: 700;
      font-size: 0.65rem;
      color: #495057;
      line-height: 1;
    }


    /* Slot Status Colors */
    .slot-available {
      border-color: #28a745;
      background-color: #f8fff9;
    }

    .slot-occupied {
      border-color: #dc3545;
      background-color: #fff5f5;
    }

    .slot-reserved {
      border-color: #ffc107;
      background-color: #fffdf5;
    }

    .slot-inactive {
      border-color: #6c757d;
      background-color: #f6f6f6;
      opacity: 0.6;
      cursor: not-allowed;
    }

    .slot-inactive:hover {
      transform: none;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .empty-state {
      background: #f8f9fa;
      border-radius: 8px;
      border: 2px dashed #dee2e6;
    }

    .stats-summary {
      background: #f8f9fa;
      padding: 1.5rem;
      border-radius: 8px;
      border: 1px solid #e9ecef;
    }

    .stat-card {
      text-align: center;
      padding: 1rem;
      background: #fff;
      border-radius: 8px;
      border: 1px solid #e9ecef;
    }

    .stat-value {
      font-size: 1.5rem;
      font-weight: 700;
      margin-bottom: 0.25rem;
    }

    .stat-label {
      font-size: 0.875rem;
      color: #6c757d;
      font-weight: 500;
    }

    @media (max-width: 768px) {
      .slot-grid-container {
        padding: 1rem;
      }

      .car-grid {
        grid-template-columns: repeat(auto-fill, minmax(35px, 1fr));
      }

      .bike-grid {
        grid-template-columns: repeat(auto-fill, minmax(30px, 1fr));
      }


      .slot-number {
        font-size: 0.55rem;
      }

      .stats-summary {
        padding: 1rem;
      }

      .stat-value {
        font-size: 1.25rem;
      }
    }
  `]
})
export class SlotGridComponent implements OnInit, OnChanges {
  @Input() lotId!: string;
  @Input() lotName?: string;
  @Input() autoRefreshEnabled: boolean = true;

  @Output() slotSelected = new EventEmitter<ParkingSlot>();
  @Output() addSlotsRequested = new EventEmitter<string>();
  @Output() slotsUpdated = new EventEmitter<ParkingSlot[]>();

  // Data
  slots: ParkingSlot[] = [];
  filteredSlots: ParkingSlot[] = [];
  groupedSlots: { carSlots: ParkingSlot[], bikeSlots: ParkingSlot[] } = { carSlots: [], bikeSlots: [] };
  slotStats = { total: 0, available: 0, occupied: 0, reserved: 0, inactive: 0, occupancyRate: 0 };

  // UI State
  loading = false;
  selectedVehicleType: string = '';
  selectedStatus: string = '';
  autoRefresh = false;
  lastUpdated?: Date;

  // Auto-refresh
  private autoRefreshInterval?: any;

  constructor(
    public slotService: ParkingSlotService,
    private toastService: ToastService
  ) {}

  ngOnInit(): void {
    if (this.lotId) {
      this.loadSlots();
      if (this.autoRefreshEnabled) {
        this.autoRefresh = true;
        this.toggleAutoRefresh();
      }
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['lotId'] && this.lotId) {
      this.loadSlots();
    }
  }

  ngOnDestroy(): void {
    this.clearAutoRefresh();
  }

  async loadSlots(): Promise<void> {
    if (!this.lotId) return;

    try {
      this.loading = true;
      const filters = {}; // Service now handles pagination automatically

      this.slots = await this.slotService.getLotSlots(this.lotId, filters);
      this.lastUpdated = new Date();
      this.applyFilters();
      this.slotsUpdated.emit(this.slots);
      
    } catch (error) {
      console.error('Error loading slots:', error);
      this.toastService.showError('Failed to load parking slots');
    } finally {
      this.loading = false;
    }
  }

  private applyFilters(): void {
    let filtered = [...this.slots];

    // Vehicle type filter
    if (this.selectedVehicleType) {
      filtered = filtered.filter(slot => slot.slot_type === this.selectedVehicleType);
    }

    // Status filter
    if (this.selectedStatus) {
      filtered = filtered.filter(slot => {
        const status = this.slotService.getSlotStatusText(slot).toLowerCase();
        return status === this.selectedStatus;
      });
    }

    this.filteredSlots = filtered;
    this.groupedSlots = this.slotService.groupSlotsByType(filtered);
    this.slotStats = this.slotService.calculateSlotStats(filtered);
  }

  onFilterChange(): void {
    this.applyFilters();
  }

  async refreshSlots(): Promise<void> {
    await this.loadSlots();
    this.toastService.showSuccess('Slots refreshed successfully');
  }

  toggleAutoRefresh(): void {
    if (this.autoRefresh) {
      this.autoRefreshInterval = setInterval(() => {
        this.loadSlots();
      }, 30000); // 30 seconds
    } else {
      this.clearAutoRefresh();
    }
  }

  private clearAutoRefresh(): void {
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval);
      this.autoRefreshInterval = undefined;
    }
  }

  onSlotClick(slot: ParkingSlot): void {
    if (slot.status === 'INACTIVE') return;
    this.slotSelected.emit(slot);
  }

  openAddSlotsModal(): void {
    this.addSlotsRequested.emit(this.lotId);
  }

  getSlotClass(slot: ParkingSlot): string {
    return this.slotService.getSlotStatusClass(slot);
  }

  getSlotTooltip(slot: ParkingSlot): string {
    const status = this.slotService.getSlotStatusText(slot);
    const type = slot.slot_type.charAt(0).toUpperCase() + slot.slot_type.slice(1);
    return `${slot.slot_number} - ${type} Slot - ${status}`;
  }

  formatTime(date: Date): string {
    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  trackBySlotId(index: number, slot: ParkingSlot): string {
    return slot.id;
  }
}
