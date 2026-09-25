import { formatJalaliDate, formatJalaliDateTime } from "../../utils/jalaliDate";
import type { AccountType } from "../../services/accountingService";

export const ACCOUNT_TYPE_LABELS: Record<AccountType, string> = {
  asset: "دارایی",
  liability: "بدهی",
  equity: "سرمایه",
  revenue: "درآمد",
  expense: "هزینه",
};

export function money(value: string | number | null | undefined): string {
  const amount = Number(value ?? 0);
  if (!Number.isFinite(amount)) return "۰";
  return new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 2 }).format(amount);
}

export function isoToJalali(value: string | null | undefined): string {
  return value ? formatJalaliDate(value) : "-";
}

export function isoToJalaliDateTime(value: string | null | undefined): string {
  return value ? formatJalaliDateTime(value) : "-";
}

export function localIsoDate(value: string): string | undefined {
  if (!value) return undefined;
  const [y, m, d] = value.split("-").map(Number);
  if (!y || !m || !d) return undefined;
  return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}
