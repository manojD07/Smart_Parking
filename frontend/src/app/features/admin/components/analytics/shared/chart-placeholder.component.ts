import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-chart-placeholder',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="chart-placeholder d-flex align-items-center justify-content-center h-100 bg-light rounded">
      <div class="text-center">
        <i class="fas" [class]="icon" class="fa-3x text-muted mb-3"></i>
        <h6>{{ title }}</h6>
        <p class="text-muted mb-0" *ngIf="subtitle">{{ subtitle }}</p>
        <small class="text-muted" *ngIf="dataPoints > 0">{{ dataPoints }} data points available</small>
        <div class="mt-2" *ngIf="showComingSoon">
          <small class="badge bg-info">Chart visualization coming soon</small>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .chart-placeholder {
      min-height: 200px;
      border: 2px dashed #dee2e6;
      transition: all 0.3s ease;
    }

    .chart-placeholder:hover {
      border-color: #adb5bd;
      background-color: #f1f3f4 !important;
    }

    .badge {
      font-size: 0.7rem;
      padding: 0.25rem 0.5rem;
    }
  `]
})
export class ChartPlaceholderComponent {
  @Input() title: string = 'Chart';
  @Input() subtitle: string = '';
  @Input() icon: string = 'fa-chart-bar';
  @Input() dataPoints: number = 0;
  @Input() showComingSoon: boolean = true;
}
