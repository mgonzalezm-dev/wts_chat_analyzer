export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  meta?: {
    timestamp: string;
    request_id: string;
  };
}

export interface ApiError {
  code: string;
  message: string;
  details?: Array<{
    field: string;
    message: string;
  }>;
}

export interface PaginationParams {
  page: number;
  limit: number;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  pages: number;
  has_next?: boolean;
  has_prev?: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationMeta;
}

export interface SearchParams extends PaginationParams {
  search?: string;
}

export interface DateRangeParams {
  date_from?: string;
  date_to?: string;
}

export interface SortParams {
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}