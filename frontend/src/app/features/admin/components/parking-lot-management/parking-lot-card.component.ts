import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatusBadgeComponent } from '../shared/status-badge.component';
import { ParkingLot } from '../../../../core/services/parking-lot.service';

@Component({
  selector: 'app-parking-lot-card',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  template: `
    <div class="card parking-lot-card h-100" [class.inactive]="!lot.is_active">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h6 class="card-title mb-0 fw-bold">{{ lot.name }}</h6>
        <app-status-badge 
          [status]="lot.is_active ? 'active' : 'inactive'"
          [text]="lot.is_active ? 'Active' : 'Inactive'"
          [icon]="lot.is_active ? 'fa-check-circle' : 'fa-times-circle'">
        </app-status-badge>
      </div>

      <div class="card-body">
        <!-- Address -->
        <div class="mb-3">
          <div class="text-muted small mb-1">
            <i class="fas fa-map-marker-alt me-1"></i>Location
          </div>
          <div class="text-truncate" [title]="lot.address">{{ lot.address }}</div>
        </div>

        <!-- Capacity Info -->
        <div class="row mb-3">
          <div class="col-6">
            <div class="capacity-item">
              <div class="capacity-icon car-icon">
                <i class="fas fa-car"></i>
              </div>
              <div>
                <div class="capacity-number">{{ lot.total_car_slots }}</div>
                <div class="capacity-label">Car Slots</div>
              </div>
            </div>
          </div>
          <div class="col-6">
            <div class="capacity-item">
              <div class="capacity-icon bike-icon">
                <i class="fas fa-motorcycle"></i>
              </div>
              <div>
                <div class="capacity-number">{{ lot.total_bike_slots }}</div>
                <div class="capacity-label">Bike Slots</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Pricing Info -->
        <div class="pricing-section mb-3">
          <div class="text-muted small mb-2">
            <i class="fas fa-dollar-sign me-1"></i>Hourly Rates
          </div>
          <div class="row">
            <div class="col-6">
              <div class="pricing-item">
                <span class="pricing-vehicle">Car:</span>
                <span class="pricing-rate">$ {{ lot.hourly_rate_car }}/hr</span>
              </div>
            </div>
            <div class="col-6">
              <div class="pricing-item">
                <span class="pricing-vehicle">Bike:</span>
                <span class="pricing-rate">$ {{ lot.hourly_rate_bike }}/hr</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Total Capacity -->
        <div class="total-capacity">
          <div class="text-muted small">Total Capacity</div>
          <div class="fw-bold text-primary">{{ totalCapacity }} Slots</div>
        </div>
      </div>

      <div class="card-footer bg-transparent">
        <div class="d-flex flex-wrap gap-2">
          <button 
            type="button" 
            class="btn btn-outline-primary btn-sm flex-fill"
            (click)="onViewSlots()"
            [title]="'View slots for ' + lot.name">
            <i class="fas fa-th-large me-1"></i>
            Slots
          </button>
          
          <div class="dropdown">
            <button 
              class="btn btn-outline-secondary btn-sm dropdown-toggle" 
              type="button" 
              [id]="'lotActions' + lot.id" 
              data-bs-toggle="dropdown"
              [title]="'Actions for ' + lot.name">
              <i class="fas fa-ellipsis-v"></i>
            </button>
            <ul class="dropdown-menu" [attr.aria-labelledby]="'lotActions' + lot.id">
              <li>
                <a class="dropdown-item" href="#" (click)="onEdit(); $event.preventDefault()">
                  <i class="fas fa-edit me-2"></i>Edit Details
                </a>
              </li>
              <li>
                <a class="dropdown-item" href="#" (click)="onToggleStatus(); $event.preventDefault()">
                  <i class="fas" [class]="lot.is_active ? 'fa-ban' : 'fa-check'" ></i>
                  {{ lot.is_active ? 'Deactivate' : 'Activate' }}
                </a>
              </li>
              <li><hr class="dropdown-divider"></li>
              <li>
                <a class="dropdown-item text-danger" href="#" (click)="onDelete(); $event.preventDefault()">
                  <i class="fas fa-trash me-2"></i>Delete Lot
                </a>
              </li>
            </ul>
          </div>
        </div>

        <!-- Created Date -->
        <div class="text-muted small mt-2">
          <i class="fas fa-calendar me-1"></i>
          Created: {{ formatDate(lot.created_at) }}
        </div>
      </div>
    </div>
  `,
  styles: [`
    .parking-lot-card {
      border: 1px solid #e9ecef;
      border-radius: 12px;
      transition: all 0.2s ease;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .parking-lot-card:hover {
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      transform: translateY(-2px);
    }

    .parking-lot-card.inactive {
      opacity: 0.7;
      background-color: #f8f9fa;
    }

    .card-header {
      background-color: #fff;
      border-bottom: 1px solid #e9ecef;
      padding: 1rem;
    }

    .card-title {
      color: #2d3748;
      font-size: 1rem;
    }

    .capacity-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .capacity-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.875rem;
    }

    .car-icon {
      background-color: #dbeafe;
      color: #1e40af;
    }

    .bike-icon {
      background-color: #dcfce7;
      color: #166534;
    }

    .capacity-number {
      font-weight: 600;
      font-size: 1.1rem;
      line-height: 1;
    }

    .capacity-label {
      font-size: 0.75rem;
      color: #6b7280;
      line-height: 1;
    }

    .pricing-section {
      background-color: #f8fafc;
      padding: 0.75rem;
      border-radius: 8px;
    }

    .pricing-item {
      display: flex;
      justify-content: space-between;
      font-size: 0.875rem;
    }

    .pricing-vehicle {
      color: #6b7280;
    }

    .pricing-rate {
      font-weight: 600;
      color: #059669;
    }

    .total-capacity {
      text-align: center;
      padding: 0.5rem;
      background-color: #f0f9ff;
      border-radius: 8px;
    }

    .card-footer {
      padding: 1rem;
      border-top: 1px solid #e9ecef;
    }

    .btn {
      border-radius: 6px;
      font-size: 0.875rem;
      font-weight: 500;
    }

    .btn-sm {
      padding: 0.375rem 0.75rem;
    }

    .dropdown-toggle::after {
      display: none;
    }

    .dropdown-menu {
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      border: 1px solid #e5e7eb;
    }

    .dropdown-item {
      padding: 0.5rem 1rem;
      font-size: 0.875rem;
    }

    .dropdown-item:hover {
      background-color: #f3f4f6;
    }

    .dropdown-item.text-danger:hover {
      background-color: #fef2f2;
      color: #dc2626 !important;
    }

    @media (max-width: 768px) {
      .card-footer .d-flex {
        flex-direction: column;
      }
      
      .btn {
        justify-content: center;
      }
    }
  `]
})
export class ParkingLotCardComponent {
  @Input() lot!: ParkingLot;

  @Output() viewSlots = new EventEmitter<ParkingLot>();
  @Output() edit = new EventEmitter<ParkingLot>();
  @Output() delete = new EventEmitter<ParkingLot>();
  @Output() toggleStatus = new EventEmitter<ParkingLot>();

  get totalCapacity(): number {
    return this.lot.total_car_slots + this.lot.total_bike_slots;
  }

  onViewSlots(): void {
    this.viewSlots.emit(this.lot);
  }

  onEdit(): void {
    this.edit.emit(this.lot);
  }

  onDelete(): void {
    this.delete.emit(this.lot);
  }

  onToggleStatus(): void {
    this.toggleStatus.emit(this.lot);
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
}
