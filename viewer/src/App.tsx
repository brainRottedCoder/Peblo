import { useEffect, useState } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";
import { HomePage } from "./pages/Home";
import { SearchPage } from "./pages/Search";
import { ShowDetailPage } from "./pages/ShowDetail";
import { WatchPage } from "./pages/Watch";

export function App() {
  const [solid, setSolid] = useState(false);
  const loc = useLocation();
  const watching = loc.pathname.startsWith("/watch");
  useEffect(() => {
    const onScroll = () => setSolid(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      {!watching && (
      <header className={`top ${solid ? "solid" : ""}`}>
        <NavLink to="/" className="logo">
          Peblo
        </NavLink>
        <nav>
          <NavLink to="/" end>
            Home
          </NavLink>
          <NavLink to="/search">Search</NavLink>
        </nav>
        <div className="top-right">
          <div className="avatar" title="Kids profile" aria-hidden />
        </div>
      </header>
      )}
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/show/:slug" element={<ShowDetailPage />} />
        <Route path="/watch/:slug" element={<WatchPage />} />
      </Routes>
    </>
  );
}
