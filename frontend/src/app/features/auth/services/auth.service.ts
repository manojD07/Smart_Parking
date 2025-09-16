import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { Router } from '@angular/router';
import { BaseApiService } from '../../../core/services/base-api.service';
import { User, UserLogin, UserRegistration, TokenResponse, ChangePasswordRequest } from '../../../core/models/user.model';
import { SuccessResponse } from '../../../core/models/common.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService extends BaseApiService {
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(false);

  public currentUser$ = this.currentUserSubject.asObservable();
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

  constructor(private router: Router) {
    super(inject(HttpClient));
    this.checkExistingAuth();
  }

  private checkExistingAuth(): void {
    const token = this.getToken();
    const user = this.getStoredUser();
    
    if (token && user) {
      this.currentUserSubject.next(user);
      this.isAuthenticatedSubject.next(true);
    }
  }

  register(userData: UserRegistration): Observable<User> {
    return this.post<User>('/auth/register', userData);
  }

  login(credentials: UserLogin): Observable<TokenResponse> {
    return this.post<TokenResponse>('/auth/login', credentials).pipe(
      tap(response => {
        this.setToken(response.access_token);
        this.setRefreshToken(response.refresh_token);
        
        // If user data is included in login response, use it directly
        if (response.user) {
          this.currentUserSubject.next(response.user);
          this.isAuthenticatedSubject.next(true);
          localStorage.setItem('current_user', JSON.stringify(response.user));
        } else {
          // Fallback: fetch user data separately
          this.getCurrentUser().subscribe();
        }
      })
    );
  }

  logout(): void {
    console.log('AuthService: logout() called');
    console.log('AuthService: Before logout - token exists:', !!this.getToken());
    console.log('AuthService: Before logout - current user:', this.currentUser);
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('current_user');
    
    this.currentUserSubject.next(null);
    this.isAuthenticatedSubject.next(false);
    
    console.log('AuthService: After logout - localStorage cleared');
    console.log('AuthService: After logout - subjects updated');
    console.log('AuthService: Navigating to login...');
    
    this.router.navigate(['/auth/login']);
  }

  getCurrentUser(): Observable<User> {
    return this.get<User>('/users/me').pipe(
      tap(user => {
        this.currentUserSubject.next(user);
        this.isAuthenticatedSubject.next(true);
        localStorage.setItem('current_user', JSON.stringify(user));
      })
    );
  }

  updateProfile(userData: Partial<User>): Observable<User> {
    return this.put<User>('/users/me', userData).pipe(
      tap(user => {
        this.currentUserSubject.next(user);
        localStorage.setItem('current_user', JSON.stringify(user));
      })
    );
  }

  changePassword(passwordData: ChangePasswordRequest): Observable<SuccessResponse> {
    return this.post<SuccessResponse>('/auth/change-password', passwordData);
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  private setToken(token: string): void {
    localStorage.setItem('access_token', token);
  }

  private setRefreshToken(token: string): void {
    localStorage.setItem('refresh_token', token);
  }

  private getStoredUser(): User | null {
    const userStr = localStorage.getItem('current_user');
    return userStr ? JSON.parse(userStr) : null;
  }

  get currentUser(): User | null {
    return this.currentUserSubject.value;
  }

  get isAuthenticated(): boolean {
    return this.isAuthenticatedSubject.value;
  }
}
