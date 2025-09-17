import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-state',
  standalone: true,
  imports: [CommonModule],
  template: `
    <!-- Skeleton Cards Loading -->
    <div *ngIf="type === 'cards'" class="row">
      <div *ngFor="let item of skeletonItems" class="col-lg-4 col-md-6 mb-4">
        <div class="card skeleton-card">
          <div class="card-body">
            <div class="skeleton-line skeleton-title mb-3"></div>
            <div class="skeleton-line skeleton-text mb-2"></div>
            <div class="skeleton-line skeleton-text mb-2"></div>
            <div class="skeleton-line skeleton-text-short mb-3"></div>
            <div class="d-flex gap-2">
              <div class="skeleton-button"></div>
              <div class="skeleton-button"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Spinner Loading -->
    <div *ngIf="type === 'spinner'" class="text-center py-5">
      <div class="spinner-border text-primary" [class]="spinnerSize" role="status">
        <span class="visually-hidden">{{ loadingText }}</span>
      </div>
      <div class="mt-3 text-muted">{{ loadingText }}</div>
    </div>

    <!-- Inline Loading -->
    <div *ngIf="type === 'inline'" class="d-flex align-items-center justify-content-center py-3">
      <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
        <span class="visually-hidden">{{ loadingText }}</span>
      </div>
      <span class="text-muted">{{ loadingText }}</span>
    </div>

    <!-- Table Loading -->
    <div *ngIf="type === 'table'" class="table-responsive">
      <table class="table">
        <thead>
          <tr>
            <th *ngFor="let header of tableHeaders" class="skeleton-line skeleton-header"></th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let row of skeletonItems">
            <td *ngFor="let header of tableHeaders" class="skeleton-line skeleton-cell"></td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  styles: [`
    .skeleton-card {
      border: 1px solid #e9ecef;
      border-radius: 12px;
      background: #fff;
    }

    .skeleton-line {
      background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
      background-size: 200% 100%;
      animation: loading 1.5s infinite;
      border-radius: 4px;
      height: 1rem;
    }

    .skeleton-title {
      height: 1.25rem;
      width: 70%;
    }

    .skeleton-text {
      height: 0.875rem;
      width: 100%;
    }

    .skeleton-text-short {
      height: 0.875rem;
      width: 60%;
    }

    .skeleton-button {
      height: 2rem;
      width: 4rem;
      background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
      background-size: 200% 100%;
      animation: loading 1.5s infinite;
      border-radius: 6px;
    }

    .skeleton-header {
      height: 1rem;
      width: 80%;
    }

    .skeleton-cell {
      height: 0.875rem;
      width: 90%;
    }

    @keyframes loading {
      0% {
        background-position: 200% 0;
      }
      100% {
        background-position: -200% 0;
      }
    }

    .spinner-border-lg {
      width: 3rem;
      height: 3rem;
    }
  `]
})
export class LoadingStateComponent {
  @Input() type: 'cards' | 'spinner' | 'inline' | 'table' = 'spinner';
  @Input() loadingText: string = 'Loading...';
  @Input() itemCount: number = 6;
  @Input() tableHeaders: string[] = ['', '', '', ''];
  @Input() size: 'sm' | 'md' | 'lg' = 'md';

  get skeletonItems(): number[] {
    return Array(this.itemCount).fill(0).map((_, i) => i);
  }

  get spinnerSize(): string {
    const sizes = {
      'sm': 'spinner-border-sm',
      'md': '',
      'lg': 'spinner-border-lg'
    };
    return sizes[this.size];
  }
}
