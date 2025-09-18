import { Component, Input, OnInit, OnChanges, SimpleChanges, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface PieChartData {
  label: string;
  value: number;
  color: string;
  icon?: string;
}

@Component({
  selector: 'app-pie-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="pie-chart-container">
      <!-- SVG Pie Chart -->
      <div class="chart-wrapper">
        <svg #pieChart [attr.width]="svgWidth" [attr.height]="svgHeight" [attr.viewBox]="'0 0 ' + svgWidth + ' ' + svgHeight">
          <!-- Background circle -->
          <circle 
            [attr.cx]="center" 
            [attr.cy]="centerY" 
            [attr.r]="radius"
            fill="none"
            stroke="#f1f3f4"
            [attr.stroke-width]="strokeWidth">
          </circle>
          
          <!-- Pie segments -->
          <g *ngFor="let segment of segments; trackBy: trackByLabel">
            <path 
              [attr.d]="segment.path"
              [attr.fill]="segment.color"
              [attr.stroke]="showBorder ? '#ffffff' : 'none'"
              [attr.stroke-width]="showBorder ? '2' : '0'"
              class="pie-segment"
              [attr.data-label]="segment.label"
              (mouseenter)="onSegmentHover(segment)"
              (mouseleave)="onSegmentLeave()"
              [style.cursor]="'pointer'">
            </path>
          </g>
          
          <!-- Center circle for donut chart -->
          <circle 
            *ngIf="donut"
            [attr.cx]="center" 
            [attr.cy]="centerY" 
            [attr.r]="innerRadius"
            fill="white">
          </circle>
          
          <!-- Center text for donut chart -->
          <g *ngIf="donut && centerText">
            <text 
              [attr.x]="center" 
              [attr.y]="centerY - 5" 
              text-anchor="middle" 
              class="center-text-main">
              {{ centerText.main }}
            </text>
            <text 
              [attr.x]="center" 
              [attr.y]="centerY + 15" 
              text-anchor="middle" 
              class="center-text-sub">
              {{ centerText.sub }}
            </text>
          </g>

          <!-- Segment Labels around the circle -->
          <g *ngFor="let segment of segments; trackBy: trackByLabel">
            <g *ngIf="showLabelsAroundCircle && segment.percentage >= minPercentageForLabel">
              <!-- Leader line from segment to label -->
              <line 
                [attr.x1]="segment.labelLineStart.x"
                [attr.y1]="segment.labelLineStart.y"
                [attr.x2]="segment.labelLineEnd.x"
                [attr.y2]="segment.labelLineEnd.y"
                [attr.stroke]="segment.color"
                stroke-width="2"
                stroke-opacity="0.6"
                class="label-line">
              </line>
              
              
              <!-- Label text -->
              <text 
                [attr.x]="segment.labelText.x"
                [attr.y]="segment.labelText.y"
                [attr.text-anchor]="segment.labelText.anchor"
                class="segment-label-main">
                {{ segment.label }}
              </text>
              
              <!-- Value and percentage text -->
              <text 
                [attr.x]="segment.labelText.x"
                [attr.y]="segment.labelText.y + 12"
                [attr.text-anchor]="segment.labelText.anchor"
                class="segment-label-sub">
                {{ segment.value.toLocaleString() }} ({{ segment.percentage.toFixed(1) }}%)
              </text>
            </g>
          </g>
        </svg>
        
        <!-- Hover tooltip -->
        <div 
          *ngIf="hoveredSegment"
          class="tooltip"
          [style.left.px]="tooltipX"
          [style.top.px]="tooltipY">
          <div class="tooltip-content">
            <div class="d-flex align-items-center mb-1">
              <div 
                class="color-dot me-2"
                [style.background-color]="hoveredSegment.color">
              </div>
              <strong>{{ hoveredSegment.label }}</strong>
            </div>
            <div>{{ hoveredSegment.value.toLocaleString() }} ({{ hoveredSegment.percentage.toFixed(1) }}%)</div>
          </div>
        </div>
      </div>
      
      <!-- Legend (only show when labels are not around circle) -->
      <div *ngIf="showLegend && !showLabelsAroundCircle" class="legend" [class.legend-horizontal]="legendHorizontal">
        <div 
          *ngFor="let item of data; trackBy: trackByLabel"
          class="legend-item"
          [class.legend-item-horizontal]="legendHorizontal">
          <div class="d-flex align-items-center" [class.flex-column]="!legendHorizontal && showValues">
            <div class="d-flex align-items-center">
              <i *ngIf="item.icon" class="fas me-2" [class]="item.icon" [style.color]="item.color"></i>
              <div 
                class="legend-color me-2"
                [style.background-color]="item.color">
              </div>
              <span class="legend-label">{{ item.label }}</span>
            </div>
            <div *ngIf="showValues" class="legend-values" [class.ms-auto]="legendHorizontal">
              <span class="legend-value">{{ item.value.toLocaleString() }}</span>
              <span class="legend-percentage">({{ getPercentage(item.value).toFixed(1) }}%)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .pie-chart-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
    }

    .chart-wrapper {
      position: relative;
      display: flex;
      justify-content: center;
      align-items: center;
    }

    .pie-segment {
      transition: all 0.3s ease;
      transform-origin: center;
    }

    .pie-segment:hover {
      filter: brightness(1.1);
      transform: scale(1.05);
    }

    .center-text-main {
      font-size: 18px;
      font-weight: 700;
      fill: #495057;
    }

    .center-text-sub {
      font-size: 12px;
      font-weight: 500;
      fill: #6c757d;
    }

    .label-line {
      opacity: 0.7;
      transition: opacity 0.3s ease;
    }


    .segment-label-main {
      font-size: 12px;
      font-weight: 800;
      fill: #333;
      stroke: white;
      stroke-width: 3;
      paint-order: stroke fill;
    }

    .segment-label-sub {
      font-size: 10px;
      font-weight: 700;
      fill: #666;
      stroke: white;
      stroke-width: 2.5;
      paint-order: stroke fill;
    }

    .tooltip {
      position: absolute;
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 0.5rem;
      border-radius: 4px;
      font-size: 0.875rem;
      pointer-events: none;
      z-index: 1000;
      white-space: nowrap;
    }

    .tooltip-content {
      min-width: 120px;
    }

    .color-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    .legend {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      max-width: 100%;
    }

    .legend-horizontal {
      flex-direction: row;
      flex-wrap: wrap;
      justify-content: center;
      gap: 1rem;
    }

    .legend-item {
      display: flex;
      align-items: center;
      min-width: 0;
    }

    .legend-item-horizontal {
      flex: 0 0 auto;
    }

    .legend-color {
      width: 12px;
      height: 12px;
      border-radius: 2px;
      flex-shrink: 0;
    }

    .legend-label {
      font-size: 0.875rem;
      font-weight: 500;
      color: #495057;
      text-transform: capitalize;
    }

    .legend-values {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      margin-left: 0.5rem;
    }

    .legend-value {
      font-size: 0.875rem;
      font-weight: 600;
      color: #495057;
    }

    .legend-percentage {
      font-size: 0.75rem;
      color: #6c757d;
    }

    @media (max-width: 768px) {
      .legend {
        max-width: 300px;
      }
      
      .legend-horizontal {
        flex-direction: column;
        gap: 0.5rem;
      }
      
      .center-text-main {
        font-size: 16px;
      }
      
      .center-text-sub {
        font-size: 10px;
      }
    }
  `]
})
export class PieChartComponent implements OnInit, OnChanges {
  @Input() data: PieChartData[] = [];
  @Input() size: number = 200;
  @Input() strokeWidth: number = 40;
  @Input() donut: boolean = true;
  @Input() showLegend: boolean = true;
  @Input() legendHorizontal: boolean = false;
  @Input() showValues: boolean = true;
  @Input() showBorder: boolean = true;
  @Input() centerText?: { main: string; sub: string };
  @Input() showLabelsAroundCircle: boolean = false;
  @Input() minPercentageForLabel: number = 5; // Only show labels for segments >= 5%

  @ViewChild('pieChart') pieChartRef!: ElementRef<SVGElement>;

  segments: any[] = [];
  hoveredSegment: any = null;
  tooltipX = 0;
  tooltipY = 0;

  get center(): number {
    return this.showLabelsAroundCircle ? this.svgWidth / 2 : this.size / 2;
  }

  get centerY(): number {
    return this.showLabelsAroundCircle ? (this.svgHeight / 2) : this.size / 2;
  }

  get radius(): number {
    return (this.size - this.strokeWidth) / 2;
  }

  get innerRadius(): number {
    return this.donut ? this.radius * 0.6 : 0;
  }

  get total(): number {
    return this.data.reduce((sum, item) => sum + item.value, 0);
  }

  get svgWidth(): number {
    return this.showLabelsAroundCircle ? this.size + 120 : this.size;
  }

  get svgHeight(): number {
    return this.showLabelsAroundCircle ? this.size + 60 : this.size;
  }

  ngOnInit(): void {
    this.updateChart();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['data'] || changes['size'] || changes['strokeWidth']) {
      this.updateChart();
    }
  }

  private updateChart(): void {
    if (!this.data || this.data.length === 0) {
      this.segments = [];
      return;
    }

    let currentAngle = -90; // Start from top
    this.segments = [];
    const labelRadius = this.radius + 25; // Distance from center to label (closer)
    const labelLineRadius = this.radius + 5; // Distance to start of leader line (closer)

    this.data.forEach(item => {
      const percentage = (item.value / this.total) * 100;
      const angle = (item.value / this.total) * 360;
      
      const startAngle = currentAngle;
      const endAngle = currentAngle + angle;
      const midAngle = (startAngle + endAngle) / 2;
      
      const path = this.createArcPath(
        this.center,
        this.centerY,
        this.radius,
        this.innerRadius,
        startAngle,
        endAngle
      );

      // Calculate label positioning
      const midAngleRad = (midAngle * Math.PI) / 180;
      const labelLineStartX = this.center + labelLineRadius * Math.cos(midAngleRad);
      const labelLineStartY = this.centerY + labelLineRadius * Math.sin(midAngleRad);
      const labelLineEndX = this.center + labelRadius * Math.cos(midAngleRad);
      const labelLineEndY = this.centerY + labelRadius * Math.sin(midAngleRad);

      // Determine label position and anchor
      const isRightSide = midAngle > -90 && midAngle < 90;
      const labelPadding = 8;

      let labelTextX, labelTextAnchor;
      
      if (isRightSide) {
        labelTextX = labelLineEndX + labelPadding;
        labelTextAnchor = 'start';
      } else {
        labelTextX = labelLineEndX - labelPadding;
        labelTextAnchor = 'end';
      }

      this.segments.push({
        label: item.label,
        value: item.value,
        percentage,
        color: item.color,
        path,
        startAngle,
        endAngle,
        midAngle,
        labelLineStart: { x: labelLineStartX, y: labelLineStartY },
        labelLineEnd: { x: labelLineEndX, y: labelLineEndY },
        labelText: {
          x: labelTextX,
          y: labelLineEndY + 4,
          anchor: labelTextAnchor
        }
      });

      currentAngle += angle;
    });
  }

  private createArcPath(
    centerX: number,
    centerY: number,
    outerRadius: number,
    innerRadius: number,
    startAngle: number,
    endAngle: number
  ): string {
    const startAngleRad = (startAngle * Math.PI) / 180;
    const endAngleRad = (endAngle * Math.PI) / 180;

    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';

    const outerStartX = centerX + outerRadius * Math.cos(startAngleRad);
    const outerStartY = centerY + outerRadius * Math.sin(startAngleRad);
    const outerEndX = centerX + outerRadius * Math.cos(endAngleRad);
    const outerEndY = centerY + outerRadius * Math.sin(endAngleRad);

    if (innerRadius === 0) {
      // Pie chart (not donut)
      return [
        `M ${centerX} ${centerY}`,
        `L ${outerStartX} ${outerStartY}`,
        `A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${outerEndX} ${outerEndY}`,
        'Z'
      ].join(' ');
    } else {
      // Donut chart
      const innerStartX = centerX + innerRadius * Math.cos(startAngleRad);
      const innerStartY = centerY + innerRadius * Math.sin(startAngleRad);
      const innerEndX = centerX + innerRadius * Math.cos(endAngleRad);
      const innerEndY = centerY + innerRadius * Math.sin(endAngleRad);

      return [
        `M ${outerStartX} ${outerStartY}`,
        `A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${outerEndX} ${outerEndY}`,
        `L ${innerEndX} ${innerEndY}`,
        `A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${innerStartX} ${innerStartY}`,
        'Z'
      ].join(' ');
    }
  }

  onSegmentHover(segment: any): void {
    this.hoveredSegment = segment;
    
    // Position tooltip near mouse (simplified)
    this.tooltipX = this.center + 20;
    this.tooltipY = this.center - 20;
  }

  onSegmentLeave(): void {
    this.hoveredSegment = null;
  }

  getPercentage(value: number): number {
    return this.total > 0 ? (value / this.total) * 100 : 0;
  }

  trackByLabel(index: number, item: any): string {
    return item.label;
  }
}
