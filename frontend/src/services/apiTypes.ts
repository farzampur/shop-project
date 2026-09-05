export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type ApiListResponse<T> = T[] | PaginatedResponse<T>;

export function extractResults<T>(response: ApiListResponse<T>): T[] {
  return Array.isArray(response) ? response : response.results;
}
