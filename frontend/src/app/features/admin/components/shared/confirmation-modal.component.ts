import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-confirmation-modal',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="modal fade" [id]="modalId" tabindex="-1" [attr.aria-labelledby]="modalId + 'Label'">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" [id]="modalId + 'Label'">
              <i *ngIf="icon" class="fas" [class]="icon" [class]="iconColorClass"></i>
              {{ title }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div *ngIf="message" class="mb-3">{{ message }}</div>
            <div *ngIf="details" class="text-muted small">{{ details }}</div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              {{ cancelText }}
            </button>
            <button 
              type="button" 
              class="btn" 
              [class]="confirmButtonClass"
              (click)="onConfirm()"
              [disabled]="processing">
              <span *ngIf="processing" class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Processing...</span>
              </span>
              <i *ngIf="!processing && confirmIcon" class="fas" [class]="confirmIcon"></i>
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .modal-content {
      border-radius: 12px;
      border: none;
      box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }

    .modal-header {
      border-bottom: 1px solid #dee2e6;
      padding: 1.5rem;
    }

    .modal-body {
      padding: 1.5rem;
    }

    .modal-footer {
      border-top: 1px solid #dee2e6;
      padding: 1.5rem;
    }

    .modal-title {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: 600;
    }

    .text-danger {
      color: #dc3545 !important;
    }

    .text-warning {
      color: #f59e0b !important;
    }

    .text-info {
      color: #0ea5e9 !important;
    }

    .btn {
      border-radius: 8px;
      font-weight: 500;
      padding: 0.5rem 1rem;
    }
  `]
})
export class ConfirmationModalComponent {
  @Input() modalId: string = 'confirmationModal';
  @Input() title: string = 'Confirm Action';
  @Input() message: string = 'Are you sure you want to proceed?';
  @Input() details?: string;
  @Input() type: 'danger' | 'warning' | 'info' | 'primary' = 'danger';
  @Input() confirmText: string = 'Confirm';
  @Input() cancelText: string = 'Cancel';
  @Input() processing: boolean = false;
  @Input() icon?: string;
  @Input() confirmIcon?: string;

  @Output() confirmed = new EventEmitter<void>();

  get iconColorClass(): string {
    const classes = {
      'danger': 'text-danger',
      'warning': 'text-warning', 
      'info': 'text-info',
      'primary': 'text-primary'
    };
    return classes[this.type];
  }

  get confirmButtonClass(): string {
    const classes = {
      'danger': 'btn-danger',
      'warning': 'btn-warning',
      'info': 'btn-info',
      'primary': 'btn-primary'
    };
    return classes[this.type];
  }

  onConfirm(): void {
    this.confirmed.emit();
  }
}
