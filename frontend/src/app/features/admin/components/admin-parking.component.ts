import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subject, takeUntil, debounceTime, distinctUntilChanged } from 'rxjs';
import { AdminService } from '../services/admin.service';
import { LoadingComponent } from '../../../shared/components/loading.component';
import { ParkingLot } from '../../../core/models/parking.model';

@Component({
  selector: 'app-admin-parking',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, LoadingComponent],
  template: `
    <div class="container-fluid mt-4">
      <!-- Header -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h1 class="h2 mb-1">
                <i class="fas fa-parking me-2"></i>
                Parking Management
              </h1>
              <p class="text-muted">Manage parking lots and slots</p>
            </div>
            <div>
              <button 
                class="btn btn-primary" 
                data-bs-toggle="modal" 
                data-bs-target="#createLotModal"
              >
                <i class="fas fa-plus me-2"></i>
                Add New Lot
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="card">
            <div class="card-body">
              <div class="row">
                <div class="col-md-6">
                  <div class="form-group">
                    <label for="searchInput" class="form-label">Search Parking Lots</label>
                    <input
                      type="text"
                      class="form-control"
                      id="searchInput"
                      placeholder="Search by name or address..."
                      [(ngModel)]="searchTerm"
                      (input)="onSearchChange()"
                    >
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="form-group">
                    <label for="statusFilter" class="form-label">Status</label>
                    <select 
                      class="form-select" 
                      id="statusFilter"
                      [(ngModel)]="statusFilter"
                      (change)="loadParkingLots()"
                    >
                      <option value="">All Status</option>
                      <option value="true">Active</option>
                      <option value="false">Inactive</option>
                    </select>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="form-group">
                    <label class="form-label">&nbsp;</label>
                    <button class="btn btn-outline-secondary w-100" (click)="resetFilters()">
                      <i class="fas fa-undo me-1"></i>
                      Reset
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <app-loading *ngIf="loading" message="Loading parking lots..."></app-loading>

      <!-- Parking Lots Grid -->
      <div class="row" *ngIf="!loading">
        <div class="col-lg-6 col-xl-4 mb-4" *ngFor="let lot of parkingLots">
          <div class="card h-100">
            <div class="card-header d-flex justify-content-between align-items-center">
              <h6 class="mb-0">{{ lot.name }}</h6>
              <span 
                class="badge" 
                [class.bg-success]="lot.is_active"
                [class.bg-secondary]="!lot.is_active"
              >
                {{ lot.is_active ? 'Active' : 'Inactive' }}
              </span>
            </div>
            <div class="card-body">
              <p class="text-muted small mb-3">
                <i class="fas fa-map-marker-alt me-1"></i>
                {{ lot.address }}
              </p>
              
              <div class="row mb-3">
                <div class="col-6">
                  <div class="text-center">
                    <h5 class="text-primary mb-0">{{ lot.total_car_slots }}</h5>
                    <small class="text-muted">Car Slots</small>
                  </div>
                </div>
                <div class="col-6">
                  <div class="text-center">
                    <h5 class="text-success mb-0">{{ lot.total_bike_slots }}</h5>
                    <small class="text-muted">Bike Slots</small>
                  </div>
                </div>
              </div>

              <div class="row mb-3">
                <div class="col-6">
                  <div class="text-center">
                    <h6 class="text-warning mb-0">\${{ lot.hourly_rate_car }}</h6>
                    <small class="text-muted">Car Rate/hr</small>
                  </div>
                </div>
                <div class="col-6">
                  <div class="text-center">
                    <h6 class="text-info mb-0">\${{ lot.hourly_rate_bike }}</h6>
                    <small class="text-muted">Bike Rate/hr</small>
                  </div>
                </div>
              </div>

              <!-- Occupancy Progress (Demo) -->
              <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <small class="text-muted">Current Occupancy</small>
                  <small class="text-muted">{{ getOccupancyRate(lot) }}%</small>
                </div>
                <div class="progress" style="height: 6px;">
                  <div
                    class="progress-bar"
                    [class.bg-success]="getOccupancyRate(lot) < 70"
                    [class.bg-warning]="getOccupancyRate(lot) >= 70 && getOccupancyRate(lot) < 90"
                    [class.bg-danger]="getOccupancyRate(lot) >= 90"
                    [style.width.%]="getOccupancyRate(lot)"
                  ></div>
                </div>
              </div>
            </div>
            <div class="card-footer">
              <div class="btn-group w-100" role="group">
                <button 
                  class="btn btn-outline-primary btn-sm"
                  (click)="editLot(lot)"
                  data-bs-toggle="modal"
                  data-bs-target="#editLotModal"
                >
                  <i class="fas fa-edit me-1"></i>
                  Edit
                </button>
                <button 
                  class="btn btn-outline-info btn-sm"
                  (click)="viewLotDetails(lot)"
                >
                  <i class="fas fa-eye me-1"></i>
                  View
                </button>
                <button 
                  class="btn btn-sm"
                  [class.btn-outline-success]="!lot.is_active"
                  [class.btn-outline-warning]="lot.is_active"
                  (click)="toggleLotStatus(lot)"
                >
                  <i class="fas" [class.fa-play]="!lot.is_active" [class.fa-pause]="lot.is_active"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div class="col-12" *ngIf="parkingLots.length === 0 && !loading">
          <div class="card">
            <div class="card-body text-center py-5">
              <i class="fas fa-parking fa-3x text-muted mb-3"></i>
              <h5>No parking lots found</h5>
              <p class="text-muted">Try adjusting your search criteria or create a new parking lot</p>
              <button 
                class="btn btn-primary" 
                data-bs-toggle="modal" 
                data-bs-target="#createLotModal"
              >
                <i class="fas fa-plus me-2"></i>
                Create First Lot
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Create Lot Modal -->
      <div class="modal fade" id="createLotModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Create New Parking Lot</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form [formGroup]="createLotForm" (ngSubmit)="createLot()">
              <div class="modal-body">
                <div class="row">
                  <div class="col-md-12 mb-3">
                    <label for="lotName" class="form-label">Lot Name</label>
                    <input
                      type="text"
                      class="form-control"
                      id="lotName"
                      formControlName="name"
                      [class.is-invalid]="isCreateFieldInvalid('name')"
                    >
                    <div class="invalid-feedback" *ngIf="isCreateFieldInvalid('name')">
                      Lot name is required
                    </div>
                  </div>
                </div>
                
                <div class="mb-3">
                  <label for="lotAddress" class="form-label">Address</label>
                  <textarea
                    class="form-control"
                    id="lotAddress"
                    rows="2"
                    formControlName="address"
                    [class.is-invalid]="isCreateFieldInvalid('address')"
                  ></textarea>
                  <div class="invalid-feedback" *ngIf="isCreateFieldInvalid('address')">
                    Address is required
                  </div>
                </div>

                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="latitude" class="form-label">Latitude</label>
                    <input
                      type="number"
                      step="any"
                      class="form-control"
                      id="latitude"
                      formControlName="latitude"
                      [class.is-invalid]="isCreateFieldInvalid('latitude')"
                    >
                    <div class="invalid-feedback" *ngIf="isCreateFieldInvalid('latitude')">
                      Valid latitude is required
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <label for="longitude" class="form-label">Longitude</label>
                    <input
                      type="number"
                      step="any"
                      class="form-control"
                      id="longitude"
                      formControlName="longitude"
                      [class.is-invalid]="isCreateFieldInvalid('longitude')"
                    >
                    <div class="invalid-feedback" *ngIf="isCreateFieldInvalid('longitude')">
                      Valid longitude is required
                    </div>
                  </div>
                </div>

                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="carSlots" class="form-label">Car Slots</label>
                    <input
                      type="number"
                      class="form-control"
                      id="carSlots"
                      formControlName="total_car_slots"
                      [class.is-invalid]="isCreateFieldInvalid('total_car_slots')"
                    >
                    <div class="invalid-feedback" *ngIf="isCreateFieldInvalid('total_car_slots')">
                      Number of car slots is required
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <label for="bikeSlots" class="form-label">Bike Slots</label>
                    <input
                      type="number"
                      class="form-control"
                      id="bikeSlots"
                      formControlName="total_bike_slots"
                      [class.is-invalid]="isCreateFieldInvalid('total_bike_slots')"
                    >
                    <div class="invalid-feedback" *ngIf="isCreateFieldInvalid('total_bike_slots')">
                      Number of bike slots is required
                    </div>
                  </div>
                </div>

                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="carRate" class="form-label">Car Hourly Rate (\$)</label>
                    <input
                      type="number"
                      step="0.01"
                      class="form-control"
                      id="carRate"
                      formControlName="hourly_rate_car"
                      [class.is-invalid]="isCreateFieldInvalid('hourly_rate_car')"
                    >
                    <div class="invalid-feedback" *ngIf="isCreateFieldInvalid('hourly_rate_car')">
                      Car hourly rate is required
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <label for="bikeRate" class="form-label">Bike Hourly Rate (\$)</label>
                    <input
                      type="number"
                      step="0.01"
                      class="form-control"
                      id="bikeRate"
                      formControlName="hourly_rate_bike"
                      [class.is-invalid]="isCreateFieldInvalid('hourly_rate_bike')"
                    >
                    <div class="invalid-feedback" *ngIf="isCreateFieldInvalid('hourly_rate_bike')">
                      Bike hourly rate is required
                    </div>
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                  Cancel
                </button>
                <button 
                  type="submit" 
                  class="btn btn-primary"
                  [disabled]="createLotForm.invalid || creating"
                >
                  <span class="spinner-border spinner-border-sm me-2" *ngIf="creating"></span>
                  Create Lot
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <!-- Edit Lot Modal -->
      <div class="modal fade" id="editLotModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Edit Parking Lot</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form [formGroup]="editLotForm" (ngSubmit)="updateLot()">
              <div class="modal-body">
                <!-- Similar form fields as create, but with edit form -->
                <div class="row">
                  <div class="col-md-12 mb-3">
                    <label for="editLotName" class="form-label">Lot Name</label>
                    <input
                      type="text"
                      class="form-control"
                      id="editLotName"
                      formControlName="name"
                    >
                  </div>
                </div>
                
                <div class="mb-3">
                  <label for="editLotAddress" class="form-label">Address</label>
                  <textarea
                    class="form-control"
                    id="editLotAddress"
                    rows="2"
                    formControlName="address"
                  ></textarea>
                </div>

                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="editCarSlots" class="form-label">Car Slots</label>
                    <input
                      type="number"
                      class="form-control"
                      id="editCarSlots"
                      formControlName="total_car_slots"
                    >
                  </div>
                  <div class="col-md-6 mb-3">
                    <label for="editBikeSlots" class="form-label">Bike Slots</label>
                    <input
                      type="number"
                      class="form-control"
                      id="editBikeSlots"
                      formControlName="total_bike_slots"
                    >
                  </div>
                </div>

                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="editCarRate" class="form-label">Car Hourly Rate (\$)</label>
                    <input
                      type="number"
                      step="0.01"
                      class="form-control"
                      id="editCarRate"
                      formControlName="hourly_rate_car"
                    >
                  </div>
                  <div class="col-md-6 mb-3">
                    <label for="editBikeRate" class="form-label">Bike Hourly Rate (\$)</label>
                    <input
                      type="number"
                      step="0.01"
                      class="form-control"
                      id="editBikeRate"
                      formControlName="hourly_rate_bike"
                    >
                  </div>
                </div>

                <div class="mb-3">
                  <div class="form-check">
                    <input
                      class="form-check-input"
                      type="checkbox"
                      id="editIsActive"
                      formControlName="is_active"
                    >
                    <label class="form-check-label" for="editIsActive">
                      Active parking lot
                    </label>
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                  Cancel
                </button>
                <button 
                  type="submit" 
                  class="btn btn-primary"
                  [disabled]="updating"
                >
                  <span class="spinner-border spinner-border-sm me-2" *ngIf="updating"></span>
                  Update Lot
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .progress {
      background-color: #e9ecef;
    }

    .card {
      box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
      border: 1px solid #e3e6f0;
    }

    .btn-group .btn {
      flex: 1;
    }
  `]
})
export class AdminParkingComponent implements OnInit, OnDestroy {
  parkingLots: ParkingLot[] = [];
  loading = true;
  creating = false;
  updating = false;
  
