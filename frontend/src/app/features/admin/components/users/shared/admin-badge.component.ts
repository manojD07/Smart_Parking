import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { User } from '../../../../../core/services/user.service';

@Component({
  selector: 'app-admin-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <span 
      class="admin-badge badge"
      [class]="getBadgeClass()"
      [title]="getBadgeTooltip()">
      <i class="fas me-1" [class]="getBadgeIcon()"></i>
      {{ getBadgeText() }}
      <i *ngIf="showAdminIndicator && user.is_admin" class="fas fa-star ms-1 admin-star"></i>
    </span>
  `,
  styles: [`
    .admin-badge {
      font-size: 0.75rem;
      padding: 0.375rem 0.75rem;
      font-weight: 600;
      border-radius: 6px;
      transition: all 0.3s ease;
      cursor: default;
    }

    .admin-badge:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .admin-star {
      font-size: 0.6rem;
      animation: sparkle 2s infinite;
    }

    @keyframes sparkle {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    .badge.bg-admin {
      background: linear-gradient(135deg, #ffc107 0%, #ff8c00 100%) !important;
      color: #333 !important;
      border: 1px solid #e0a800;
    }

    .badge.bg-user {
      background-color: #6c757d !important;
      color: white !important;
    }

    .badge.bg-super-admin {
      background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%) !important;
      color: white !important;
      border: 1px solid #c82333;
    }

    @media (max-width: 768px) {
      .admin-badge {
        font-size: 0.7rem;
        padding: 0.25rem 0.5rem;
      }
      
      .admin-star {
        font-size: 0.5rem;
      }
    }
  `]
})
export class AdminBadgeComponent {
  @Input() user!: User;
  @Input() size: 'sm' | 'md' | 'lg' = 'md';
  @Input() showAdminIndicator: boolean = true;
  @Input() variant: 'default' | 'minimal' | 'detailed' = 'default';

  getBadgeClass(): string {
    const baseClasses = ['badge'];
    
    // Size classes
    if (this.size === 'sm') baseClasses.push('badge-sm');
    if (this.size === 'lg') baseClasses.push('badge-lg');
    
    // Role-based classes
    if (this.user.is_admin) {
      // Check if this is a super admin (for future enhancement)
      baseClasses.push('bg-admin');
    } else {
      baseClasses.push('bg-user');
    }
    
    return baseClasses.join(' ');
  }

  getBadgeIcon(): string {
    if (this.user.is_admin) {
      return 'fa-crown';
    } else {
      return 'fa-user';
    }
  }

  getBadgeText(): string {
    if (this.variant === 'minimal') {
      return this.user.is_admin ? 'A' : 'U';
    }
    
    if (this.variant === 'detailed') {
      return this.user.is_admin ? 'Administrator' : 'Regular User';
    }
    
    // Default variant
    return this.user.is_admin ? 'Admin' : 'User';
  }

  getBadgeTooltip(): string {
    const roleName = this.user.is_admin ? 'Administrator' : 'Regular User';
    const permissions = this.user.is_admin 
      ? 'Full system access with administrative privileges'
      : 'Standard user access to parking and booking features';
    
    return `${roleName}: ${permissions}`;
  }
}
