export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  success?: boolean;
  errors?: string[];
}

export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface SuccessResponse {
  message: string;
  success?: boolean;
}

export interface ErrorResponse {
  detail: string;
  message?: string;
  errors?: string[];
  status_code?: number;
}

export interface LoadingState {
  loading: boolean;
  error?: string | null;
}

export interface SelectOption {
  value: any;
  label: string;
  disabled?: boolean;
}
