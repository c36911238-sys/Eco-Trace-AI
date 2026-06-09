import { create } from 'zustand';

interface User {
  id: number;
  email: string;
  full_name: string;
  eco_level: number;
  total_carbon_saved: number;
}

interface CarbonStore {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useCarbonStore = create<CarbonStore>((set) => ({
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  logout: () => {
    localStorage.removeItem('access_token');
    set({ user: null, isAuthenticated: false });
  },
}));
