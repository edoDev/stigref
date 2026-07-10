import { writable } from "svelte/store";
import { baseUrl } from "./paths";

export type Route =
  | { name: "home" }
  | { name: "about" }
  | { name: "stigs" }
  | { name: "stig"; id: string }
  | { name: "rule"; id: string }
  | { name: "kev" }
  | { name: "saved" }
  | { name: "products" }
  | { name: "product"; id: string }
  | { name: "help" }
  | { name: "releases" }
  | { name: "compare" }
  | { name: "cci" }
  | { name: "cciDetail"; id: string }
  | { name: "vendors" }
  | { name: "vendor"; id: string }
  | { name: "tools" }
  | { name: "nist" }
  | { name: "notfound"; path: string };

function stripBase(pathname: string): string {
  let base = baseUrl();
  if (base !== "/" && pathname.startsWith(base.slice(0, -1))) {
    // base is /stigref/ — also accept /stigref without trailing
    const bare = base.replace(/\/$/, "");
    if (pathname === bare || pathname.startsWith(bare + "/")) {
      pathname = pathname.slice(bare.length) || "/";
    }
  }
  if (!pathname.startsWith("/")) pathname = "/" + pathname;
  return pathname;
}

export function parsePath(pathname: string = location.pathname): Route {
  const path = stripBase(pathname);
  if (path === "/" || path === "") return { name: "home" };
  if (path === "/about") return { name: "about" };
  if (path === "/stigs") return { name: "stigs" };
  if (path === "/kev") return { name: "kev" };
  if (path === "/saved") return { name: "saved" };
  if (path === "/products") return { name: "products" };
  if (path === "/help") return { name: "help" };
  if (path === "/releases") return { name: "releases" };
  if (path === "/compare") return { name: "compare" };
  if (path === "/cci") return { name: "cci" };
  if (path === "/vendors") return { name: "vendors" };
  if (path === "/tools") return { name: "tools" };
  if (path === "/nist") return { name: "nist" };

  let m = path.match(/^\/stigs\/([^/]+)\/?$/);
  if (m) return { name: "stig", id: decodeURIComponent(m[1]) };

  m = path.match(/^\/rules\/([^/]+)\/?$/);
  if (m) return { name: "rule", id: decodeURIComponent(m[1]) };

  m = path.match(/^\/products\/([^/]+)\/?$/);
  if (m) return { name: "product", id: decodeURIComponent(m[1]) };

  m = path.match(/^\/cci\/([^/]+)\/?$/);
  if (m) return { name: "cciDetail", id: decodeURIComponent(m[1]) };

  m = path.match(/^\/vendors\/([^/]+)\/?$/);
  if (m) return { name: "vendor", id: decodeURIComponent(m[1]) };

  return { name: "notfound", path };
}

export const route = writable<Route>(parsePath());

export function navigate(to: string, replace = false): void {
  const url = to.startsWith("http") ? to : to;
  if (replace) history.replaceState({}, "", url);
  else history.pushState({}, "", url);
  route.set(parsePath());
  window.scrollTo(0, 0);
}

export function initRouter(): () => void {
  const onPop = () => route.set(parsePath());
  window.addEventListener("popstate", onPop);

  // Intercept same-origin left-clicks on internal anchors
  const onClick = (e: MouseEvent) => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey)
      return;
    const target = (e.target as Element | null)?.closest?.("a");
    if (!target) return;
    const href = target.getAttribute("href");
    if (!href || href.startsWith("#") || target.target === "_blank") return;
    if (target.hasAttribute("download")) return;
    let url: URL;
    try {
      url = new URL(href, location.origin);
    } catch {
      return;
    }
    if (url.origin !== location.origin) return;
    const base = baseUrl().replace(/\/$/, "");
    if (base && !url.pathname.startsWith(base) && url.pathname !== base) return;
    e.preventDefault();
    navigate(url.pathname + url.search + url.hash);
  };
  document.addEventListener("click", onClick);

  return () => {
    window.removeEventListener("popstate", onPop);
    document.removeEventListener("click", onClick);
  };
}
