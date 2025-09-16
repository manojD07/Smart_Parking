import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="container mt-4">
      <div class="row">
        <div class="col-12">
          <h1 class="h2 mb-4">Profile</h1>
          <div class="card">
            <div class="card-body">
              <p>Profile management coming soon...</p>
              <button class="btn btn-primary" routerLink="/dashboard">Back to Dashboard</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class ProfileComponent {}
