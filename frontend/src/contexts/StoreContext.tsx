import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { getCurrentUser } from "../services/identityService";
import type { CurrentUser, StoreAccess, StoreRole } from "../services/authTypes";

export type Store = StoreAccess;

interface StoreContextType {
  user: CurrentUser | null;
  stores: Store[];
  activeStore: Store | null;
  activeRole: StoreRole | null;
  setActiveStore: (store: Store) => void;
  loading: boolean;
  reloadIdentity: () => Promise<void>;
}

const StoreContext = createContext<StoreContextType | undefined>(undefined);

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [activeStore, setActiveStoreState] = useState<Store | null>(null);
  const [loading, setLoading] = useState(true);

  const loadIdentity = async () => {
    const accessToken = localStorage.getItem("access_token");

    if (!accessToken) {
      setUser(null);
      setStores([]);
      setActiveStoreState(null);
      localStorage.removeItem("active_store_id");
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const identity = await getCurrentUser();
      const availableStores = identity.stores ?? [];

      setUser(identity);
      setStores(availableStores);

      if (availableStores.length === 0) {
        setActiveStoreState(null);
        localStorage.removeItem("active_store_id");
        return;
      }

      const savedStoreId = Number(localStorage.getItem("active_store_id"));
      const savedStore = availableStores.find((store) => store.id === savedStoreId);
      const nextStore = savedStore ?? availableStores[0];

      setActiveStoreState(nextStore);
      localStorage.setItem("active_store_id", String(nextStore.id));
    } catch (error) {
      console.error("IDENTITY ERROR:", error);
      setUser(null);
      setStores([]);
      setActiveStoreState(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadIdentity();

    const handleAuthChange = () => {
      void loadIdentity();
    };

    window.addEventListener("auth-change", handleAuthChange);
    return () => window.removeEventListener("auth-change", handleAuthChange);
  }, []);

  const setActiveStore = (store: Store) => {
    if (!stores.some((item) => item.id === store.id)) return;
    setActiveStoreState(store);
    localStorage.setItem("active_store_id", String(store.id));
  };

  const value = useMemo<StoreContextType>(() => ({
    user,
    stores,
    activeStore,
    activeRole: activeStore?.role ?? null,
    setActiveStore,
    loading,
    reloadIdentity: loadIdentity,
  }), [user, stores, activeStore, loading]);

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore() {
  const context = useContext(StoreContext);
  if (!context) {
    throw new Error("useStore باید داخل StoreProvider استفاده شود.");
  }
  return context;
}
