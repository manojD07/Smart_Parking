import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { Router } from '@angular/router';
import { AuthService } from '../../features/auth/services/auth.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const authService = inject(AuthService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'An unexpected error occurred';

      if (error.error instanceof ErrorEvent) {
        // Client-side error
        errorMessage = `Error: ${error.error.message}`;
      } else {
        // Server-side error
        switch (error.status) {
          case 401:
            // Unauthorized - clear token and redirect to login
            authService.logout();
            router.navigate(['/auth/login']);
            errorMessage = 'Session expired. Please login again.';
            break;
          case 403:
            errorMessage = 'Access forbidden. You don\'t have permission to access this resource.';
            break;
          case 404:
            errorMessage = 'The requested resource was not found.';
            break;
          case 422:
            // Validation error
            if (error.error?.detail) {
              errorMessage = error.error.detail;
            } else if (error.error?.errors) {
              errorMessage = error.error.errors.join(', ');
            } else {
              errorMessage = 'Validation error occurred.';
            }
            break;
          case 500:
            errorMessage = 'Internal server error. Please try again later.';
            break;
          default:
            if (error.error?.detail) {
              errorMessage = error.error.detail;
            } else if (error.error?.message) {
              errorMessage = error.error.message;
            }
        }
      }

      // Log error to console for debugging
      console.error('HTTP Error:', error);

      return throwError(() => new Error(errorMessage));
    })
  );
};
