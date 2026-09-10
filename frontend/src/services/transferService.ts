import api from "./api";
import type { ApiListResponse } from "./apiTypes";

export interface StockTransferItem { id:number; product:number; product_name:string; barcode?:string; quantity:string; }
export interface StockTransfer {
  id:number; source_store:number; source_store_name:string; destination_store:number; destination_store_name:string;
  status:string; status_display:string; created_by:number; created_by_username:string; approved_by?:number|null;
  notes:string; created_at:string; updated_at:string; shipped_at?:string|null; received_at?:string|null; items:StockTransferItem[];
}
function list<T>(data:ApiListResponse<T>):T[]{ return Array.isArray(data)?data:data.results; }
export async function listTransfers(storeId:number){ const r=await api.get<ApiListResponse<StockTransfer>>("/products/stock-transfers/",{params:{store:storeId}}); return list(r.data); }
export async function createTransfer(sourceStore:number,destinationStore:number,product:number,quantity:string,notes:string){
  const r=await api.post<StockTransfer>("/products/stock-transfers/",{source_store:sourceStore,destination_store:destinationStore,notes,items:[{product,quantity}]}); return r.data;
}
export async function approveTransfer(id:number){return (await api.post<StockTransfer>(`/products/stock-transfers/${id}/approve/`)).data;}
export async function shipTransfer(id:number){return (await api.post<StockTransfer>(`/products/stock-transfers/${id}/ship/`)).data;}
export async function receiveTransfer(id:number){return (await api.post<StockTransfer>(`/products/stock-transfers/${id}/receive/`)).data;}
export async function cancelTransfer(id:number){return (await api.post<StockTransfer>(`/products/stock-transfers/${id}/cancel/`)).data;}
