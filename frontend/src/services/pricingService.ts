import api from "./api";
import type {ApiListResponse} from "./apiTypes";
export type PriceType="retail"|"wholesale"|"special";
export interface ProductPrice {id:number;product:number;product_name:string;store:number;store_name:string;price_type:PriceType;price_type_display:string;amount:string;effective_from:string;effective_to?:string|null;is_active:boolean;is_current?:boolean;created_by:number;created_by_username:string;created_at:string;updated_at:string;}
const list=<T,>(data:ApiListResponse<T>):T[]=>Array.isArray(data)?data:data.results;
export async function listPrices(storeId:number,productId?:number,active=false){const r=await api.get<ApiListResponse<ProductPrice>>("/products/prices/",{params:{store:storeId,...(productId?{product:productId}:{}),...(active?{active:1}:{})}});return list(r.data);}
export async function createPrice(payload:Pick<ProductPrice,"product"|"store"|"price_type"|"amount"> & {effective_from?:string;effective_to?:string|null;is_active?:boolean}){return (await api.post<ProductPrice>("/products/prices/",payload)).data;}
export async function updatePrice(id:number,payload:Partial<ProductPrice>){return (await api.patch<ProductPrice>(`/products/prices/${id}/`,payload)).data;}
export async function deletePrice(id:number){await api.delete(`/products/prices/${id}/`);}
