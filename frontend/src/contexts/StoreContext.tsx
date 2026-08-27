import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import api from "../services/api";

export interface Store {
  id: number;
  name: string;
  code: string;
  phone: string;
  address: string;
  is_active: boolean;
}

interface StoreContextType {
  stores: Store[];
  activeStore: Store | null;
  setActiveStore: (store: Store) => void;
  loading: boolean;
}

const StoreContext =
  createContext<StoreContextType | undefined>(
    undefined
  );

export function StoreProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [stores, setStores] = useState<Store[]>([]);
  const [activeStore, setActiveStoreState] =
    useState<Store | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/stores/")
      .then((response) => {
        const data = Array.isArray(response.data)
          ? response.data
          : response.data.results;

        const availableStores: Store[] = data || [];

        setStores(availableStores);

        if (availableStores.length === 0) {
          return;
        }

        const savedStoreId =
          localStorage.getItem("active_store_id");

        const savedStore = availableStores.find(
          (store) =>
            store.id === Number(savedStoreId)
        );

        if (savedStore) {
          setActiveStoreState(savedStore);
        } else {
          setActiveStoreState(
            availableStores[0]
          );

          localStorage.setItem(
            "active_store_id",
            String(availableStores[0].id)
          );
        }
      })
      .catch((error) => {
        console.error(
          "STORES ERROR:",
          error.response?.status
        );

        console.error(
          "STORES DATA:",
          error.response?.data
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const setActiveStore = (store: Store) => {
    setActiveStoreState(store);

    localStorage.setItem(
      "active_store_id",
      String(store.id)
    );
  };

  return (
    <StoreContext.Provider
      value={{
        stores,
        activeStore,
        setActiveStore,
        loading,
      }}
    >
      {children}
    </StoreContext.Provider>
  );
}

export function useStore() {
  const context = useContext(StoreContext);

  if (!context) {
    throw new Error(
      "useStore باید داخل StoreProvider استفاده شود."
    );
  }

  return context;
}

