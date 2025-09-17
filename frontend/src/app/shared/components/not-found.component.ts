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
          <h1 class="display-1">404</h1>
          <h2>Page Not Found</h2>
          <p class="lead">The page you're looking for doesn't exist.</p>
          <a routerLink="/" class="btn btn-primary">Go Home</a>
        </div>
      </div>
    </div>
  `
})
export class NotFoundComponent {}