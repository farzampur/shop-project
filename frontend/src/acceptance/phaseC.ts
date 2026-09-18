export type AcceptanceStage = "C1" | "C2" | "C3";

export interface AcceptanceScenario {
  id: string;
  stage: AcceptanceStage;
  title: string;
  checkpoints: string[];
}

export const phaseCAcceptanceScenarios: AcceptanceScenario[] = [
  {
    id: "C1-01",
    stage: "C1",
    title: "ورود و Store فعال",
    checkpoints: ["Login", "Dashboard", "Store فعال", "Role-based menu"],
  },
  {
    id: "C1-02",
    stage: "C1",
    title: "خرید تا دریافت و Batch",
    checkpoints: ["Purchase", "Receive", "Inventory", "Batch"],
  },
  {
    id: "C1-03",
    stage: "C1",
    title: "فروش با FIFO",
    checkpoints: ["Inventory", "Sale", "FIFO", "Price/cost snapshot"],
  },
  {
    id: "C1-04",
    stage: "C1",
    title: "Return/Cancel و آثار مالی",
    checkpoints: ["Sale", "Return/Cancel", "Stock", "Financial records"],
  },
  {
    id: "C1-05",
    stage: "C1",
    title: "پرداخت مشتری",
    checkpoints: ["Customer", "Payment", "CashBox", "Ledger"],
  },
  {
    id: "C1-06",
    stage: "C1",
    title: "انتقال بین Storeها",
    checkpoints: ["Source", "Destination", "Batch", "Inventory"],
  },
  {
    id: "C1-07",
    stage: "C1",
    title: "گزارش‌ها",
    checkpoints: ["Sales report", "Inventory", "Profit", "Financial report"],
  },
  {
    id: "C1-08",
    stage: "C1",
    title: "Session recovery",
    checkpoints: ["Logout", "Login", "Access token", "Active Store"],
  },
  {
    id: "C2-01",
    stage: "C2",
    title: "Auth ↔ Store ↔ Role",
    checkpoints: ["ProtectedRoute", "Identity", "StoreContext", "RoleRoute"],
  },
  {
    id: "C2-02",
    stage: "C2",
    title: "Purchase ↔ Inventory",
    checkpoints: ["Receive", "Batch", "Inventory quantity"],
  },
  {
    id: "C2-03",
    stage: "C2",
    title: "Sales ↔ Finance",
    checkpoints: ["FIFO", "Order", "CashBox", "Customer Ledger"],
  },
  {
    id: "C2-04",
    stage: "C2",
    title: "Transfer ↔ Reports",
    checkpoints: ["Source stock", "Destination stock", "Batch history", "Reports"],
  },
  {
    id: "C2-05",
    stage: "C2",
    title: "UI integration",
    checkpoints: ["RTL", "Loading", "Error", "Responsive"],
  },
  {
    id: "C3-01",
    stage: "C3",
    title: "Production build",
    checkpoints: ["npm run build", "No TypeScript errors", "No Vite errors"],
  },
  {
    id: "C3-02",
    stage: "C3",
    title: "Business acceptance",
    checkpoints: ["Purchase", "Sale", "Return", "Payment", "Transfer", "Reports"],
  },
  {
    id: "C3-03",
    stage: "C3",
    title: "UI acceptance",
    checkpoints: ["Desktop", "Tablet", "Mobile", "RTL", "Feedback states"],
  },
];
