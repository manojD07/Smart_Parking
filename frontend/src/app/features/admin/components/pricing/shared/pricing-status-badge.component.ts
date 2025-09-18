import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-pricing-status-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <span class="badge" [class]="getBadgeClass()">
      <i class="fas" [class]="getIcon()"></i>
      {{ getDisplayText() }}
    </span>
  `,
  styles: [`
    .badge {
      font-size: 0.75rem;
      padding: 0.375rem 0.75rem;
      border-radius: 6px;
    }

    .badge i {
      margin-right: 0.25rem;
    }
  `]
})
export class PricingStatusBadgeComponent {
  @Input() type: 'rule_type' | 'priority' | 'status' = 'status';
  @Input() value: string = '';

  getBadgeClass(): string {
    if (this.type === 'rule_type') {
      const classes = {
        'time_based': 'bg-primary',
        'day_based': 'bg-success',
        'seasonal': 'bg-warning',
        'demand_based': 'bg-info'
      };
      return classes[this.value as keyof typeof classes] || 'bg-secondary';
    }
    
    if (this.type === 'priority') {
      const classes = {
        'high': 'bg-danger',
        'normal': 'bg-primary',
        'low': 'bg-secondary'
      };
      return classes[this.value as keyof typeof classes] || 'bg-secondary';
    }
    
    if (this.type === 'status') {
      return this.value === 'active' ? 'bg-success' : 'bg-secondary';
    }
    
    return 'bg-secondary';
  }

  getIcon(): string {
    if (this.type === 'rule_type') {
      const icons = {
        'time_based': 'fa-clock',
        'day_based': 'fa-calendar',
        'seasonal': 'fa-leaf',
        'demand_based': 'fa-chart-line'
      };
      return icons[this.value as keyof typeof icons] || 'fa-tag';
    }
    
    if (this.type === 'priority') {
      const icons = {
        'high': 'fa-star',
        'normal': 'fa-circle',
        'low': 'fa-minus'
      };
      return icons[this.value as keyof typeof icons] || 'fa-circle';
    }
    
    if (this.type === 'status') {
      return this.value === 'active' ? 'fa-check' : 'fa-times';
    }
    
    return 'fa-tag';
  }

  getDisplayText(): string {
    if (this.type === 'rule_type') {
      const texts = {
        'time_based': 'Time Based',
        'day_based': 'Day Based',
        'seasonal': 'Seasonal',
        'demand_based': 'Demand Based'
      };
      return texts[this.value as keyof typeof texts] || this.value;
    }
    
    if (this.type === 'priority') {
      return this.value.charAt(0).toUpperCase() + this.value.slice(1);
    }
    
    if (this.type === 'status') {
      return this.value === 'active' ? 'Active' : 'Inactive';
    }
    
    return this.value;
  }
}
