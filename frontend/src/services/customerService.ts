import api from "./api";
import type { ApiListResponse } from "./apiTypes";
export interface Customer { id:number; store:number; first_name:string; last_name:string; mobile:string; address:string; name?:string; phone?:string; }
export async function listCustomers(storeId:number):Promise<Customer[]>{const r=await api.get<ApiListResponse<Customer>>("/sales/customers/",{params:{store:storeId}});return Array.isArray(r.data)?r.data:r.data.results;}
export async function createCustomer(data:Omit<Customer,"id">):Promise<Customer>{const r=await api.post<Customer>("/sales/customers/",data);return r.data;}

export interface CustomerBalance { customer_id:number; customer_name:string; sales:string|number; payments:string|number; balance:string|number; }
export async function getCustomerBalance(customerId:number):Promise<CustomerBalance>{ const r=await api.get<CustomerBalance>(`/sales/customers/${customerId}/balance/`); return r.data; }
