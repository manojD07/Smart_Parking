import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// Services
import { UserService, User, UserFilters } from '../../../core/services/user.service';
import { UserAdminService } from '../../../core/services/user-admin.service';
import { ToastService } from '../../../core/services/toast.service';
import { AuthService } from '../../auth/services/auth.service';
import { AdminService } from '../services/admin.service';

// Components
import { LoadingStateComponent } from './shared/loading-state.component';
import { AdminToggleComponent } from './users/admin-actions/admin-toggle.component';
import { AdminBadgeComponent } from './users/shared/admin-badge.component';

@Component({
  selector: 'app-admin-users',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingStateComponent, AdminToggleComponent, AdminBadgeComponent],
  template: `
    <div class="container-fluid mt-4">
      <!-- Header -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h2>
                <i class="fas fa-users me-2"></i>
                User Management
              </h2>
              <p class="text-muted mb-0">Manage user accounts, roles, and permissions</p>
            </div>
            <div class="d-flex gap-2">
              <button 
                class="btn btn-outline-primary btn-sm"
                (click)="refreshUsers()"
                [disabled]="loading">
                <i class="fas fa-sync-alt me-1" [class.fa-spin]="loading"></i>
                Refresh
              </button>
              <button class="btn btn-primary">
                <i class="fas fa-user-plus me-2"></i>
                Add User
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="row mb-4" *ngIf="!loading && userStats">
        <div class="col-md-3 mb-3">
          <div class="card bg-primary text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ dashboardData?.overview?.total_users || userStats.total || users.length }}</h4>
                  <small>Total Users</small>
                </div>
                <i class="fas fa-users fa-2x opacity-75"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div class="col-md-3 mb-3">
          <div class="card bg-success text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ userStats.active }}</h4>
                  <small>Active Users</small>
                </div>
                <i class="fas fa-user-check fa-2x opacity-75"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div class="col-md-3 mb-3">
          <div class="card bg-warning text-dark">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ userStats.admins }}</h4>
                  <small>Admin Users</small>
                </div>
                <i class="fas fa-crown fa-2x opacity-75"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div class="col-md-3 mb-3">
          <div class="card bg-info text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ userStats.inactive }}</h4>
                  <small>Inactive Users</small>
                </div>
                <i class="fas fa-user-times fa-2x opacity-75"></i>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading && users.length === 0" class="row">
        <div class="col-12">
          <app-loading-state 
            type="spinner" 
            loadingText="Loading users..."
            size="lg">
          </app-loading-state>
        </div>
      </div>

      <!-- User Table Placeholder -->
      <div *ngIf="!loading" class="row">
        <div class="col-12">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-table me-2"></i>
                Users ({{ totalUsers || users.length }})
              </h5>
            </div>
            
            <!-- Filters -->
            <div class="card-body border-bottom">
              <div class="row g-3">
                <div class="col-md-4">
                  <label class="form-label">Search Users</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    placeholder="Search by name or email..."
                    [(ngModel)]="filters.search"
                    (input)="onFilterChange()">
                </div>
                <div class="col-md-3">
                  <label class="form-label">User Status</label>
                  <select class="form-select" [(ngModel)]="filters.is_active" (change)="onFilterChange()">
                    <option [ngValue]="undefined">All Users</option>
                    <option [ngValue]="true">Active Users</option>
                    <option [ngValue]="false">Inactive Users</option>
                  </select>
                </div>
                <div class="col-md-3">
                  <label class="form-label">User Role</label>
                  <select class="form-select" [(ngModel)]="filters.is_admin" (change)="onFilterChange()">
                    <option [ngValue]="undefined">All Roles</option>
                    <option [ngValue]="true">Admins</option>
                    <option [ngValue]="false">Regular Users</option>
                  </select>
                </div>
                <div class="col-md-2">
                  <label class="form-label">Per Page</label>
                  <select class="form-select" [(ngModel)]="itemsPerPage" (change)="onItemsPerPageChange()">
                    <option value="10">10</option>
                    <option value="20">20</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                  </select>
                </div>
              </div>
              <div class="row mt-3">
                <div class="col-12">
                  <button class="btn btn-outline-secondary btn-sm me-2" (click)="clearFilters()">
                    <i class="fas fa-times me-1"></i>Clear Filters
                  </button>
                  <small class="text-muted">
                    Showing {{ users.length }} of {{ totalUsers || users.length }} users
                  </small>
                </div>
              </div>
            </div>
            
            <div class="card-body">
              <div class="table-responsive">
                <table class="table table-hover">
                  <thead>
                    <tr>
                      <th (click)="onSort('first_name')" class="sortable">
                        User
                        <i class="fas fa-sort ms-1" [class.fa-sort-up]="sortBy === 'first_name' && sortOrder === 'asc'" [class.fa-sort-down]="sortBy === 'first_name' && sortOrder === 'desc'"></i>
                      </th>
                      <th (click)="onSort('email')" class="sortable">
                        Email
                        <i class="fas fa-sort ms-1" [class.fa-sort-up]="sortBy === 'email' && sortOrder === 'asc'" [class.fa-sort-down]="sortBy === 'email' && sortOrder === 'desc'"></i>
                      </th>
                      <th (click)="onSort('is_active')" class="sortable">
                        Status
                        <i class="fas fa-sort ms-1" [class.fa-sort-up]="sortBy === 'is_active' && sortOrder === 'asc'" [class.fa-sort-down]="sortBy === 'is_active' && sortOrder === 'desc'"></i>
                      </th>
                      <th (click)="onSort('is_admin')" class="sortable">
                        Role
                        <i class="fas fa-sort ms-1" [class.fa-sort-up]="sortBy === 'is_admin' && sortOrder === 'asc'" [class.fa-sort-down]="sortBy === 'is_admin' && sortOrder === 'desc'"></i>
                      </th>
                      <th (click)="onSort('created_at')" class="sortable">
                        Joined
                        <i class="fas fa-sort ms-1" [class.fa-sort-up]="sortBy === 'created_at' && sortOrder === 'asc'" [class.fa-sort-down]="sortBy === 'created_at' && sortOrder === 'desc'"></i>
                      </th>
                      <th>Spent</th>
                      <th>Admin Actions</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr *ngFor="let user of users; trackBy: trackByUserId">
                      <td>
                        <div class="d-flex align-items-center">
                          <i class="fas fa-user-circle fa-lg text-muted me-2"></i>
                          <div>
                            <div class="fw-semibold">{{ formatUserName(user) }}</div>
                            <small class="text-muted" *ngIf="user.phone">{{ user.phone }}</small>
                          </div>
                        </div>
                      </td>
                      <td>{{ user.email }}</td>
                      <td>
                        <span [class]="formatUserStatus(user).class">
                          {{ formatUserStatus(user).text }}
                        </span>
                      </td>
                      <td>
                        <app-admin-badge 
                          [user]="user" 
                          size="sm" 
                          [showAdminIndicator]="true">
                        </app-admin-badge>
                      </td>
                      <td>{{ formatDate(user.created_at) }}</td>
                      <td>
                        <span class="fw-semibold text-success">{{ formatCurrency(user.total_spent) }}</span>
                      </td>
                      <td>
                        <app-admin-toggle
                          [user]="user"
                          [currentUser]="currentUser"
                          [allUsers]="users"
                          (adminToggled)="onAdminToggled($event)">
                        </app-admin-toggle>
                      </td>
                      <td>
                        <div class="btn-group btn-group-sm">
                          <button class="btn btn-outline-primary" (click)="viewUser(user)">
                            <i class="fas fa-eye"></i>
                          </button>
                          <button class="btn btn-outline-secondary" (click)="editUser(user)">
                            <i class="fas fa-edit"></i>
                          </button>
                          <button 
                            class="btn"
                            [class.btn-outline-success]="!user.is_active"
                            [class.btn-outline-danger]="user.is_active"
                            (click)="toggleUserStatus(user)">
                            <i class="fas" 
                               [class.fa-check]="!user.is_active"
                               [class.fa-times]="user.is_active"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                    <tr *ngIf="users.length === 0">
                      <td colspan="8" class="text-center py-4">
                        <i class="fas fa-users fa-2x text-muted mb-2"></i>
                        <div>No users found</div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <!-- Pagination -->
              <div class="d-flex justify-content-between align-items-center mt-3" *ngIf="totalUsers > itemsPerPage">
                <div>
                  <small class="text-muted">
                    Showing {{ (currentPage - 1) * itemsPerPage + 1 }} to {{ Math.min(currentPage * itemsPerPage, totalUsers) }} of {{ totalUsers }} users
                  </small>
                </div>
                <nav>
                  <ul class="pagination pagination-sm mb-0">
                    <li class="page-item" [class.disabled]="currentPage === 1">
                      <button class="page-link" (click)="onPageChange(1)" [disabled]="currentPage === 1">
                        <i class="fas fa-angle-double-left"></i>
                      </button>
                    </li>
                    <li class="page-item" [class.disabled]="currentPage === 1">
                      <button class="page-link" (click)="onPageChange(currentPage - 1)" [disabled]="currentPage === 1">
                        <i class="fas fa-angle-left"></i>
                      </button>
                    </li>
                    <li class="page-item" *ngFor="let page of getPagesArray()" [class.active]="page === currentPage">
                      <button class="page-link" (click)="onPageChange(page)">{{ page }}</button>
                    </li>
                    <li class="page-item" [class.disabled]="currentPage === getTotalPages()">
                      <button class="page-link" (click)="onPageChange(currentPage + 1)" [disabled]="currentPage === getTotalPages()">
                        <i class="fas fa-angle-right"></i>
                      </button>
                    </li>
                    <li class="page-item" [class.disabled]="currentPage === getTotalPages()">
                      <button class="page-link" (click)="onPageChange(getTotalPages())" [disabled]="currentPage === getTotalPages()">
                        <i class="fas fa-angle-double-right"></i>
                      </button>
                    </li>
                  </ul>
                </nav>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .card {
      border-radius: 12px;
      border: 1px solid #e9ecef;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .card-header {
      background-color: #f8f9fa;
      border-bottom: 1px solid #e9ecef;
      border-radius: 12px 12px 0 0 !important;
    }

    .table th {
      border-top: none;
      font-weight: 600;
      color: #495057;
      background-color: #f8f9fa;
    }

    .table td {
      vertical-align: middle;
    }

    .badge {
      font-size: 0.75rem;
      padding: 0.375rem 0.75rem;
    }

    .sortable {
      cursor: pointer;
      user-select: none;
      transition: background-color 0.2s ease;
    }

    .sortable:hover {
      background-color: #e9ecef;
    }

    .sortable i {
      opacity: 0.5;
    }

    .sortable i.fa-sort-up,
    .sortable i.fa-sort-down {
      opacity: 1;
      color: #007bff;
    }
  `]
})
export class AdminUsersComponent implements OnInit {
  // Data
  users: User[] = [];
  currentUser: User | undefined = undefined;
  userStats = {
    total: 0,
    active: 0,
    inactive: 0,
    admins: 0
  };

