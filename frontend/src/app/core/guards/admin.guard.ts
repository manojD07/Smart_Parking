import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { map, take } from 'rxjs/operators';
import { AuthService } from '../../features/auth/services/auth.service';

export const adminGuard = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.currentUser$.pipe(
    take(1),
    map(user => {
      // Only allow admin access if user has is_admin = true
      if (user && user.is_admin === true) {
        return true;
      }
      
      console.log('Admin guard: Access denied. User is not admin:', user);
      
      // Redirect to regular dashboard if not admin
      router.navigate(['/dashboard']);
      return false;
    })
  );
};
