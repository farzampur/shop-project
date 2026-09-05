import api from "./api";
import type { ApiListResponse } from "./apiTypes";
export interface Customer { id:number; store:number; first_name:string; last_name:string; mobile:string; address:string; }
export async function listCustomers(storeId:number):Promise<Customer[]>{const r=await api.get<ApiListResponse<Customer>>("/sales/customers/",{params:{store:storeId}});return Array.isArray(r.data)?r.data:r.data.results;}
export async function createCustomer(data:Omit<Customer,"id">):Promise<Customer>{const r=await api.post<Customer>("/sales/customers/",data);return r.data;}
