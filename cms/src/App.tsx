import gsap from "gsap";
import type { ReactNode } from "react";
import { useLayoutEffect, useRef } from "react";
import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import { LoginPage } from "./pages/Login";
import { PublishPage } from "./pages/Publish";
import { ShowEditPage } from "./pages/ShowEdit";
import { ShowNewPage } from "./pages/ShowNew";
import { ShowsPage } from "./pages/Shows";

function Guard({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function Shell({ children }: { children: ReactNode }) {
  const { email, role, logout } = useAuth();
  const root = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const el = root.current;
    if (!el) return;
    const reduced =
      new URLSearchParams(location.search).get("reduced") === "1" ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;
    const ctx = gsap.context(() => {
      gsap.from(".topbar [data-anim]", {
        y: -14,
        autoAlpha: 0,
        duration: 0.55,
        ease: "power2.out",
        stagger: 0.05,
      });
    }, el);
    return () => ctx.revert();
  }, []);

  return (
    <div className="shell" ref={root}>
      <header className="topbar">
        <div className="brand" data-anim>
          <span className="brand-mark" aria-hidden="true">
            P
          </span>
          Peblo CMS
        </div>
        <nav className="nav" data-anim>
          <NavLink to="/shows">Shows</NavLink>
          <NavLink to="/publish">Publish</NavLink>
        </nav>
        <div className="who" data-anim>
          <span>
            {email}
            <em>{role}</em>
          </span>
          <button type="button" className="ghost" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>
      {children}
    </div>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/shows"
        element={
          <Guard>
            <Shell>
              <ShowsPage />
            </Shell>
          </Guard>
        }
      />
      <Route
        path="/shows/new"
        element={
          <Guard>
            <Shell>
              <ShowNewPage />
            </Shell>
          </Guard>
        }
      />
      <Route
        path="/shows/:id"
        element={
          <Guard>
            <Shell>
              <ShowEditPage />
            </Shell>
          </Guard>
        }
      />
      <Route
        path="/publish"
        element={
          <Guard>
            <Shell>
              <PublishPage />
            </Shell>
          </Guard>
        }
      />
      <Route path="*" element={<Navigate to="/shows" replace />} />
    </Routes>
  );
}
