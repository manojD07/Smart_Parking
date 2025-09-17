import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';

// Services
import { ParkingLotService, ParkingLot } from '../../../../core/services/parking-lot.service';
import { ParkingSlotService, ParkingSlot, AddSlotsData } from '../../../../core/services/parking-slot.service';
import { ToastService } from '../../../../core/services/toast.service';

// Components
import { SlotGridComponent } from './slot-grid.component';
import { ConfirmationModalComponent } from '../shared/confirmation-modal.component';

@Component({
  selector: 'app-slot-overview',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    ReactiveFormsModule,
    SlotGridComponent,
  ],
  template: `
    <div class="modal fade" id="slotOverviewModal" tabindex="-1" aria-labelledby="slotOverviewModalLabel">
      <div class="modal-dialog modal-fullscreen-lg-down modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="slotOverviewModalLabel">
              <i class="fas fa-th-large me-2"></i>
              Parking Slots - {{ selectedLot?.name }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          
          <div class="modal-body p-0">
            <app-slot-grid
              *ngIf="selectedLot"
              [lotId]="selectedLot.id"
              [lotName]="selectedLot.name"
              [autoRefreshEnabled]="true"
              (slotSelected)="onSlotSelected($event)"
              (addSlotsRequested)="onAddSlotsRequested($event)"
              (slotsUpdated)="onSlotsUpdated($event)">
            </app-slot-grid>
          </div>
          
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              <i class="fas fa-times me-2"></i>Close
            </button>
            <button type="button" class="btn btn-primary" (click)="openAddSlotsModal()">
              <i class="fas fa-plus me-2"></i>Add More Slots
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Slots Modal -->
    <div class="modal fade" id="addSlotsModal" tabindex="-1" aria-labelledby="addSlotsModalLabel">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="addSlotsModalLabel">
              <i class="fas fa-plus me-2"></i>
              Add Parking Slots
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          
          <form [formGroup]="addSlotsForm" (ngSubmit)="onAddSlots()">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label fw-semibold">Parking Lot</label>
                <div class="form-control-plaintext">{{ selectedLot?.name }}</div>
              </div>

              <div class="row">
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">
                      <i class="fas fa-car text-primary me-2"></i>
                      Car Slots
                    </label>
                    <input 
                      type="number" 
                      class="form-control" 
                      formControlName="car_slots"
                      placeholder="Number of car slots"
                      min="0"
                      max="100">
                    <div class="form-text">
                      Current: {{ currentLot?.total_car_slots || 0 }} car slots
                    </div>
                  </div>
                </div>
                
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">
                      <i class="fas fa-motorcycle text-success me-2"></i>
                      Bike Slots
                    </label>
                    <input 
                      type="number" 
                      class="form-control" 
                      formControlName="bike_slots"
                      placeholder="Number of bike slots"
                      min="0"
                      max="200">
                    <div class="form-text">
                      Current: {{ currentLot?.total_bike_slots || 0 }} bike slots
                    </div>
                  </div>
                </div>
              </div>

              <div class="alert alert-info" *ngIf="totalNewSlots > 0">
                <i class="fas fa-info-circle me-2"></i>
                <strong>{{ totalNewSlots }}</strong> new slots will be created
                <div class="small mt-1">
                  Slots will be automatically numbered (e.g., C001, B001)
                </div>
              </div>

              <div class="alert alert-warning" *ngIf="addSlotsForm.get('car_slots')?.value === 0 && addSlotsForm.get('bike_slots')?.value === 0">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Please specify at least one slot to add
              </div>
            </div>
            
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                Cancel
              </button>
              <button 
                type="submit" 
                class="btn btn-primary"
                [disabled]="addSlotsForm.invalid || totalNewSlots === 0 || addingSlots">
                <span *ngIf="addingSlots" class="spinner-border spinner-border-sm me-2" role="status">
                  <span class="visually-hidden">Adding...</span>
                </span>
                <i *ngIf="!addingSlots" class="fas fa-plus me-2"></i>
                Add {{ totalNewSlots }} Slot{{ totalNewSlots !== 1 ? 's' : '' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Slot Details Modal -->
    <div class="modal fade" id="slotDetailsModal" tabindex="-1" aria-labelledby="slotDetailsModalLabel">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="slotDetailsModalLabel">
              <i class="fas" [class]="selectedSlot ? getSlotIcon(selectedSlot.slot_type) : 'fa-info-circle'"></i>
              Slot Details - {{ selectedSlot?.slot_number }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          
          <div class="modal-body" *ngIf="selectedSlot">
            <div class="row">
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label fw-semibold">Slot Number</label>
                  <div class="form-control-plaintext">{{ selectedSlot.slot_number }}</div>
                </div>
                
                <div class="mb-3">
                  <label class="form-label fw-semibold">Vehicle Type</label>
                  <div class="form-control-plaintext">
                    <i class="fas" [class]="getSlotIcon(selectedSlot.slot_type)"></i>
                    {{ selectedSlot.slot_type.charAt(0).toUpperCase() + selectedSlot.slot_type.slice(1) }}
                  </div>
                </div>
                
                <div class="mb-3">
                  <label class="form-label fw-semibold">Status</label>
                  <div class="form-control-plaintext">
                    <span class="badge" [class]="getStatusBadgeClass(selectedSlot)">
                      {{ getSlotStatusText(selectedSlot) }}
                    </span>
                  </div>
                </div>
              </div>
              
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label fw-semibold">Occupied</label>
                  <div class="form-control-plaintext">
                    <i class="fas" [class]="selectedSlot.is_occupied ? 'fa-check text-success' : 'fa-times text-muted'"></i>
                    {{ selectedSlot.is_occupied ? 'Yes' : 'No' }}
                  </div>
                </div>
                
                <div class="mb-3">
                  <label class="form-label fw-semibold">Reserved</label>
                  <div class="form-control-plaintext">
                    <i class="fas" [class]="selectedSlot.is_reserved ? 'fa-check text-warning' : 'fa-times text-muted'"></i>
                    {{ selectedSlot.is_reserved ? 'Yes' : 'No' }}
                  </div>
                </div>
                
                <div class="mb-3">
                  <label class="form-label fw-semibold">Created</label>
                  <div class="form-control-plaintext">
                    {{ formatDate(selectedSlot.created_at) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              Close
            </button>
            <!-- Future: Add slot management actions here -->
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .modal-xl {
      max-width: 90vw;
    }

    .form-control-plaintext {
      padding: 0.375rem 0;
      margin-bottom: 0;
      background-color: transparent;
      border: none;
    }

    .badge {
      font-size: 0.75rem;
      padding: 0.375rem 0.75rem;
    }

    .alert {
      border-radius: 8px;
    }

    .btn {
      border-radius: 8px;
    }

    .modal-content {
      border-radius: 12px;
      border: none;
      box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }

    .modal-header {
      border-bottom: 1px solid #dee2e6;
    }

    .modal-footer {
      border-top: 1px solid #dee2e6;
    }

    @media (max-width: 768px) {
      .modal-xl {
        max-width: 100vw;
      }
    }
  `]
})
export class SlotOverviewComponent implements OnInit {
  @Input() selectedLot: ParkingLot | null = null;

