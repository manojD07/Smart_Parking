import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <span class="badge" [class]="badgeClass">
      <i *ngIf="icon" class="fas" [class]="icon"></i>
      {{ text }}
    </span>
  `,
  styles: [`
    .badge {
      font-size: 0.75rem;
      padding: 0.375rem 0.75rem;
      border-radius: 6px;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
    }
    
    .badge i {
      font-size: 0.7rem;
    }
  `]
})
export class StatusBadgeComponent {
  @Input() status: 'active' | 'inactive' | 'available' | 'occupied' | 'reserved' | 'success' | 'error' | 'warning' | 'info' = 'info';
  @Input() text: string = '';
  @Input() icon?: string;

  get badgeClass(): string {
    const classes: { [key: string]: string } = {
      'active': 'bg-success text-white',
      'inactive': 'bg-danger text-white',
      'available': 'bg-success text-white',
      'occupied': 'bg-danger text-white',
      'reserved': 'bg-warning text-dark',
      'success': 'bg-success text-white',
      'error': 'bg-danger text-white',
      'warning': 'bg-warning text-dark',
      'info': 'bg-info text-white'
    };
    return classes[this.status] || classes['info'];
  }
}
