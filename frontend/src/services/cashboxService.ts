import api from "./api";
import type { ApiListResponse } from "./apiTypes";
export interface CashBox { id:number; name:string; store:number; balance:string; description?:string; }
export async function listCashBoxes(storeId:number):Promise<CashBox[]>{const r=await api.get<ApiListResponse<CashBox>>("/sales/cashboxes/",{params:{store:storeId}});return Array.isArray(r.data)?r.data:r.data.results;}