  // Filters
  filters: UserFilters = {
    skip: 0,
    limit: 20
  };

  // Pagination
  currentPage = 1;
  totalUsers = 0;
  itemsPerPage = 20;

  // Sorting
  sortBy = 'created_at';
  sortOrder: 'asc' | 'desc' = 'desc';

  // UI State
  loading = false;
  dashboardData: any = null;

  constructor(
    private userService: UserService,
    private userAdminService: UserAdminService,
    private authService: AuthService,
    private toastService: ToastService,
    private adminService: AdminService
  ) {}

  async ngOnInit(): Promise<void> {
    await this.loadCurrentUser();
    await this.loadDashboardData();
    await this.loadUserStatistics(); // Load user statistics from API
    await this.loadUsers();
  }

  async loadDashboardData(): Promise<void> {
    try {
      this.dashboardData = await this.adminService.getDashboardData().toPromise();
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      // Don't show error for this as it's not critical
    }
  }

  async loadUserStatistics(): Promise<void> {
    try {
      const stats = await this.adminService.getUserStatistics().toPromise();
      if (stats) {
        this.userStats = {
          total: stats.total_users,
          active: stats.active_users,
          inactive: stats.inactive_users,
          admins: stats.admin_users
        };
      }
    } catch (error) {
      console.error('Error loading user statistics:', error);
      // Fallback to calculating from loaded users if API fails
      this.calculateUserStatsFromLoadedUsers();
    }
  }

