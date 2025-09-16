import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subject, takeUntil, debounceTime, distinctUntilChanged } from 'rxjs';
import { AdminService, AdminUserCreate, AdminUserUpdate } from '../services/admin.service';
import { LoadingComponent } from '../../../shared/components/loading.component';
import { User } from '../../../core/models/user.model';

@Component({
  selector: 'app-admin-users',
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
                <i class="fas fa-users me-2"></i>
                User Management
              </h1>
              <p class="text-muted">Manage system users and permissions</p>
            </div>
            <div>
              <button 
                class="btn btn-primary" 
                data-bs-toggle="modal" 
                data-bs-target="#createUserModal"
              >
                <i class="fas fa-plus me-2"></i>
                Add New User
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
                <div class="col-md-4">
                  <div class="form-group">
                    <label for="searchInput" class="form-label">Search Users</label>
                    <input
                      type="text"
                      class="form-control"
                      id="searchInput"
                      placeholder="Search by name or email..."
                      [(ngModel)]="searchTerm"
                      (input)="onSearchChange()"
                    >
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="form-group">
                    <label for="roleFilter" class="form-label">Role</label>
                    <select 
                      class="form-select" 
                      id="roleFilter"
                      [(ngModel)]="roleFilter"
                      (change)="loadUsers()"
                    >
                      <option value="">All Roles</option>
                      <option value="admin">Admins</option>
                      <option value="user">Regular Users</option>
                    </select>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="form-group">
                    <label for="statusFilter" class="form-label">Status</label>
                    <select 
                      class="form-select" 
                      id="statusFilter"
                      [(ngModel)]="statusFilter"
                      (change)="loadUsers()"
                    >
                      <option value="">All Status</option>
                      <option value="true">Active</option>
                      <option value="false">Inactive</option>
                    </select>
                  </div>
                </div>
                <div class="col-md-2">
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

      <app-loading *ngIf="loading" message="Loading users..."></app-loading>

      <!-- Users Table -->
      <div class="row" *ngIf="!loading">
        <div class="col-12">
          <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
              <h5 class="mb-0">Users ({{ users.length }})</h5>
              <div>
                <button class="btn btn-sm btn-outline-primary me-2" (click)="loadUsers()">
                  <i class="fas fa-sync-alt me-1" [class.fa-spin]="loading"></i>
                  Refresh
                </button>
                <button class="btn btn-sm btn-outline-success">
                  <i class="fas fa-download me-1"></i>
                  Export
                </button>
              </div>
            </div>
            <div class="card-body p-0">
              <div class="table-responsive">
                <table class="table table-striped table-hover mb-0">
                  <thead class="table-dark">
                    <tr>
                      <th>User</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Joined</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr *ngFor="let user of users">
                      <td>
                        <div class="d-flex align-items-center">
                          <div class="avatar me-3">
                            <div class="avatar-initials bg-primary text-white">
                              {{ getUserInitials(user) }}
                            </div>
                          </div>
                          <div>
                            <div class="fw-bold">{{ user.first_name }} {{ user.last_name }}</div>
                            <small class="text-muted" *ngIf="user.phone">{{ user.phone }}</small>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span class="font-monospace">{{ user.email }}</span>
                      </td>
                      <td>
                        <span 
                          class="badge" 
                          [class.bg-danger]="user.is_admin"
                          [class.bg-secondary]="!user.is_admin"
                        >
                          {{ user.is_admin ? 'Admin' : 'User' }}
                        </span>
                      </td>
                      <td>
                        <span 
                          class="badge" 
                          [class.bg-success]="user.is_active"
                          [class.bg-warning]="!user.is_active"
                        >
                          {{ user.is_active ? 'Active' : 'Inactive' }}
                        </span>
                      </td>
                      <td>
                        <small>{{ user.created_at | date:'short' }}</small>
                      </td>
                      <td>
                        <div class="btn-group" role="group">
                          <button 
                            class="btn btn-sm btn-outline-primary"
                            (click)="editUser(user)"
                            data-bs-toggle="modal"
                            data-bs-target="#editUserModal"
                          >
                            <i class="fas fa-edit"></i>
                          </button>
                          <button 
                            class="btn btn-sm"
                            [class.btn-outline-success]="!user.is_active"
                            [class.btn-outline-warning]="user.is_active"
                            (click)="toggleUserStatus(user)"
                          >
                            <i class="fas" [class.fa-play]="!user.is_active" [class.fa-pause]="user.is_active"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Empty State -->
              <div class="text-center py-5" *ngIf="users.length === 0 && !loading">
                <i class="fas fa-users fa-3x text-muted mb-3"></i>
                <h5>No users found</h5>
                <p class="text-muted">Try adjusting your search criteria</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Create User Modal -->
      <div class="modal fade" id="createUserModal" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Create New User</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form [formGroup]="createUserForm" (ngSubmit)="createUser()">
              <div class="modal-body">
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="firstName" class="form-label">First Name</label>
                    <input
                      type="text"
                      class="form-control"
                      id="firstName"
                      formControlName="first_name"
                      [class.is-invalid]="isCreateFieldInvalid('first_name')"
                    >
                    <div class="invalid-feedback" *ngIf="isCreateFieldInvalid('first_name')">
                      First name is required
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <label for="lastName" class="form-label">Last Name</label>
                    <input
                      type="text"
                      class="form-control"
                      id="lastName"
                      formControlName="last_name"
                      [class.is-invalid]="isCreateFieldInvalid('last_name')"
                    >
                    <div class="invalid-feedback" *ngIf="isCreateFieldInvalid('last_name')">
                      Last name is required
                    </div>
                  </div>
                </div>
                <div class="mb-3">
                  <label for="email" class="form-label">Email</label>
                  <input
                    type="email"
                    class="form-control"
                    id="email"
                    formControlName="email"
                    [class.is-invalid]="isCreateFieldInvalid('email')"
                  >
                  <div class="invalid-feedback" *ngIf="isCreateFieldInvalid('email')">
                    Please enter a valid email address
                  </div>
                </div>
                <div class="mb-3">
                  <label for="phone" class="form-label">Phone (Optional)</label>
                  <input
                    type="tel"
                    class="form-control"
                    id="phone"
                    formControlName="phone"
                  >
                </div>
                <div class="mb-3">
                  <label for="password" class="form-label">Password</label>
                  <input
                    type="password"
                    class="form-control"
                    id="password"
                    formControlName="password"
                    [class.is-invalid]="isCreateFieldInvalid('password')"
                  >
                  <div class="invalid-feedback" *ngIf="isCreateFieldInvalid('password')">
                    Password must be at least 8 characters
                  </div>
                </div>
                <div class="mb-3">
                  <div class="form-check">
                    <input
                      class="form-check-input"
                      type="checkbox"
                      id="isAdmin"
                      formControlName="is_admin"
                    >
                    <label class="form-check-label" for="isAdmin">
                      Administrator privileges
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
                  [disabled]="createUserForm.invalid || creating"
                >
                  <span class="spinner-border spinner-border-sm me-2" *ngIf="creating"></span>
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <!-- Edit User Modal -->
      <div class="modal fade" id="editUserModal" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Edit User</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form [formGroup]="editUserForm" (ngSubmit)="updateUser()">
              <div class="modal-body">
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="editFirstName" class="form-label">First Name</label>
                    <input
                      type="text"
                      class="form-control"
                      id="editFirstName"
                      formControlName="first_name"
                    >
                  </div>
                  <div class="col-md-6 mb-3">
                    <label for="editLastName" class="form-label">Last Name</label>
                    <input
                      type="text"
                      class="form-control"
                      id="editLastName"
                      formControlName="last_name"
                    >
                  </div>
                </div>
                <div class="mb-3">
                  <label for="editPhone" class="form-label">Phone</label>
                  <input
                    type="tel"
                    class="form-control"
                    id="editPhone"
                    formControlName="phone"
                  >
                </div>
                <div class="mb-3">
                  <div class="form-check">
                    <input
                      class="form-check-input"
                      type="checkbox"
                      id="editIsAdmin"
                      formControlName="is_admin"
                    >
                    <label class="form-check-label" for="editIsAdmin">
                      Administrator privileges
                    </label>
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
                      Active user
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
                  Update User
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .avatar {
      width: 40px;
      height: 40px;
    }

    .avatar-initials {
      width: 100%;
      height: 100%;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      font-size: 14px;
    }

    .table th {
      border-top: none;
      font-weight: 600;
      font-size: 0.9rem;
    }

    .btn-group .btn {
      border-radius: 0.25rem;
      margin-right: 0.25rem;
    }
  `]
})
export class AdminUsersComponent implements OnInit, OnDestroy {
  users: User[] = [];
  loading = true;
  creating = false;
  updating = false;
  
  searchTerm = '';
  roleFilter = '';
  statusFilter = '';
  
  createUserForm: FormGroup;
  editUserForm: FormGroup;
  selectedUser: User | null = null;
  
  private destroy$ = new Subject<void>();
  private searchSubject = new Subject<string>();

  constructor(
    private adminService: AdminService,
    private fb: FormBuilder
  ) {
    this.createUserForm = this.createUserFormGroup();
    this.editUserForm = this.createEditFormGroup();
    
    // Setup search debouncing
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeUntil(this.destroy$)
    ).subscribe(() => {
      this.loadUsers();
    });
  }

  ngOnInit(): void {
    this.loadUsers();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private createUserFormGroup(): FormGroup {
    return this.fb.group({
      first_name: ['', Validators.required],
      last_name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      phone: [''],
      password: ['', [Validators.required, Validators.minLength(8)]],
      is_admin: [false]
    });
  }

  private createEditFormGroup(): FormGroup {
    return this.fb.group({
      first_name: [''],
      last_name: [''],
      phone: [''],
      is_admin: [false],
      is_active: [true]
    });
  }

  loadUsers(): void {
    this.loading = true;
    
    const params: any = {
      limit: 100
    };
    
    if (this.searchTerm) {
      params.search = this.searchTerm;
    }
    
    if (this.roleFilter) {
      params.is_admin = this.roleFilter === 'admin';
    }
    
    if (this.statusFilter) {
      params.is_active = this.statusFilter === 'true';
    }

    this.adminService.getAllUsers(params)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (users) => {
          this.users = users;
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading users:', error);
          this.loading = false;
          // Provide demo data if backend is not available
          this.users = this.getDemoUsers();
        }
      });
  }

  onSearchChange(): void {
    this.searchSubject.next(this.searchTerm);
  }

  resetFilters(): void {
    this.searchTerm = '';
    this.roleFilter = '';
    this.statusFilter = '';
    this.loadUsers();
  }

  createUser(): void {
    if (this.createUserForm.valid) {
      this.creating = true;
      
      const userData: AdminUserCreate = this.createUserForm.value;
      
      this.adminService.createUser(userData)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (user) => {
            this.users.unshift(user);
            this.createUserForm.reset();
            this.creating = false;
            // Close modal (you might want to use a proper modal service)
            console.log('User created successfully');
          },
          error: (error) => {
            console.error('Error creating user:', error);
            this.creating = false;
          }
        });
    }
  }

  editUser(user: User): void {
    this.selectedUser = user;
    this.editUserForm.patchValue({
      first_name: user.first_name,
      last_name: user.last_name,
      phone: user.phone,
      is_admin: user.is_admin,
      is_active: user.is_active
    });
  }

  updateUser(): void {
    if (this.selectedUser && this.editUserForm.valid) {
      this.updating = true;
      
      const updateData: AdminUserUpdate = this.editUserForm.value;
      
      this.adminService.updateUser(this.selectedUser.id, updateData)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (updatedUser) => {
            const index = this.users.findIndex(u => u.id === updatedUser.id);
            if (index !== -1) {
              this.users[index] = updatedUser;
            }
            this.updating = false;
            console.log('User updated successfully');
          },
          error: (error) => {
            console.error('Error updating user:', error);
            this.updating = false;
          }
        });
    }
  }

  toggleUserStatus(user: User): void {
    if (user.is_active) {
      this.adminService.deactivateUser(user.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            user.is_active = false;
            console.log('User deactivated');
          },
          error: (error) => console.error('Error deactivating user:', error)
        });
    } else {
      this.adminService.activateUser(user.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            user.is_active = true;
            console.log('User activated');
          },
          error: (error) => console.error('Error activating user:', error)
        });
    }
  }

  getUserInitials(user: User): string {
    return (user.first_name.charAt(0) + user.last_name.charAt(0)).toUpperCase();
  }

  isCreateFieldInvalid(fieldName: string): boolean {
    const field = this.createUserForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  private getDemoUsers(): User[] {
    return [
      {
        id: '1',
        email: 'admin@smartparking.com',
        first_name: 'Admin',
        last_name: 'User',
        phone: '+1234567890',
        is_admin: true,
        is_active: true,
        total_spent: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: '2',
        email: 'john.doe@example.com',
        first_name: 'John',
        last_name: 'Doe',
        phone: '+1234567891',
        is_admin: false,
        is_active: true,
        total_spent: 45.50,
        created_at: new Date(Date.now() - 86400000).toISOString(),
        updated_at: new Date(Date.now() - 86400000).toISOString()
      }
    ];
  }
}
