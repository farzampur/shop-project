export type StoreRole = "manager" | "seller" | "cashier" | "warehouse";

export interface StoreAccess {
  id: number;
  name: string;
  code: string;
  phone: string;
  address: string;
  is_active: boolean;
  role: StoreRole;
  role_display: string;
}

export interface CurrentUser {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_staff: boolean;
  is_superuser: boolean;
  stores: StoreAccess[];
}
