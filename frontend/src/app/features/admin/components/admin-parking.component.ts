import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ParkingLotListComponent } from './parking-lot-management/parking-lot-list.component';

@Component({
  selector: 'app-admin-parking',
  standalone: true,
  imports: [CommonModule, ParkingLotListComponent],
  template: `
    <div class="parking-management">
      <!-- Phase 1: Parking Lot Management -->
      <app-parking-lot-list></app-parking-lot-list>
      
      <!-- Phase 2: Slot Management will be added here -->
    </div>
  `,
  styles: [`
    .parking-management {
      min-height: 100vh;
      background-color: #f8f9fa;
    }
  `]
})
export class AdminParkingComponent {
}