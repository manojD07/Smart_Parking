import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-not-found',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="container mt-5">
      <div class="row justify-content-center">
        <div class="col-md-6 text-center">
          <div class="error-page">
            <h1 class="display-1 text-primary">404</h1>
            <h2 class="h4 mb-3">Page Not Found</h2>
            <p class="text-muted mb-4">
              The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
            </p>
            <div class="d-grid gap-2 d-md-flex justify-content-md-center">
              <button class="btn btn-primary me-md-2" routerLink="/dashboard">
                <i class="fas fa-home me-2"></i>
                Go to Dashboard
              </button>
              <button class="btn btn-outline-secondary" onclick="history.back()">
                <i class="fas fa-arrow-left me-2"></i>
                Go Back
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class NotFoundComponent {}
