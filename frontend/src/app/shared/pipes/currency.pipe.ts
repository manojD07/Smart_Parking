import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'appCurrency',
  standalone: true
})
export class AppCurrencyPipe implements PipeTransform {
  transform(value: number | null | undefined): string {
    if (value === null || value === undefined || isNaN(value)) {
      return '$0.00';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  }
}