  async loadUsers(): Promise<void> {
    try {
      this.loading = true;
      
      console.log('👥 Loading users with filters:', this.filters);
      this.users = await this.userService.getAllUsers(this.filters);
      
      // Set total users from user statistics (if not filtered)
      if (!this.filters.search && this.filters.is_active === undefined && this.filters.is_admin === undefined) {
        this.totalUsers = this.userStats.total;
      } else {
        // For filtered results, we need to estimate or fetch a total count
        // For now, use the loaded users count (not ideal for large datasets)
        this.totalUsers = this.users.length + (this.currentPage > 1 ? (this.currentPage - 1) * this.itemsPerPage : 0);
      }
      
      console.log('👥 Loaded users:', this.users.length, 'Total:', this.totalUsers);
    } catch (error) {
      console.error('Error loading users:', error);
      this.toastService.showError('Failed to load users');
    } finally {
      this.loading = false;
    }
  }

  async loadCurrentUser(): Promise<void> {
    try {
      this.currentUser = await this.userService.getCurrentUserProfile();
      console.log('👤 Current user loaded:', this.currentUser);
    } catch (error) {
      console.error('Error loading current user:', error);
      // Don't show error toast for this as it's not critical
    }
  }

  async refreshUsers(): Promise<void> {
    await this.loadUsers();
    this.toastService.showSuccess('Users refreshed');
  }

