import { Component, Input, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Subject, takeUntil, interval, catchError, of } from 'rxjs';

import { DemandLevel, DurationUtils } from '../../core/models/duration.model';
import { environment } from '../../../environments/environment';

export interface DemandInfo {
  level: DemandLevel;
  description: string;
  percentage: number;
  trend: 'rising' | 'falling' | 'stable';
  lastUpdated: string;
  factors: string[];
  recommendation: string;
}

export interface DemandIndicatorConfig {
  showPercentage: boolean;
  showTrend: boolean;
  showRecommendation: boolean;
  showFactors: boolean;
  autoRefresh: boolean;
  refreshInterval: number; // seconds
  size: 'small' | 'medium' | 'large';
  style: 'badge' | 'card' | 'inline';
}

@Component({
  selector: 'app-demand-indicator',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="demand-indicator" [ngClass]="getContainerClasses()">
      <!-- Badge Style -->
      <div *ngIf="config.style === 'badge'" class="demand-badge" [ngClass]="getDemandClasses()">
        <i [class]="getDemandIcon()"></i>
        <span class="demand-text">{{ currentDemand.description }}</span>
        <span *ngIf="config.showPercentage" class="demand-percentage">
          ({{ currentDemand.percentage }}%)
        </span>
        <i *ngIf="config.showTrend && getTrendIcon()" [class]="getTrendIcon()" class="trend-icon"></i>
      </div>

      <!-- Inline Style -->
      <div *ngIf="config.style === 'inline'" class="demand-inline" [ngClass]="getDemandClasses()">
        <i [class]="getDemandIcon()"></i>
        <span class="demand-label">Demand:</span>
        <span class="demand-level">{{ currentDemand.level | titlecase }}</span>
        <span *ngIf="config.showPercentage" class="demand-percentage">
          {{ currentDemand.percentage }}%
        </span>
      </div>

      <!-- Card Style -->
      <div *ngIf="config.style === 'card'" class="demand-card">
        <div class="card-header" [ngClass]="getDemandClasses()">
          <div class="header-content">
            <i [class]="getDemandIcon()"></i>
            <div class="demand-info">
              <h6 class="demand-title">Current Demand</h6>
              <div class="demand-level-display">
                <span class="level-text">{{ currentDemand.level | titlecase }}</span>
                <span *ngIf="config.showPercentage" class="level-percentage">
                  {{ currentDemand.percentage }}%
                </span>
              </div>
            </div>
            <div *ngIf="config.showTrend" class="trend-indicator">
              <i [class]="getTrendIcon()" class="trend-icon"></i>
              <small class="trend-text">{{ getTrendText() }}</small>
            </div>
          </div>
        </div>

        <div *ngIf="config.showRecommendation || config.showFactors" class="card-body">
          <!-- Recommendation -->
          <div *ngIf="config.showRecommendation" class="recommendation-section">
            <h6 class="section-title">
              <i class="fas fa-lightbulb me-1"></i>
              Recommendation
            </h6>
            <p class="recommendation-text">{{ currentDemand.recommendation }}</p>
          </div>

          <!-- Demand Factors -->
          <div *ngIf="config.showFactors && currentDemand.factors.length" class="factors-section">
            <h6 class="section-title">
              <i class="fas fa-chart-line me-1"></i>
              Influencing Factors
            </h6>
            <ul class="factors-list">
              <li *ngFor="let factor of currentDemand.factors" class="factor-item">
                {{ factor }}
              </li>
            </ul>
          </div>

          <!-- Last Updated -->
          <div class="last-updated">
            <small class="text-muted">
              <i class="fas fa-clock me-1"></i>
              Last updated: {{ getLastUpdatedDisplay() }}
            </small>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="isLoading" class="demand-loading" [ngClass]="'demand-loading-' + config.size">
        <i class="fas fa-spinner fa-spin"></i>
        <span class="loading-text">Loading demand...</span>
      </div>

      <!-- Error State -->
      <div *ngIf="hasError" class="demand-error" [ngClass]="'demand-error-' + config.size">
        <i class="fas fa-exclamation-triangle"></i>
        <span class="error-text">Unable to load demand</span>
        <button class="btn btn-sm btn-outline-secondary ms-2" (click)="refreshDemand()">
          <i class="fas fa-redo"></i>
        </button>
      </div>
    </div>
  `,
  styleUrls: ['./demand-indicator.component.scss']
})
export class DemandIndicatorComponent implements OnInit, OnDestroy {
  @Input() lotId?: string;
  @Input() config: DemandIndicatorConfig = {
    showPercentage: true,
    showTrend: true,
    showRecommendation: false,
    showFactors: false,
    autoRefresh: true,
    refreshInterval: 30, // 30 seconds
    size: 'medium',
    style: 'badge'
  };

  currentDemand: DemandInfo = {
    level: DemandLevel.MEDIUM,
    description: 'Normal demand',
    percentage: 65,
    trend: 'stable',
    lastUpdated: new Date().toISOString(),
    factors: [],
    recommendation: 'Standard booking recommended'
  };

  isLoading = false;
  hasError = false;
  private destroy$ = new Subject<void>();
  private apiUrl = environment.apiUrl;

  // Utility access
  DurationUtils = DurationUtils;

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadDemandInfo();
    
    if (this.config.autoRefresh) {
      this.setupAutoRefresh();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadDemandInfo(): void {
    this.isLoading = true;
    this.hasError = false;

    // Build API URL - use lot-specific or global demand
    const url = this.lotId 
      ? `${this.apiUrl}/realtime/lot/${this.lotId}/availability`
      : `${this.apiUrl}/realtime/current-availability`;

    this.http.get<any>(url)
      .pipe(
        takeUntil(this.destroy$),
        catchError(error => {
          console.error('Demand info error:', error);
          this.hasError = true;
          this.isLoading = false;
          // Return empty data on error
          return of({ occupancy_rate: 0, demand_level: 'low' });
        })
      )
      .subscribe(response => {
        this.processDemandResponse(response);
        this.isLoading = false;
        this.cdr.detectChanges();
      });
  }

  private processDemandResponse(response: any): void {
    // Extract demand info from API response
    const occupancyRate = response.occupancy_rate || 65;
    const demandLevel = this.calculateDemandLevel(occupancyRate);
    
    this.currentDemand = {
      level: demandLevel,
      description: this.getDemandDescription(demandLevel),
      percentage: Math.round(occupancyRate),
      trend: this.calculateTrend(occupancyRate),
      lastUpdated: new Date().toISOString(),
      factors: this.extractDemandFactors(response),
      recommendation: this.generateRecommendation(demandLevel, occupancyRate)
    };
  }

  private calculateDemandLevel(occupancyRate: number): DemandLevel {
    if (occupancyRate >= 90) return DemandLevel.PEAK;
    if (occupancyRate >= 75) return DemandLevel.HIGH;
    if (occupancyRate >= 40) return DemandLevel.MEDIUM;
    return DemandLevel.LOW;
  }

  private getDemandDescription(level: DemandLevel): string {
    switch (level) {
      case DemandLevel.LOW:
        return 'Low demand';
      case DemandLevel.MEDIUM:
        return 'Normal demand';
      case DemandLevel.HIGH:
        return 'High demand';
      case DemandLevel.PEAK:
        return 'Peak demand';
      default:
        return 'Unknown demand';
    }
  }

  private calculateTrend(currentRate: number): 'rising' | 'falling' | 'stable' {
    // Simple trend calculation - in real implementation, compare with historical data
    const hour = new Date().getHours();
    
    // Peak hours: 8-10 AM, 5-7 PM
    if ((hour >= 8 && hour <= 10) || (hour >= 17 && hour <= 19)) {
      return 'rising';
    }
    
    // Off-peak hours: 11 PM - 6 AM
    if (hour >= 23 || hour <= 6) {
      return 'falling';
    }
    
    return 'stable';
  }

  private extractDemandFactors(response: any): string[] {
    const factors: string[] = [];
    
    if (response.weather) {
      factors.push(`Weather: ${response.weather}`);
    }
    
    const hour = new Date().getHours();
    if (hour >= 8 && hour <= 10) {
      factors.push('Morning rush hour');
    } else if (hour >= 17 && hour <= 19) {
      factors.push('Evening rush hour');
    } else if (hour >= 12 && hour <= 14) {
      factors.push('Lunch time peak');
    }
    
    if (response.events) {
      factors.push('Special events nearby');
    }
    
    return factors;
  }

  private generateRecommendation(level: DemandLevel, occupancyRate: number): string {
    switch (level) {
      case DemandLevel.LOW:
        return 'Great time to book! Plenty of spaces available.';
      case DemandLevel.MEDIUM:
        return 'Standard booking recommended. Good availability.';
      case DemandLevel.HIGH:
        return 'Book soon! Limited spaces available.';
      case DemandLevel.PEAK:
        return 'High demand! Consider alternative times or locations.';
      default:
        return 'Standard booking recommended.';
    }
  }


  private setupAutoRefresh(): void {
    interval(this.config.refreshInterval * 1000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        this.loadDemandInfo();
      });
  }

  // Template methods
  getContainerClasses(): string {
    return `demand-${this.config.size} demand-style-${this.config.style}`;
  }

  getDemandClasses(): string {
    return `demand-${this.currentDemand.level}`;
  }

  getDemandIcon(): string {
    return DurationUtils.getDemandLevelIcon(this.currentDemand.level);
  }

  getTrendIcon(): string | null {
    switch (this.currentDemand.trend) {
      case 'rising':
        return 'fas fa-arrow-up text-warning';
      case 'falling':
        return 'fas fa-arrow-down text-success';
      case 'stable':
        return 'fas fa-minus text-info';
      default:
        return null;
    }
  }

  getTrendText(): string {
    switch (this.currentDemand.trend) {
      case 'rising':
        return 'Rising';
      case 'falling':
        return 'Falling';
      case 'stable':
        return 'Stable';
      default:
        return '';
    }
  }

  getLastUpdatedDisplay(): string {
    const lastUpdated = new Date(this.currentDemand.lastUpdated);
    const now = new Date();
    const diffSeconds = Math.floor((now.getTime() - lastUpdated.getTime()) / 1000);
    
    if (diffSeconds < 60) {
      return 'Just now';
    } else if (diffSeconds < 3600) {
      const minutes = Math.floor(diffSeconds / 60);
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else {
      return lastUpdated.toLocaleTimeString();
    }
  }

  refreshDemand(): void {
    this.loadDemandInfo();
  }
}
