/** Global keyboard shortcuts — B-006 */

import { navigate } from "./router";
import { routes } from "./paths";

function isTypingTarget(el: EventTarget | null): boolean {
  if (!(el instanceof HTMLElement)) return false;
  const tag = el.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  if (el.isContentEditable) return true;
  return false;
}

/** Focus the main search box if present. */
function focusSearch(): boolean {
  const el = document.querySelector<HTMLInputElement>(
    'main input[type="search"], main input[aria-label="Search"]',
  );
  if (el) {
    el.focus();
    el.select?.();
    return true;
  }
  return false;
}

export function initKeyboard(): () => void {
  const onKey = (e: KeyboardEvent) => {
    if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;

    // / — focus search (or go home)
    if (e.key === "/" && !isTypingTarget(e.target)) {
      e.preventDefault();
      if (!focusSearch()) navigate(routes.home());
      else focusSearch();
      return;
    }

    // ? — help (shift+/)
    if (e.key === "?" && !isTypingTarget(e.target)) {
      e.preventDefault();
      navigate(routes.help());
      return;
    }

    // g then s/k/p/h — go to section (simple single-key with g prefix via session flag)
    if (e.key === "g" && !isTypingTarget(e.target)) {
      (window as unknown as { __stigrefG?: boolean }).__stigrefG = true;
      window.setTimeout(() => {
        (window as unknown as { __stigrefG?: boolean }).__stigrefG = false;
      }, 800);
      return;
    }
    const g = (window as unknown as { __stigrefG?: boolean }).__stigrefG;
    if (g && !isTypingTarget(e.target)) {
      (window as unknown as { __stigrefG?: boolean }).__stigrefG = false;
      if (e.key === "s") {
        e.preventDefault();
        navigate(routes.stigs());
      } else if (e.key === "k") {
        e.preventDefault();
        navigate(routes.kev());
      } else if (e.key === "p") {
        e.preventDefault();
        navigate(routes.products());
      } else if (e.key === "h") {
        e.preventDefault();
        navigate(routes.home());
      } else if (e.key === "a") {
        e.preventDefault();
        navigate(routes.saved());
      } else if (e.key === "r") {
        e.preventDefault();
        navigate(routes.releases());
      }
    }

    // Escape — blur active input
    if (e.key === "Escape" && isTypingTarget(e.target)) {
      (e.target as HTMLElement).blur();
    }
  };

  window.addEventListener("keydown", onKey);
  return () => window.removeEventListener("keydown", onKey);
}
