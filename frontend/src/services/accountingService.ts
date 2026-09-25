import api from "./api";
import type { ApiListResponse } from "./apiTypes";

export type AccountType = "asset" | "liability" | "equity" | "revenue" | "expense";
export type JournalStatus = "posted" | "reversed";
export type PartyType = "customer" | "supplier" | "cashbox" | "user" | "";

export interface Account {
  id: number;
  store: number;
  parent: number | null;
  code: string;
  name: string;
  account_type: AccountType;
  account_type_label: string;
  is_group: boolean;
  is_system: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountingPeriod {
  id: number;
  store: number;
  name: string;
  start_date: string;
  end_date: string;
  is_closed: boolean;
  created_at: string;
  closed_at: string | null;
  closed_by: number | null;
}

export interface JournalLineItem {
  id: number;
  account: number;
  account_code: string;
  account_name: string;
  debit: string | number;
  credit: string | number;
  description: string;
  party_type: PartyType;
  party_id: number | null;
}

export interface JournalEntry {
  id: number;
  store: number;
  period: number;
  entry_number: number;
  entry_date: string;
  description: string;
  status: JournalStatus;
  source_type: string;
  source_id: number | null;
  source_key: string;
  reversal_of: number | null;
  created_by: number;
  created_at: string;
  line_items: JournalLineItem[];
}

export interface TrialBalanceRow {
  account_id: number;
  account__code: string;
  account__name: string;
  account__account_type: AccountType;
  debit: string | number;
  credit: string | number;
  balance: string | number;
}

export interface GeneralLedgerRow {
  entry_id: number;
  entry_number: number;
  date: string;
  description: string;
  account_id: number;
  account_code: string;
  account_name: string;
  debit: string | number;
  credit: string | number;
  balance: string | number;
}

export interface ProfitLossReport {
  revenue: string | number;
  expense: string | number;
  net_profit: string | number;
}

export interface BalanceSheetAccountRow extends TrialBalanceRow {
  balance: string | number;
}

export interface BalanceSheetReport {
  assets: string | number;
  liabilities: string | number;
  equity: string | number;
  current_profit: string | number;
  liabilities_plus_equity: string | number;
  balanced: boolean;
  accounts: BalanceSheetAccountRow[];
}

export interface AccountingListParams {
  store: number;
  start_date?: string;
  end_date?: string;
}

const list = <T,>(value: ApiListResponse<T>): T[] => (Array.isArray(value) ? value : value.results);

function cleanParams<T extends object>(params: T): Record<string, string | number> {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== "")
  ) as Record<string, string | number>;
}

export async function setupAccounting(store: number) {
  return (await api.post<{ store: number; status: string }>("/accounting/setup/", { store })).data;
}

export async function syncAccounting(store: number) {
  return (await api.post<{ store: number; status: string }>("/accounting/sync/", { store })).data;
}

export async function listAccounts(store: number): Promise<Account[]> {
  const response = await api.get<ApiListResponse<Account>>("/accounting/accounts/", { params: { store } });
  return list(response.data);
}

export async function createAccount(data: {
  store: number;
  parent: number | null;
  code: string;
  name: string;
  account_type: AccountType;
  is_group: boolean;
  is_active: boolean;
}) {
  return (await api.post<Account>("/accounting/accounts/", data)).data;
}

export async function updateAccount(id: number, data: Partial<Pick<Account, "parent" | "code" | "name" | "account_type" | "is_group" | "is_active">>) {
  return (await api.patch<Account>(`/accounting/accounts/${id}/`, data)).data;
}

export async function deleteAccount(id: number) {
  await api.delete(`/accounting/accounts/${id}/`);
}

export async function listPeriods(store: number): Promise<AccountingPeriod[]> {
  const response = await api.get<ApiListResponse<AccountingPeriod>>("/accounting/periods/", { params: { store } });
  return list(response.data);
}

export async function createPeriod(data: { store: number; name: string; start_date: string; end_date: string }) {
  return (await api.post<AccountingPeriod>("/accounting/periods/", data)).data;
}

export async function updatePeriod(id: number, data: Partial<Pick<AccountingPeriod, "name" | "start_date" | "end_date">>) {
  return (await api.patch<AccountingPeriod>(`/accounting/periods/${id}/`, data)).data;
}

export async function deletePeriod(id: number) {
  await api.delete(`/accounting/periods/${id}/`);
}

export async function closePeriod(id: number) {
  return (await api.post<AccountingPeriod>(`/accounting/periods/${id}/close/`)).data;
}

export async function listJournalEntries(params: AccountingListParams): Promise<JournalEntry[]> {
  const response = await api.get<ApiListResponse<JournalEntry>>("/accounting/entries/", {
    params: cleanParams(params),
  });
  return list(response.data);
}

export async function createJournalEntry(data: {
  store: number;
  entry_date: string;
  description: string;
  lines: Array<{
    account: number;
    debit: string;
    credit: string;
    description?: string;
    party_type?: PartyType;
    party_id?: number | null;
  }>;
}) {
  return (await api.post<JournalEntry>("/accounting/entries/create/", data)).data;
}

export async function reverseJournalEntry(id: number) {
  return (await api.post<JournalEntry>(`/accounting/entries/${id}/reverse/`)).data;
}

export async function getTrialBalance(params: AccountingListParams): Promise<TrialBalanceRow[]> {
  return (await api.get<TrialBalanceRow[]>("/accounting/trial-balance/", { params: cleanParams(params) })).data;
}

export async function getGeneralLedger(params: AccountingListParams & { account?: number }): Promise<GeneralLedgerRow[]> {
  return (await api.get<GeneralLedgerRow[]>("/accounting/general-ledger/", { params: cleanParams(params) })).data;
}

export async function getProfitLoss(params: AccountingListParams): Promise<ProfitLossReport> {
  return (await api.get<ProfitLossReport>("/accounting/profit-loss/", { params: cleanParams(params) })).data;
}

export async function getBalanceSheet(store: number, as_of_date?: string): Promise<BalanceSheetReport> {
  return (await api.get<BalanceSheetReport>("/accounting/balance-sheet/", { params: cleanParams({ store, as_of_date }) })).data;
}