  // Admin management methods
  async onAdminToggled(user: User): Promise<void> {
    console.log('👑 Admin status toggled for user:', user);
    
    // Update the user in the local array
    const index = this.users.findIndex(u => u.id === user.id);
    if (index !== -1) {
      this.users[index] = { ...user };
    }
    
    // Recalculate statistics
    await this.loadUserStatistics();
    
    // Show success message is handled by AdminToggleComponent
  }

  // Filter, Sort, and Pagination methods
  onFilterChange(): void {
    this.currentPage = 1;
    this.filters.skip = 0;
    this.loadUsers();
  }

  clearFilters(): void {
    this.filters = {
      skip: 0,
      limit: this.itemsPerPage
    };
    this.currentPage = 1;
    this.loadUsers();
  }

  onSort(field: string): void {
    if (this.sortBy === field) {
      this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortBy = field;
      this.sortOrder = 'asc';
    }
    this.currentPage = 1;
    this.filters.skip = 0;
    this.loadUsers();
  }

  onPageChange(page: number): void {
    this.currentPage = page;
    this.filters.skip = (page - 1) * this.itemsPerPage;
    this.loadUsers();
  }

  onItemsPerPageChange(): void {
    this.filters.limit = this.itemsPerPage;
    this.currentPage = 1;
    this.filters.skip = 0;
    this.loadUsers();
  }

  getTotalPages(): number {
    return Math.ceil(this.totalUsers / this.itemsPerPage);
  }

  getPagesArray(): number[] {
    const totalPages = this.getTotalPages();
    const maxVisible = 5;
    let startPage = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
      startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    const pages: number[] = [];
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    return pages;
  }

  Math = Math; // Make Math available in template

  // User actions
  viewUser(user: User): void {
    console.log('👁️ View user:', user);
    // TODO: Open user details modal
  }

  editUser(user: User): void {
    console.log('✏️ Edit user:', user);
    // TODO: Open user edit form
  }

  async toggleUserStatus(user: User): Promise<void> {
    try {
      const action = user.is_active ? 'deactivate' : 'activate';
      const confirmed = confirm(`Are you sure you want to ${action} ${this.formatUserName(user)}?`);
      
      if (!confirmed) return;

      if (user.is_active) {
        await this.userService.deactivateUser(user.id);
        this.toastService.showSuccess(`User ${this.formatUserName(user)} deactivated`);
      } else {
        await this.userService.activateUser(user.id);
        this.toastService.showSuccess(`User ${this.formatUserName(user)} activated`);
      }

      // Refresh user list
      await this.loadUsers();
      
    } catch (error) {
      console.error('Error toggling user status:', error);
      this.toastService.showError('Failed to update user status');
    }
  }

  // Helper methods
  trackByUserId(index: number, user: User): string {
    return user.id;
  }

  formatUserName(user: User): string {
    return this.userService.formatUserName(user);
  }

  formatUserStatus(user: User): { text: string; class: string } {
    return this.userService.formatUserStatus(user);
  }

  formatUserRole(user: User): { text: string; class: string; icon: string } {
    return this.userService.formatUserRole(user);
  }

  formatDate(dateString: string): string {
    return this.userService.formatDate(dateString);
  }

  formatCurrency(amount: number): string {
    return this.userService.formatCurrency(amount);
  }

  private calculateUserStatsFromLoadedUsers(): void {
    // Fallback method when API fails - calculate from loaded users only
    this.userStats = {
      total: this.users.length, // Note: This is only the loaded users, not the total count
      active: this.users.filter(u => u.is_active).length,
      inactive: this.users.filter(u => !u.is_active).length,
      admins: this.users.filter(u => u.is_admin).length
    };
  }
}