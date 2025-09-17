import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil, debounceTime, distinctUntilChanged } from 'rxjs/operators';

// Components
import { ParkingLotCardComponent } from './parking-lot-card.component';
import { ParkingLotFormComponent } from './parking-lot-form.component';
import { LoadingStateComponent } from '../shared/loading-state.component';
import { ConfirmationModalComponent } from '../shared/confirmation-modal.component';

// Services
import { ParkingLotService, ParkingLot, CreateLotData, UpdateLotData, LotStatistics } from '../../../../core/services/parking-lot.service';
import { ToastService } from '../../../../core/services/toast.service';

interface PaginationInfo {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

@Component({
  selector: 'app-parking-lot-list',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    ReactiveFormsModule,
    ParkingLotCardComponent,
    ParkingLotFormComponent,
    LoadingStateComponent,
    ConfirmationModalComponent
  ],
  template: `
    <div class="container-fluid p-4">
      <!-- Header -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 class="mb-1">Parking Lot Management</h2>
          <p class="text-muted mb-0">Manage parking lots, capacity, and pricing</p>
        </div>
        <div class="d-flex gap-2">
          <button class="btn btn-outline-primary" (click)="refreshLots()">
            <i class="fas fa-sync-alt me-2"></i>Refresh
          </button>
          <button class="btn btn-primary" (click)="openCreateModal()">
            <i class="fas fa-plus me-2"></i>Add New Lot
          </button>
        </div>
      </div>

      <!-- Statistics Cards -->
      <div class="row mb-4" *ngIf="statistics">
        <div class="col-lg-3 col-md-6 mb-3">
          <div class="card border-0 shadow-sm">
            <div class="card-body">
              <div class="d-flex align-items-center">
                <div class="flex-shrink-0">
                  <div class="bg-primary bg-gradient rounded-3 p-3">
                    <i class="fas fa-building text-white fa-lg"></i>
                  </div>
                </div>
                <div class="flex-grow-1 ms-3">
                  <div class="text-muted small">Total Lots</div>
                  <div class="fs-4 fw-bold">{{ statistics.total_lots }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-lg-3 col-md-6 mb-3">
          <div class="card border-0 shadow-sm">
            <div class="card-body">
              <div class="d-flex align-items-center">
                <div class="flex-shrink-0">
                  <div class="bg-success bg-gradient rounded-3 p-3">
                    <i class="fas fa-check-circle text-white fa-lg"></i>
                  </div>
                </div>
                <div class="flex-grow-1 ms-3">
                  <div class="text-muted small">Active Lots</div>
                  <div class="fs-4 fw-bold">{{ statistics.active_lots }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-lg-3 col-md-6 mb-3">
          <div class="card border-0 shadow-sm">
            <div class="card-body">
              <div class="d-flex align-items-center">
                <div class="flex-shrink-0">
                  <div class="bg-warning bg-gradient rounded-3 p-3">
                    <i class="fas fa-pause-circle text-white fa-lg"></i>
                  </div>
                </div>
                <div class="flex-grow-1 ms-3">
                  <div class="text-muted small">Inactive Lots</div>
                  <div class="fs-4 fw-bold">{{ statistics.inactive_lots }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-lg-3 col-md-6 mb-3">
          <div class="card border-0 shadow-sm">
            <div class="card-body">
              <div class="d-flex align-items-center">
                <div class="flex-shrink-0">
                  <div class="bg-info bg-gradient rounded-3 p-3">
                    <i class="fas fa-th-large text-white fa-lg"></i>
                  </div>
                </div>
                <div class="flex-grow-1 ms-3">
                  <div class="text-muted small">Total Capacity</div>
                  <div class="fs-4 fw-bold">{{ statistics.total_capacity }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Search and Filters -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-body">
          <form [formGroup]="filterForm" class="row g-3">
            <div class="col-md-6">
              <label class="form-label">Search Lots</label>
              <div class="input-group">
                <span class="input-group-text">
                  <i class="fas fa-search"></i>
                </span>
                <input 
                  type="text" 
                  class="form-control" 
                  formControlName="search"
                  placeholder="Search by name or address..."
                >
                <button 
                  class="btn btn-outline-secondary" 
                  type="button"
                  *ngIf="filterForm.get('search')?.value"
                  (click)="clearSearch()">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>
            <div class="col-md-3">
              <label class="form-label">Status Filter</label>
              <select class="form-select" formControlName="statusFilter">
                <option value="">All Status</option>
                <option value="true">Active Only</option>
                <option value="false">Inactive Only</option>
              </select>
            </div>
            <div class="col-md-3">
              <label class="form-label">Sort By</label>
              <select class="form-select" formControlName="sortBy">
                <option value="name">Name</option>
                <option value="created_at">Created Date</option>
                <option value="capacity">Total Capacity</option>
                <option value="status">Status</option>
              </select>
            </div>
          </form>
        </div>
      </div>

      <!-- Parking Lots List -->
      <div class="card border-0 shadow-sm">
        <!-- Loading State -->
        <div *ngIf="loading">
          <app-loading-state 
            type="table" 
            loadingText="Loading parking lots..."
            [itemCount]="10"
            [tableHeaders]="['Name', 'Address', 'Capacity', 'Rates', 'Status', 'Actions']">
          </app-loading-state>
        </div>

        <!-- Empty State -->
        <div *ngIf="!loading && paginatedLots.length === 0" class="card-body text-center py-5">
          <div class="text-muted">
            <i class="fas fa-building fa-3x mb-3 d-block opacity-25"></i>
            <h5 *ngIf="!hasSearchFilters">No Parking Lots Found</h5>
            <h5 *ngIf="hasSearchFilters">No Matching Lots Found</h5>
            <p *ngIf="!hasSearchFilters">Create your first parking lot to get started</p>
            <p *ngIf="hasSearchFilters">Try adjusting your search criteria</p>
            <button 
              *ngIf="!hasSearchFilters" 
              class="btn btn-primary mt-3"
              (click)="openCreateModal()">
              <i class="fas fa-plus me-2"></i>Create First Lot
            </button>
            <button 
              *ngIf="hasSearchFilters" 
              class="btn btn-outline-primary mt-3"
              (click)="clearAllFilters()">
              <i class="fas fa-times me-2"></i>Clear Filters
            </button>
          </div>
        </div>

        <!-- Parking Lots Table -->
        <div *ngIf="!loading && paginatedLots.length > 0" class="table-responsive" style="overflow-y: visible;">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th>Parking Lot</th>
                <th>Location</th>
                <th>Capacity</th>
                <th>Hourly Rates</th>
                <th>Status</th>
                <th>Created</th>
                <th class="text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let lot of paginatedLots; trackBy: trackByLotId" [class.table-warning]="!lot.is_active">
                <!-- Parking Lot Name & Info -->
                <td>
                  <div class="d-flex align-items-center">
                    <div class="lot-icon me-3">
                      <i class="fas fa-building text-primary"></i>
                    </div>
                    <div>
                      <div class="fw-semibold">{{ lot.name }}</div>
                      <div class="text-muted small">ID: {{ lot.id.substring(0, 8) }}...</div>
                    </div>
                  </div>
                </td>

                <!-- Location -->
                <td>
                  <div class="location-info">
                    <div class="text-truncate" style="max-width: 200px;" [title]="lot.address">
                      <i class="fas fa-map-marker-alt text-muted me-1"></i>
                      {{ lot.address }}
                    </div>
                    <div class="text-muted small">
                      {{ lot.latitude }}, {{ lot.longitude }}
                    </div>
                  </div>
                </td>

                <!-- Capacity -->
                <td>
                  <div class="capacity-info">
                    <div class="d-flex align-items-center mb-1">
                      <i class="fas fa-car text-primary me-1"></i>
                      <span class="me-2">{{ lot.total_car_slots }}</span>
                      <i class="fas fa-motorcycle text-success me-1"></i>
                      <span>{{ lot.total_bike_slots }}</span>
                    </div>
                    <div class="text-muted small">
                      Total: {{ lot.total_car_slots + lot.total_bike_slots }} slots
                    </div>
                  </div>
                </td>

                <!-- Hourly Rates -->
                <td>
                  <div class="rates-info">
                    <div class="small">
                      <div class="d-flex justify-content-between">
                        <span class="text-muted">Car:</span>
                        <span class="fw-semibold text-success">₹{{ lot.hourly_rate_car }}/hr</span>
                      </div>
                      <div class="d-flex justify-content-between">
                        <span class="text-muted">Bike:</span>
                        <span class="fw-semibold text-success">₹{{ lot.hourly_rate_bike }}/hr</span>
                      </div>
                    </div>
                  </div>
                </td>

                <!-- Status -->
                <td>
                  <span class="badge" [class]="lot.is_active ? 'bg-success' : 'bg-danger'">
                    <i class="fas" [class]="lot.is_active ? 'fa-check-circle' : 'fa-times-circle'"></i>
                    {{ lot.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>

                <!-- Created Date -->
                <td>
                  <div class="text-muted small">
                    {{ formatDate(lot.created_at) }}
                  </div>
                </td>

                <!-- Actions -->
                <td class="text-center">
                  <div class="btn-group btn-group-sm" role="group">
                    <button 
                      type="button" 
                      class="btn btn-outline-primary"
                      (click)="onViewSlots(lot)"
                      [title]="'View slots for ' + lot.name">
                      <i class="fas fa-th-large"></i>
                    </button>
                    
                    <div class="btn-group btn-group-sm" role="group">
                      <button 
                        class="btn btn-outline-secondary dropdown-toggle dropdown-toggle-split" 
                        type="button" 
                        [id]="'lotActions' + lot.id" 
                        data-bs-toggle="dropdown"
                        data-bs-auto-close="true"
                        aria-expanded="false"
                        [title]="'More actions for ' + lot.name">
                        <i class="fas fa-ellipsis-v"></i>
                      </button>
                      <ul class="dropdown-menu dropdown-menu-end" [attr.aria-labelledby]="'lotActions' + lot.id">
                        <li>
                          <a class="dropdown-item" href="#" (click)="onEditLot(lot); $event.preventDefault()">
                            <i class="fas fa-edit me-2"></i>Edit Details
                          </a>
                        </li>
                        <li>
                          <a class="dropdown-item" href="#" (click)="onToggleStatus(lot); $event.preventDefault()">
                            <i class="fas" [class]="lot.is_active ? 'fa-ban' : 'fa-check'"></i>
                            {{ lot.is_active ? 'Deactivate' : 'Activate' }}
                          </a>
                        </li>
                        <li><hr class="dropdown-divider"></li>
                        <li>
                          <a class="dropdown-item text-danger" href="#" (click)="onDeleteLot(lot); $event.preventDefault()">
                            <i class="fas fa-trash me-2"></i>Delete Lot
                          </a>
                        </li>
                      </ul>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination -->
      <div class="d-flex justify-content-between align-items-center mt-4" *ngIf="pagination.totalItems > 0">
        <div class="text-muted">
          Showing {{ ((pagination.currentPage - 1) * pagination.pageSize) + 1 }} to 
          {{ Math.min(pagination.currentPage * pagination.pageSize, pagination.totalItems) }} of 
          {{ pagination.totalItems }} lots
        </div>
        <nav>
          <ul class="pagination mb-0">
            <li class="page-item" [class.disabled]="pagination.currentPage === 1">
              <a class="page-link" href="#" (click)="changePage(pagination.currentPage - 1); $event.preventDefault()">
                <i class="fas fa-chevron-left"></i>
              </a>
            </li>
            <li class="page-item" 
                *ngFor="let page of getPageNumbers()" 
                [class.active]="page === pagination.currentPage">
              <a class="page-link" href="#" (click)="changePage(page); $event.preventDefault()">
                {{ page }}
              </a>
            </li>
            <li class="page-item" [class.disabled]="pagination.currentPage === pagination.totalPages">
              <a class="page-link" href="#" (click)="changePage(pagination.currentPage + 1); $event.preventDefault()">
                <i class="fas fa-chevron-right"></i>
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- Create/Edit Lot Modal -->
    <app-parking-lot-form
      modalId="lotFormModal"
      [lot]="selectedLot"
      [processing]="formProcessing"
      (save)="onSaveLot($event)"
      (cancel)="onCancelForm()">
    </app-parking-lot-form>

    <!-- Confirmation Modals -->
    <app-confirmation-modal
      modalId="deleteLotModal"
      title="Delete Parking Lot"
      [message]="deleteConfirmationMessage"
      details="This action cannot be undone. All associated slots and bookings will also be deleted."
      type="danger"
      confirmText="Delete Lot"
      [processing]="deleteProcessing"
      icon="fa-trash"
      confirmIcon="fa-trash"
      (confirmed)="confirmDeleteLot()">
    </app-confirmation-modal>

    <app-confirmation-modal
      modalId="toggleStatusModal"
      [title]="statusToggleTitle"
      [message]="statusToggleMessage"
      [type]="statusToggleType"
      [confirmText]="statusToggleConfirmText"
      [processing]="statusToggleProcessing"
      [icon]="statusToggleIcon"
      [confirmIcon]="statusToggleIcon"
      (confirmed)="confirmToggleStatus()">
    </app-confirmation-modal>
  `,
  styles: [`
    .card {
      border-radius: 12px;
    }

    .btn {
      border-radius: 8px;
    }

    .form-control, .form-select {
      border-radius: 8px;
    }

    .input-group-text {
      background-color: #f8f9fa;
      border: 1px solid #ced4da;
    }

    .pagination .page-link {
      border-radius: 8px;
      margin: 0 2px;
      border: 1px solid #dee2e6;
    }

    .pagination .page-item.active .page-link {
      background-color: #0d6efd;
      border-color: #0d6efd;
    }

    .bg-gradient {
      background: linear-gradient(135deg, var(--bs-bg-opacity, 1), rgba(255,255,255,0.1)) !important;
    }

    .opacity-25 {
      opacity: 0.25;
    }

    .lot-icon {
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #f8f9fa;
      border-radius: 8px;
    }

    .table th {
      border-top: none;
      font-weight: 600;
      font-size: 0.875rem;
      color: #6c757d;
      white-space: nowrap;
    }

    .table td {
      vertical-align: middle;
      padding: 1rem 0.75rem;
    }

    .table-hover tbody tr:hover {
      background-color: #f8f9fa;
    }

    .table-warning {
      --bs-table-bg: #fff3cd;
      --bs-table-striped-bg: #ffecb5;
      --bs-table-striped-color: #000;
      --bs-table-active-bg: #ffdf9e;
      --bs-table-active-color: #000;
      --bs-table-hover-bg: #ffe69c;
      --bs-table-hover-color: #000;
      color: #664d03;
    }

    .badge {
      font-size: 0.75rem;
      padding: 0.375rem 0.75rem;
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
    }

    .btn-group-sm .btn {
      padding: 0.25rem 0.5rem;
      font-size: 0.75rem;
    }

    .dropdown-toggle-split {
      padding-left: 0.375rem;
      padding-right: 0.375rem;
    }

    .dropdown-toggle-split::after {
      margin-left: 0;
    }

    .dropdown-menu {
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      border: 1px solid #e5e7eb;
      font-size: 0.875rem;
      z-index: 1050;
      position: absolute;
    }

    .table-responsive {
      overflow-x: auto;
      overflow-y: visible;
      padding-bottom: 120px;
      margin-bottom: -120px;
    }

    .btn-group {
      position: static;
    }

    .dropdown-item {
      padding: 0.5rem 1rem;
    }

    .dropdown-item:hover {
      background-color: #f3f4f6;
    }

    .dropdown-item.text-danger:hover {
      background-color: #fef2f2;
      color: #dc2626 !important;
    }

    @media (max-width: 768px) {
      .d-flex.justify-content-between {
        flex-direction: column;
        gap: 1rem;
      }

      .pagination {
        justify-content: center;
      }

      .table-responsive {
        font-size: 0.875rem;
      }

      .location-info .text-truncate {
        max-width: 150px !important;
      }

      .capacity-info,
      .rates-info {
        font-size: 0.8rem;
      }

      .btn-group-sm .btn {
        padding: 0.2rem 0.4rem;
        font-size: 0.7rem;
      }
    }
  `]
})
export class ParkingLotListComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  // Data
  allLots: ParkingLot[] = [];
  filteredLots: ParkingLot[] = [];
  paginatedLots: ParkingLot[] = [];
  statistics: LotStatistics | null = null;

  // UI State
  loading = false;
  formProcessing = false;
  deleteProcessing = false;
  statusToggleProcessing = false;

  // Forms
  filterForm: FormGroup;

  // Pagination
  pagination: PaginationInfo = {
    currentPage: 1,
    pageSize: 20,
    totalItems: 0,
    totalPages: 0
  };

  // Modals
  selectedLot: ParkingLot | null = null;
  lotToDelete: ParkingLot | null = null;
  lotToToggle: ParkingLot | null = null;

  // Math for template
  Math = Math;

  constructor(
    private parkingLotService: ParkingLotService,
    private toastService: ToastService,
    private fb: FormBuilder
  ) {
    this.filterForm = this.fb.group({
      search: [''],
      statusFilter: [''],
      sortBy: ['name']
    });
  }

  ngOnInit(): void {
    this.setupFilterSubscription();
    this.loadLots();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private setupFilterSubscription(): void {
    this.filterForm.valueChanges
      .pipe(
        takeUntil(this.destroy$),
        debounceTime(300),
        distinctUntilChanged()
      )
      .subscribe(() => {
        this.applyFilters();
      });
  }

  async loadLots(): Promise<void> {
    try {
      this.loading = true;
      
      // Load lots and statistics in parallel
      const [lots, stats] = await Promise.all([
        this.parkingLotService.getAllLots(),
        this.parkingLotService.getLotStatistics()
      ]);
      
      this.allLots = lots;
      this.statistics = stats;
      this.applyFilters();
      
    } catch (error) {
      console.error('Error loading parking lots:', error);
      this.toastService.showError('Failed to load parking lots');
    } finally {
      this.loading = false;
    }
  }

  private applyFilters(): void {
    const filters = this.filterForm.value;
    let filtered = [...this.allLots];

    // Search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(lot =>
        lot.name.toLowerCase().includes(searchTerm) ||
        lot.address.toLowerCase().includes(searchTerm)
      );
    }

    // Status filter
    if (filters.statusFilter !== '') {
      const isActive = filters.statusFilter === 'true';
      filtered = filtered.filter(lot => lot.is_active === isActive);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (filters.sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'created_at':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'capacity':
          const aCapacity = a.total_car_slots + a.total_bike_slots;
          const bCapacity = b.total_car_slots + b.total_bike_slots;
          return bCapacity - aCapacity;
        case 'status':
          return (b.is_active ? 1 : 0) - (a.is_active ? 1 : 0);
        default:
          return 0;
      }
    });

    this.filteredLots = filtered;
    this.pagination.totalItems = filtered.length;
    this.pagination.totalPages = Math.ceil(filtered.length / this.pagination.pageSize);
    this.pagination.currentPage = 1;
    this.updatePagination();
  }

  private updatePagination(): void {
    const startIndex = (this.pagination.currentPage - 1) * this.pagination.pageSize;
    const endIndex = startIndex + this.pagination.pageSize;
    this.paginatedLots = this.filteredLots.slice(startIndex, endIndex);
  }

  // Pagination methods
  changePage(page: number): void {
    if (page >= 1 && page <= this.pagination.totalPages) {
      this.pagination.currentPage = page;
      this.updatePagination();
    }
  }

  getPageNumbers(): number[] {
    const pages = [];
    const maxPages = 5;
    let startPage = Math.max(1, this.pagination.currentPage - Math.floor(maxPages / 2));
    let endPage = Math.min(this.pagination.totalPages, startPage + maxPages - 1);
    
    if (endPage - startPage < maxPages - 1) {
      startPage = Math.max(1, endPage - maxPages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    return pages;
  }

  // Filter methods
  get hasSearchFilters(): boolean {
    const filters = this.filterForm.value;
    return filters.search || filters.statusFilter !== '';
  }

  clearSearch(): void {
    this.filterForm.patchValue({ search: '' });
  }

  clearAllFilters(): void {
    this.filterForm.reset();
    this.filterForm.patchValue({
      search: '',
      statusFilter: '',
      sortBy: 'name'
    });
  }

  async refreshLots(): Promise<void> {
    await this.loadLots();
    this.toastService.showSuccess('Parking lots refreshed');
  }

  // CRUD Operations
  openCreateModal(): void {
    this.selectedLot = null;
    const modalElement = document.getElementById('lotFormModal');
    if (modalElement) {
      const modal = new (window as any).bootstrap.Modal(modalElement);
      modal.show();
    }
  }

  async onSaveLot(lotData: CreateLotData | UpdateLotData): Promise<void> {
    try {
      this.formProcessing = true;
      
      if (this.selectedLot) {
        // Update existing lot
        await this.parkingLotService.updateLot(this.selectedLot.id, lotData as UpdateLotData);
        this.toastService.showSuccess('Parking lot updated successfully');
      } else {
        // Create new lot
        await this.parkingLotService.createLot(lotData as CreateLotData);
        this.toastService.showSuccess('Parking lot created successfully');
      }
      
      // Close modal
      const modalElement = document.getElementById('lotFormModal');
      if (modalElement) {
        const modal = (window as any).bootstrap.Modal.getInstance(modalElement);
        if (modal) modal.hide();
      }
      
      await this.loadLots();
      
    } catch (error) {
      console.error('Error saving parking lot:', error);
      this.toastService.showError('Failed to save parking lot');
    } finally {
      this.formProcessing = false;
    }
  }

  onCancelForm(): void {
    this.selectedLot = null;
  }

  onEditLot(lot: ParkingLot): void {
    this.selectedLot = lot;
    const modalElement = document.getElementById('lotFormModal');
    if (modalElement) {
      const modal = new (window as any).bootstrap.Modal(modalElement);
      modal.show();
    }
  }

  onDeleteLot(lot: ParkingLot): void {
    this.lotToDelete = lot;
    const modalElement = document.getElementById('deleteLotModal');
    if (modalElement) {
      const modal = new (window as any).bootstrap.Modal(modalElement);
      modal.show();
    }
  }

  async confirmDeleteLot(): Promise<void> {
    if (!this.lotToDelete) return;

    try {
      this.deleteProcessing = true;
      await this.parkingLotService.deleteLot(this.lotToDelete.id);
      
      this.toastService.showSuccess('Parking lot deleted successfully');
      
      // Close modal
      const modalElement = document.getElementById('deleteLotModal');
      if (modalElement) {
        const modal = (window as any).bootstrap.Modal.getInstance(modalElement);
        if (modal) modal.hide();
      }
      
      await this.loadLots();
      
    } catch (error) {
      console.error('Error deleting parking lot:', error);
      this.toastService.showError('Failed to delete parking lot');
    } finally {
      this.deleteProcessing = false;
      this.lotToDelete = null;
    }
  }

  onToggleStatus(lot: ParkingLot): void {
    this.lotToToggle = lot;
    const modalElement = document.getElementById('toggleStatusModal');
    if (modalElement) {
      const modal = new (window as any).bootstrap.Modal(modalElement);
      modal.show();
    }
  }

  async confirmToggleStatus(): Promise<void> {
    if (!this.lotToToggle) return;

    try {
      this.statusToggleProcessing = true;
      const newStatus = !this.lotToToggle.is_active;
      
      await this.parkingLotService.toggleLotStatus(this.lotToToggle.id, newStatus);
      
      this.toastService.showSuccess(
        `Parking lot ${newStatus ? 'activated' : 'deactivated'} successfully`
      );
      
      // Close modal
      const modalElement = document.getElementById('toggleStatusModal');
      if (modalElement) {
        const modal = (window as any).bootstrap.Modal.getInstance(modalElement);
        if (modal) modal.hide();
      }
      
      await this.loadLots();
      
    } catch (error) {
      console.error('Error toggling lot status:', error);
      this.toastService.showError('Failed to update lot status');
    } finally {
      this.statusToggleProcessing = false;
      this.lotToToggle = null;
    }
  }

  // Event handlers
  onViewSlots(lot: ParkingLot): void {
    // This will be implemented in Phase 2
    this.toastService.showInfo(`Viewing slots for ${lot.name} - Coming in Phase 2`);
  }

  trackByLotId(index: number, lot: ParkingLot): string {
    return lot.id;
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  // Computed properties for confirmation modals
  get deleteConfirmationMessage(): string {
    return this.lotToDelete ? 
      `Are you sure you want to delete "${this.lotToDelete.name}"?` : 
      'Are you sure you want to delete this parking lot?';
  }

  get statusToggleTitle(): string {
    return this.lotToToggle?.is_active ? 'Deactivate Parking Lot' : 'Activate Parking Lot';
  }

  get statusToggleMessage(): string {
    if (!this.lotToToggle) return '';
    const action = this.lotToToggle.is_active ? 'deactivate' : 'activate';
    return `Are you sure you want to ${action} "${this.lotToToggle.name}"?`;
  }

  get statusToggleType(): 'danger' | 'warning' | 'info' | 'primary' {
    return this.lotToToggle?.is_active ? 'warning' : 'primary';
  }

  get statusToggleConfirmText(): string {
    return this.lotToToggle?.is_active ? 'Deactivate' : 'Activate';
  }

  get statusToggleIcon(): string {
    return this.lotToToggle?.is_active ? 'fa-ban' : 'fa-check';
  }
}
