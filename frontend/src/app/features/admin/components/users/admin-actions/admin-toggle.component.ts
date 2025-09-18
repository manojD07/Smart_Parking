import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

// Services
import { UserAdminService, AdminValidationResult } from '../../../../../core/services/user-admin.service';
import { User } from '../../../../../core/services/user.service';
import { ToastService } from '../../../../../core/services/toast.service';

@Component({
  selector: 'app-admin-toggle',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="admin-toggle-container">
      <!-- Admin Toggle Button -->
      <button 
        type="button"
        [class]="getToggleButtonClass()"
        [disabled]="loading || !validation?.canPerformAction"
        [title]="getButtonTooltip()"
        (click)="showConfirmation()">
        
        <span *ngIf="loading" class="spinner-border spinner-border-sm me-1"></span>
        <i *ngIf="!loading" class="fas me-1" [class]="getToggleButtonIcon()"></i>
        {{ getToggleButtonText() }}
      </button>

      <!-- Confirmation Modal -->
      <div 
        class="modal fade" 
        [id]="'adminToggleModal_' + user.id" 
        tabindex="-1" 
        aria-labelledby="adminToggleModalLabel" 
        aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="adminToggleModalLabel">
                <i class="fas me-2" [class]="getModalIcon()"></i>
                {{ getModalTitle() }}
              </h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div class="alert" [class]="getAlertClass()">
                <i class="fas me-2" [class]="getAlertIcon()"></i>
                {{ getConfirmationMessage() }}
              </div>

              <!-- Admin Statistics -->
              <div class="admin-stats mb-3" *ngIf="validation">
                <small class="text-muted d-block mb-2">Current Admin Status:</small>
                <div class="row text-center">
                  <div class="col-6">
                    <div class="stat-value text-warning">{{ validation.currentAdminCount }}</div>
                    <div class="stat-label">Current Admins</div>
                  </div>
                  <div class="col-6">
                    <div class="stat-value text-info">{{ validation.minimumRequired }}</div>
                    <div class="stat-label">Minimum Required</div>
                  </div>
                </div>
              </div>

              <!-- Warnings -->
              <div class="warnings" *ngIf="validation?.warnings && validation.warnings.length > 0">
                <small class="text-muted d-block mb-2">Important Notes:</small>
                <ul class="list-unstyled">
                  <li *ngFor="let warning of validation.warnings" class="text-warning mb-1">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <small>{{ warning }}</small>
                  </li>
                </ul>
              </div>

              <!-- Error Message -->
              <div class="alert alert-danger" *ngIf="validation && !validation.canPerformAction">
                <i class="fas fa-times-circle me-2"></i>
                {{ validation.reason }}
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                Cancel
              </button>
              <button 
                type="button" 
                class="btn"
                [class]="getConfirmButtonClass()"
                [disabled]="!validation?.canPerformAction || confirmingAction"
                (click)="confirmAdminAction()">
                
                <span *ngIf="confirmingAction" class="spinner-border spinner-border-sm me-1"></span>
                <i *ngIf="!confirmingAction" class="fas me-1" [class]="getConfirmButtonIcon()"></i>
                {{ getConfirmButtonText() }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .admin-toggle-container {
      display: inline-block;
    }

    .stat-value {
      font-size: 1.25rem;
      font-weight: 700;
      margin-bottom: 0.25rem;
    }

    .stat-label {
      font-size: 0.75rem;
      color: #6c757d;
      font-weight: 500;
    }

    .admin-stats {
      background-color: #f8f9fa;
      border-radius: 8px;
      padding: 1rem;
    }

    .warnings {
      background-color: #fff3cd;
      border-radius: 8px;
      padding: 0.75rem;
      border-left: 4px solid #ffc107;
    }

    .warnings ul {
      margin-bottom: 0;
    }

    .modal-content {
      border-radius: 12px;
      border: none;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }

    .modal-header {
      border-bottom: 1px solid #e9ecef;
      background-color: #f8f9fa;
      border-radius: 12px 12px 0 0;
    }

    .btn-sm {
      font-size: 0.875rem;
      padding: 0.375rem 0.75rem;
    }

    @media (max-width: 768px) {
      .modal-dialog {
        margin: 1rem;
      }
      
      .stat-value {
        font-size: 1rem;
      }
    }
  `]
})
export class AdminToggleComponent implements OnInit {
  @Input() user!: User;
  @Input() currentUser?: User;
  @Input() allUsers: User[] = [];
  @Output() adminToggled = new EventEmitter<User>();

  validation: AdminValidationResult | null = null;
  loading = false;
  confirmingAction = false;
  private modal: any;

  constructor(
    private userAdminService: UserAdminService,
    private toastService: ToastService
  ) {}

  async ngOnInit(): Promise<void> {
    await this.validateAction();
  }

  ngAfterViewInit(): void {
    // Initialize Bootstrap modal with unique ID
    const modalElement = document.getElementById(`adminToggleModal_${this.user.id}`);
    if (modalElement) {
      this.modal = new (window as any).bootstrap.Modal(modalElement);
    }
  }

  async validateAction(): Promise<void> {
    try {
      this.loading = true;
      
      const action = this.user.is_admin ? 'remove_admin' : 'make_admin';
      this.validation = await this.userAdminService.validateAdminAction(
        this.user.id,
        action,
        this.currentUser,
        this.allUsers
      );
      
    } catch (error) {
      console.error('Error validating admin action:', error);
      this.validation = {
        canPerformAction: false,
        reason: 'Unable to validate action',
        warnings: [],
        currentAdminCount: 0,
        minimumRequired: 1
      };
    } finally {
      this.loading = false;
    }
  }

  async showConfirmation(): Promise<void> {
    await this.validateAction(); // Re-validate before showing modal
    
    if (this.validation?.canPerformAction) {
      this.modal?.show();
    } else {
      this.toastService.showError(this.validation?.reason || 'Cannot perform this action');
    }
  }

  async confirmAdminAction(): Promise<void> {
    if (!this.validation?.canPerformAction) return;

    try {
      this.confirmingAction = true;
      
      const action = this.user.is_admin ? 'remove_admin' : 'make_admin';
      let success = false;

      if (action === 'make_admin') {
        success = await this.userAdminService.makeUserAdmin(this.user.id);
      } else {
        success = await this.userAdminService.removeUserAdmin(this.user.id);
      }

      if (success) {
        // Log the action
        this.userAdminService.logAdminAction({
          userId: this.user.id,
          userName: `${this.user.first_name} ${this.user.last_name}`,
          action,
          timestamp: new Date().toISOString(),
          performedBy: this.currentUser?.email
        });

        // Update local user object
        this.user.is_admin = !this.user.is_admin;
        
        // Show success message
        const actionText = action === 'make_admin' ? 'granted admin privileges' : 'removed admin privileges';
        this.toastService.showSuccess(`Successfully ${actionText} for ${this.user.first_name} ${this.user.last_name}`);
        
        // Emit event for parent component
        this.adminToggled.emit(this.user);
        
        // Close modal
        this.modal?.hide();
        
        // Re-validate for next action
        await this.validateAction();
        
      } else {
        this.toastService.showError('Failed to update admin status');
      }

    } catch (error) {
      console.error('Error confirming admin action:', error);
      this.toastService.showError('Failed to update admin status');
    } finally {
      this.confirmingAction = false;
    }
  }

  // UI Helper Methods
  getToggleButtonClass(): string {
    if (!this.validation) return 'btn btn-outline-secondary btn-sm';
    
    const buttonInfo = this.userAdminService.getAdminToggleButton(this.user);
    return this.validation.canPerformAction ? buttonInfo.class : 'btn btn-outline-secondary btn-sm';
  }

  getToggleButtonIcon(): string {
    return this.userAdminService.getAdminToggleButton(this.user).icon;
  }

  getToggleButtonText(): string {
    return this.userAdminService.getAdminToggleButton(this.user).text;
  }

  getButtonTooltip(): string {
    if (!this.validation?.canPerformAction) {
      return this.validation?.reason || 'Action not available';
    }
    
    const action = this.user.is_admin ? 'Remove admin privileges' : 'Grant admin privileges';
    return `${action} for ${this.user.first_name} ${this.user.last_name}`;
  }

  getModalTitle(): string {
    const action = this.user.is_admin ? 'remove_admin' : 'make_admin';
    return this.userAdminService.getAdminActionMessage(action, this.user, this.validation!).title;
  }

  getConfirmationMessage(): string {
    const action = this.user.is_admin ? 'remove_admin' : 'make_admin';
    return this.userAdminService.getAdminActionMessage(action, this.user, this.validation!).message;
  }

  getModalIcon(): string {
    return this.user.is_admin ? 'fa-user-minus' : 'fa-crown';
  }

  getAlertClass(): string {
    return this.user.is_admin ? 'alert-warning' : 'alert-info';
  }

  getAlertIcon(): string {
    return this.user.is_admin ? 'fa-exclamation-triangle' : 'fa-info-circle';
  }

  getConfirmButtonClass(): string {
    return this.user.is_admin ? 'btn-danger' : 'btn-warning';
  }

  getConfirmButtonIcon(): string {
    return this.user.is_admin ? 'fa-user-minus' : 'fa-crown';
  }

  getConfirmButtonText(): string {
    return this.user.is_admin ? 'Remove Admin' : 'Make Admin';
  }
}
