import gsap from "gsap";
import { useLayoutEffect, type DependencyList, type RefObject } from "react";

function reducedMotion() {
  return (
    new URLSearchParams(location.search).get("reduced") === "1" ||
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

export function useGsapEnter(
  root: RefObject<HTMLElement | null>,
  selector = "[data-anim]",
  deps: DependencyList = [],
) {
  useLayoutEffect(() => {
    const el = root.current;
    if (!el || reducedMotion()) return;
    const nodes = el.querySelectorAll(selector);
    if (!nodes.length) return;
    const ctx = gsap.context(() => {
      gsap.from(nodes, {
        y: 22,
        autoAlpha: 0,
        duration: 0.7,
        ease: "power2.out",
        stagger: 0.06,
      });
    }, el);
    return () => ctx.revert();
  }, [root, selector, ...deps]);
}
