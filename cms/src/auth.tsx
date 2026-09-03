import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { api } from "./api";
import type { Role } from "./types";

type Auth = {
  token: string | null;
  email: string | null;
  role: Role | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState(() => localStorage.getItem("peblo_token"));
  const [email, setEmail] = useState(() => localStorage.getItem("peblo_email"));
  const [role, setRole] = useState<Role | null>(() => (localStorage.getItem("peblo_role") as Role) || null);

  const value = useMemo<Auth>(
    () => ({
      token,
      email,
      role,
      async login(nextEmail, password) {
        const res = await api<{ access_token: string; email: string; role: Role }>("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email: nextEmail, password }),
        });
        localStorage.setItem("peblo_token", res.access_token);
        localStorage.setItem("peblo_email", res.email);
        localStorage.setItem("peblo_role", res.role);
        setToken(res.access_token);
        setEmail(res.email);
        setRole(res.role);
      },
      logout() {
        localStorage.removeItem("peblo_token");
        localStorage.removeItem("peblo_email");
        localStorage.removeItem("peblo_role");
        setToken(null);
        setEmail(null);
        setRole(null);
      },
    }),
    [token, email, role],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth outside provider");
  return ctx;
}