  searchTerm = '';
  statusFilter = '';
  
  createLotForm: FormGroup;
  editLotForm: FormGroup;
  selectedLot: ParkingLot | null = null;
  
  private destroy$ = new Subject<void>();
  private searchSubject = new Subject<string>();

  constructor(
    private adminService: AdminService,
    private fb: FormBuilder
  ) {
    this.createLotForm = this.createLotFormGroup();
    this.editLotForm = this.createEditFormGroup();
    
    // Setup search debouncing
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeUntil(this.destroy$)
    ).subscribe(() => {
      this.loadParkingLots();
    });
  }

  ngOnInit(): void {
    this.loadParkingLots();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private createLotFormGroup(): FormGroup {
    return this.fb.group({
      name: ['', Validators.required],
      address: ['', Validators.required],
      latitude: ['', [Validators.required, Validators.min(-90), Validators.max(90)]],
      longitude: ['', [Validators.required, Validators.min(-180), Validators.max(180)]],
      total_car_slots: ['', [Validators.required, Validators.min(1)]],
      total_bike_slots: ['', [Validators.required, Validators.min(1)]],
      hourly_rate_car: ['', [Validators.required, Validators.min(0)]],
      hourly_rate_bike: ['', [Validators.required, Validators.min(0)]]
    });
  }

  private createEditFormGroup(): FormGroup {
    return this.fb.group({
      name: [''],
      address: [''],
      total_car_slots: [''],
      total_bike_slots: [''],
      hourly_rate_car: [''],
      hourly_rate_bike: [''],
      is_active: [true]
    });
  }

  loadParkingLots(): void {
    this.loading = true;
    
    const params: any = {
      limit: 100
    };
    
    if (this.searchTerm) {
      params.search = this.searchTerm;
    }
    
    if (this.statusFilter) {
      params.is_active = this.statusFilter === 'true';
    }

    this.adminService.getAllParkingLots(params)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (lots) => {
          this.parkingLots = lots;
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading parking lots:', error);
          this.loading = false;
          // Provide demo data if backend is not available
          this.parkingLots = this.getDemoLots();
        }
      });
  }

  onSearchChange(): void {
    this.searchSubject.next(this.searchTerm);
  }

  resetFilters(): void {
    this.searchTerm = '';
    this.statusFilter = '';
    this.loadParkingLots();
  }

  createLot(): void {
    if (this.createLotForm.valid) {
      this.creating = true;
      
      const lotData = this.createLotForm.value;
      
      this.adminService.createParkingLot(lotData)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (lot) => {
            this.parkingLots.unshift(lot);
            this.createLotForm.reset();
            this.creating = false;
            console.log('Parking lot created successfully');
          },
          error: (error) => {
            console.error('Error creating parking lot:', error);
            this.creating = false;
          }
        });
    }
  }

  editLot(lot: ParkingLot): void {
    this.selectedLot = lot;
    this.editLotForm.patchValue({
      name: lot.name,
      address: lot.address,
      total_car_slots: lot.total_car_slots,
      total_bike_slots: lot.total_bike_slots,
      hourly_rate_car: lot.hourly_rate_car,
      hourly_rate_bike: lot.hourly_rate_bike,
      is_active: lot.is_active
    });
  }

  updateLot(): void {
    if (this.selectedLot && this.editLotForm.valid) {
      this.updating = true;
      
      const updateData = this.editLotForm.value;
      
      this.adminService.updateParkingLot(this.selectedLot.id, updateData)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (updatedLot) => {
            const index = this.parkingLots.findIndex(l => l.id === updatedLot.id);
            if (index !== -1) {
              this.parkingLots[index] = updatedLot;
            }
            this.updating = false;
            console.log('Parking lot updated successfully');
          },
          error: (error) => {
            console.error('Error updating parking lot:', error);
            this.updating = false;
          }
        });
    }
  }

  toggleLotStatus(lot: ParkingLot): void {
    if (lot.is_active) {
      this.adminService.deactivateParkingLot(lot.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            lot.is_active = false;
            console.log('Parking lot deactivated');
          },
          error: (error) => console.error('Error deactivating lot:', error)
        });
    } else {
      this.adminService.activateParkingLot(lot.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            lot.is_active = true;
            console.log('Parking lot activated');
          },
          error: (error) => console.error('Error activating lot:', error)
        });
    }
  }

  viewLotDetails(lot: ParkingLot): void {
    // Navigate to detailed view or open details modal
    console.log('Viewing details for lot:', lot.name);
  }

  getOccupancyRate(lot: ParkingLot): number {
    // Demo calculation - in real app this would come from the API
    return Math.floor(Math.random() * 90) + 10;
  }

  isCreateFieldInvalid(fieldName: string): boolean {
    const field = this.createLotForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  private getDemoLots(): ParkingLot[] {
    return [
      {
        id: '1',
        name: 'Downtown Plaza Parking',
        address: '123 Main Street, Downtown, NY 10001',
        latitude: 40.7128,
        longitude: -74.0060,
        total_car_slots: 150,
        total_bike_slots: 75,
        hourly_rate_car: 8.00,
        hourly_rate_bike: 3.00,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: '2',
        name: 'Airport Long-Term Parking',
        address: '456 Airport Drive, Queens, NY 11430',
        latitude: 40.6413,
        longitude: -73.7781,
        total_car_slots: 300,
        total_bike_slots: 50,
        hourly_rate_car: 12.00,
        hourly_rate_bike: 4.00,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ];
  }
}
