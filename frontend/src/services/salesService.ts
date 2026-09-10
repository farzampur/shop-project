import api from "./api";
import type { ApiListResponse } from "./apiTypes";

export type PaymentMethod = "cash" | "card" | "credit";
export type OrderStatus = "pending" | "confirmed" | "paid" | "cancelled";

export interface CartItem { id:number; product:number; product_name:string; price_type:"retail"|"wholesale"|"special"; purchase_price?:string; quantity:string; unit_price:string; discount_percent:string; discount_amount:string; final_unit_price:string; total_price_before_discount:string; total_discount_amount:string; total_price:string; }
export interface Cart { id:number; store:number; store_name:string; customer:number|null; items:CartItem[]; total_before_discount:string; total_discount:string; total_price:string; subtotal_price?:string; discount_amount?:string; }
export interface Payment { id:number; method:PaymentMethod; amount:string; cashbox:number|null; created_at:string; }
export interface OrderItem { id:number; product_id:number; product_name:string; quantity:string; unit_price:string; price_type:"retail"|"wholesale"|"special"; price_type_display?:string; discount_percent:string; total_price:string; }
export interface Order { id:number; status:OrderStatus; total_before_discount:string; total_discount:string; total_price:string; subtotal_price?:string; discount_amount?:string; created_at:string; items:OrderItem[]; payments:Payment[]; customer:number|null; customer_name:string|null; cancellation?:{id:number;cancelled_by:number;cancelled_by_username:string;cancelled_at:string;reason:string}|null; }
export interface CheckoutPayment { method:PaymentMethod; amount:string; cashbox_id?:number|null; }
function unwrap<T>(data: ApiListResponse<T>): T[] { return Array.isArray(data) ? data : data.results; }
export async function listCarts(storeId:number):Promise<Cart[]> { const r=await api.get<ApiListResponse<Cart>>("/sales/carts/",{params:{store:storeId}}); return unwrap(r.data); }
export async function createCart(storeId:number, customer?:number|null):Promise<Cart> { const r=await api.post<Cart>("/sales/carts/",{store:storeId,...(customer ? {customer}: {})}); return r.data; }
export async function updateCartCustomer(cartId:number, customer:number|null):Promise<Cart> { const r=await api.patch<Cart>(`/sales/carts/${cartId}/`,{customer}); return r.data; }
export async function addCartItem(cartId:number,data:{product?:number;barcode?:string;quantity:string|number;discount_percent:string|number;price_type?:"retail"|"wholesale"|"special"}):Promise<CartItem>{const r=await api.post<CartItem>(`/sales/carts/${cartId}/items/`,data);return r.data;}
export async function updateCartItem(cartId:number,itemId:number,data:{quantity:string|number;discount_percent:string|number}):Promise<CartItem>{const r=await api.patch<CartItem>(`/sales/carts/${cartId}/items/${itemId}/`,data);return r.data;}
export async function deleteCartItem(cartId:number,itemId:number):Promise<void>{await api.delete(`/sales/carts/${cartId}/items/${itemId}/`);}
export async function checkoutCart(cartId:number,payments:CheckoutPayment[]){const r=await api.post(`/sales/checkout/`,{cart_id:cartId,payments});return r.data as {id:number;status:OrderStatus;total_before_discount:string;total_discount:string;total_price:string};}
export async function listOrders(storeId:number):Promise<Order[]>{const r=await api.get<ApiListResponse<Order>>("/sales/orders/",{params:{store:storeId}});return unwrap(r.data);}
export async function changeOrderStatus(orderId:number,status:"confirmed"|"cancelled",reason=""){const r=await api.post(`/sales/orders/${orderId}/change_status/`,{status,reason});return r.data as {id:number;status:OrderStatus};}
export async function payOrder(orderId:number,payments:CheckoutPayment[]){const r=await api.post(`/sales/orders/${orderId}/pay/`,{payments});return r.data as {id:number;status:OrderStatus};}
export function getInvoiceUrl(orderId:number):string{return `${api.defaults.baseURL}/sales/orders/${orderId}/invoice/`;}
export async function downloadInvoicePdf(orderId:number):Promise<Blob>{const r=await api.get(`/sales/orders/${orderId}/invoice/`,{responseType:"blob"});return r.data as Blob;}
export async function downloadThermalReceiptPdf(orderId:number):Promise<Blob>{const r=await api.get(`/sales/orders/${orderId}/thermal-receipt/`,{responseType:"blob"});return r.data as Blob;}

export { checkoutCart as checkout };
