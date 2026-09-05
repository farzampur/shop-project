import type { StoreRole } from "./authTypes";

export const ROLE = {
  manager: "manager",
  seller: "seller",
  cashier: "cashier",
  warehouse: "warehouse",
} as const satisfies Record<string, StoreRole>;

export const ALL_ROLES: readonly StoreRole[] = [
  ROLE.manager,
  ROLE.seller,
  ROLE.cashier,
  ROLE.warehouse,
];

/**
 * Frontend navigation policy mirrors the backend's coarse-grained store role
 * capabilities. Backend permissions remain the security authority.
 */
export type AppRouteKey =
  | "dashboard"
  | "categories"
  | "products"
  | "purchases"
  | "sales"
  | "customers"
  | "cashbox"
  | "reports";

export const ROUTE_ROLES: Record<AppRouteKey, readonly StoreRole[]> = {
  dashboard: ALL_ROLES,
  categories: ALL_ROLES,
  products: ALL_ROLES,
  purchases: [ROLE.manager, ROLE.warehouse],
  sales: [ROLE.manager, ROLE.seller, ROLE.cashier],
  customers: [ROLE.manager, ROLE.seller, ROLE.cashier],
  cashbox: [ROLE.manager, ROLE.cashier],
  reports: ALL_ROLES,
};

export function canAccessRoute(
  route: AppRouteKey,
  role: StoreRole | null,
): boolean {
  return role !== null && ROUTE_ROLES[route].includes(role);
}