  // Forms
  addSlotsForm: FormGroup;

  // UI State
  addingSlots = false;
  selectedSlot: ParkingSlot | null = null;
  currentSlots: ParkingSlot[] = [];

  constructor(
    private parkingLotService: ParkingLotService,
    private slotService: ParkingSlotService,
    private toastService: ToastService,
    private fb: FormBuilder
  ) {
    this.addSlotsForm = this.fb.group({
      car_slots: [0, [Validators.min(0), Validators.max(100)]],
      bike_slots: [0, [Validators.min(0), Validators.max(200)]]
    });
  }

  ngOnInit(): void {
    // Form is already initialized
  }

  get currentLot(): ParkingLot | null {
    return this.selectedLot;
  }

  get totalNewSlots(): number {
    const carSlots = this.addSlotsForm.get('car_slots')?.value || 0;
    const bikeSlots = this.addSlotsForm.get('bike_slots')?.value || 0;
    return carSlots + bikeSlots;
  }

  onSlotSelected(slot: ParkingSlot): void {
    this.selectedSlot = slot;
    const modalElement = document.getElementById('slotDetailsModal');
    if (modalElement) {
      const modal = new (window as any).bootstrap.Modal(modalElement);
      modal.show();
    }
  }

  onAddSlotsRequested(lotId: string): void {
    this.openAddSlotsModal();
  }

  onSlotsUpdated(slots: ParkingSlot[]): void {
    this.currentSlots = slots;
  }

  openAddSlotsModal(): void {
    this.addSlotsForm.reset({ car_slots: 0, bike_slots: 0 });
    const modalElement = document.getElementById('addSlotsModal');
    if (modalElement) {
      const modal = new (window as any).bootstrap.Modal(modalElement);
      modal.show();
    }
  }

  async onAddSlots(): Promise<void> {
    if (!this.selectedLot || this.addSlotsForm.invalid || this.totalNewSlots === 0) return;

    try {
      this.addingSlots = true;
      const formData = this.addSlotsForm.value;
      const addSlotsData: AddSlotsData = {
        car_slots: formData.car_slots || 0,
        bike_slots: formData.bike_slots || 0
      };

      const result = await this.slotService.addSlots(this.selectedLot.id, addSlotsData);
      
      if (result.success) {
        this.toastService.showSuccess(
          `Successfully added ${this.totalNewSlots} slot${this.totalNewSlots !== 1 ? 's' : ''} to ${this.selectedLot.name}`
        );
        
        // Close modal
        const modalElement = document.getElementById('addSlotsModal');
        if (modalElement) {
          const modal = (window as any).bootstrap.Modal.getInstance(modalElement);
          if (modal) modal.hide();
        }
        
        // Refresh slot grid (this will trigger via the slot grid's refresh)
        // The slot grid component will automatically refresh when slots are added
        
      } else {
        this.toastService.showError(result.error || 'Failed to add slots');
      }
      
    } catch (error) {
      console.error('Error adding slots:', error);
      this.toastService.showError('Failed to add slots');
    } finally {
      this.addingSlots = false;
    }
  }

  // Utility methods
  getSlotIcon(slotType: 'car' | 'bike'): string {
    return slotType === 'car' ? 'fa-car' : 'fa-motorcycle';
  }

  getSlotStatusText(slot: ParkingSlot): string {
    return this.slotService.getSlotStatusText(slot);
  }

  getStatusBadgeClass(slot: ParkingSlot): string {
    const status = this.slotService.getSlotStatusText(slot).toLowerCase();
    const classes: { [key: string]: string } = {
      'available': 'bg-success',
      'occupied': 'bg-danger',
      'reserved': 'bg-warning text-dark',
      'inactive': 'bg-secondary'
    };
    return classes[status] || 'bg-secondary';
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}
