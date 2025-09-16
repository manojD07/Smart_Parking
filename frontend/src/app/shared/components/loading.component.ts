import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="d-flex justify-content-center align-items-center" [class]="containerClass">
      <div class="text-center">
        <div class="spinner-border text-primary" [class]="spinnerSize" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <div class="mt-2" *ngIf="message">
          <small class="text-muted">{{ message }}</small>
        </div>
      </div>
    </div>
  `
})
export class LoadingComponent {
  @Input() message = 'Loading...';
  @Input() size: 'sm' | 'md' | 'lg' = 'md';
  @Input() containerClass = 'py-5';

  get spinnerSize(): string {
    switch (this.size) {
      case 'sm':
        return 'spinner-border-sm';
      case 'lg':
        return '';
      default:
        return '';
    }
  }
}
