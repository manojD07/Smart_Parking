import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { ParkingLot } from '../models/parking.model';

export interface SearchParams {
  vehicleType: string;
  lotId?: string;
  startTime: string;
  duration: string;
}

export interface SearchState {
  params: SearchParams | null;
  results: ParkingLot[];
  hasSearched: boolean;
  lastSearchTime: Date | null;
}

@Injectable({
  providedIn: 'root'
})
export class SearchStateService {
  private readonly STORAGE_KEY = 'parking_search_state';
  private readonly EXPIRY_MINUTES = 30; // Search state expires after 30 minutes

  private searchStateSubject = new BehaviorSubject<SearchState>({
    params: null,
    results: [],
    hasSearched: false,
    lastSearchTime: null
  });

  public searchState$ = this.searchStateSubject.asObservable();

  constructor() {
    this.loadSearchState();
  }

  /**
   * Save search parameters and results
   */
  saveSearchState(params: SearchParams, results: ParkingLot[]): void {
    const searchState: SearchState = {
      params,
      results,
      hasSearched: true,
      lastSearchTime: new Date()
    };

    // Save to memory
    this.searchStateSubject.next(searchState);

    // Save to localStorage for persistence across page reloads
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(searchState));
    } catch (error) {
      console.warn('Failed to save search state to localStorage:', error);
    }
  }

  /**
   * Get current search state
   */
  getCurrentSearchState(): SearchState {
    return this.searchStateSubject.value;
  }

  /**
   * Check if we have valid search results
   */
  hasValidSearchResults(): boolean {
    const state = this.getCurrentSearchState();
    
    if (!state.hasSearched || !state.lastSearchTime) {
      return false;
    }

    // Check if search results are still valid (not expired)
    const now = new Date();
    const searchTime = new Date(state.lastSearchTime);
    const diffMinutes = (now.getTime() - searchTime.getTime()) / (1000 * 60);

    return diffMinutes < this.EXPIRY_MINUTES;
  }

  /**
   * Clear search state
   */
  clearSearchState(): void {
    const emptyState: SearchState = {
      params: null,
      results: [],
      hasSearched: false,
      lastSearchTime: null
    };

    this.searchStateSubject.next(emptyState);
    
    try {
      localStorage.removeItem(this.STORAGE_KEY);
    } catch (error) {
      console.warn('Failed to clear search state from localStorage:', error);
    }
  }

  /**
   * Load search state from localStorage
   */
  private loadSearchState(): void {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        const searchState: SearchState = JSON.parse(stored);
        
        // Check if the stored state is still valid
        if (searchState.lastSearchTime) {
          const now = new Date();
          const searchTime = new Date(searchState.lastSearchTime);
          const diffMinutes = (now.getTime() - searchTime.getTime()) / (1000 * 60);

          if (diffMinutes < this.EXPIRY_MINUTES) {
            this.searchStateSubject.next(searchState);
            return;
          }
        }
      }
    } catch (error) {
      console.warn('Failed to load search state from localStorage:', error);
    }

    // If no valid stored state, start with empty state
    this.clearSearchState();
  }

  /**
   * Get search results URL with parameters
   */
  getSearchResultsUrl(): string {
    const state = this.getCurrentSearchState();
    if (!state.params) {
      return '/parking';
    }

    const queryParams = new URLSearchParams();
    queryParams.set('vehicleType', state.params.vehicleType);
    queryParams.set('startTime', state.params.startTime);
    queryParams.set('duration', state.params.duration);
    
    if (state.params.lotId) {
      queryParams.set('lotId', state.params.lotId);
    }

    return `/parking?${queryParams.toString()}`;
  }
}
