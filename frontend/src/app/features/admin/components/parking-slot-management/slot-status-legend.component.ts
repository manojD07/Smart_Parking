import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

interface LegendItem {
  label: string;
  class: string;
  icon: string;
  count?: number;
}

@Component({
  selector: 'app-slot-status-legend',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="legend-container">
      <div class="legend-header" *ngIf="showTitle">
        <h6 class="legend-title">
          <i class="fas fa-info-circle me-2"></i>
          Slot Status Legend
        </h6>
      </div>
      
      <div class="legend-items" [class.compact]="compact">
        <div 
          *ngFor="let item of legendItems" 
          class="legend-item"
          [class.with-count]="item.count !== undefined">
          
          <div class="legend-indicator" [class]="item.class">
            <i class="fas" [class]="item.icon"></i>
          </div>
          
          <span class="legend-label">{{ item.label }}</span>
          
          <span *ngIf="item.count !== undefined" class="legend-count">
            ({{ item.count }})
          </span>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .legend-container {
      background: #f8f9fa;
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid #e9ecef;
    }

    .legend-header {
      margin-bottom: 0.75rem;
    }

    .legend-title {
      margin: 0;
      font-size: 0.875rem;
      font-weight: 600;
      color: #495057;
    }

    .legend-items {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .legend-items.compact {
      gap: 0.75rem;
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.875rem;
      white-space: nowrap;
    }

    .legend-indicator {
      width: 24px;
      height: 24px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      color: white;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .legend-label {
      font-weight: 500;
      color: #495057;
    }

    .legend-count {
      color: #6c757d;
      font-weight: 400;
      font-size: 0.8rem;
    }

    /* Slot Status Colors */
    .slot-available {
      background-color: #28a745;
    }

    .slot-occupied {
      background-color: #dc3545;
    }

    .slot-reserved {
      background-color: #ffc107;
      color: #212529 !important;
    }

    .slot-inactive {
      background-color: #6c757d;
    }

    .slot-maintenance {
      background-color: #fd7e14;
    }

    @media (max-width: 768px) {
      .legend-container {
        padding: 0.75rem;
      }

      .legend-items {
        gap: 0.5rem;
      }

      .legend-item {
        font-size: 0.8rem;
      }

      .legend-indicator {
        width: 20px;
        height: 20px;
        font-size: 0.7rem;
      }
    }
  `]
})
export class SlotStatusLegendComponent {
  @Input() showTitle: boolean = true;
  @Input() compact: boolean = false;
  @Input() availableCount?: number;
  @Input() occupiedCount?: number;
  @Input() reservedCount?: number;
  @Input() inactiveCount?: number;
  @Input() maintenanceCount?: number;

  get legendItems(): LegendItem[] {
    return [
      {
        label: 'Available',
        class: 'slot-available',
        icon: 'fa-check',
        count: this.availableCount
      },
      {
        label: 'Occupied',
        class: 'slot-occupied',
        icon: 'fa-times',
        count: this.occupiedCount
      },
      {
        label: 'Reserved',
        class: 'slot-reserved',
        icon: 'fa-clock',
        count: this.reservedCount
      },
      {
        label: 'Inactive',
        class: 'slot-inactive',
        icon: 'fa-ban',
        count: this.inactiveCount
      },
      {
        label: 'Maintenance',
        class: 'slot-maintenance',
        icon: 'fa-wrench',
        count: this.maintenanceCount
      }
    ];
  }
}
