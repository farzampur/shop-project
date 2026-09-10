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
  | "inventory"
  | "purchases"
  | "suppliers"
  | "sales"
  | "customers"
  | "cashbox"
  | "reports"
  | "cashClose"
  | "audit"
  | "users"
  | "stores"
  | "transfers"
  | "pricing";

export const ROUTE_ROLES: Record<AppRouteKey, readonly StoreRole[]> = {
  dashboard: ALL_ROLES,
  categories: [ROLE.manager, ROLE.warehouse],
  products: [ROLE.manager, ROLE.warehouse],
  inventory: [ROLE.manager, ROLE.warehouse],
  purchases: [ROLE.manager, ROLE.warehouse],
  suppliers: [ROLE.manager, ROLE.warehouse],
  sales: [ROLE.manager, ROLE.seller, ROLE.cashier],
  customers: [ROLE.manager, ROLE.seller, ROLE.cashier],
  cashbox: [ROLE.manager, ROLE.cashier],
  reports: [ROLE.manager],
  cashClose: [ROLE.manager, ROLE.cashier],
  audit: [ROLE.manager],
  users: [ROLE.manager],
  stores: [ROLE.manager],
  transfers: [ROLE.manager, ROLE.warehouse],
  pricing: [ROLE.manager],
};

export function canAccessRoute(
  route: AppRouteKey,
  role: StoreRole | null,
): boolean {
  return role !== null && ROUTE_ROLES[route].includes(role);
}
