"use client";

import { Component, ReactNode } from "react";

/**
 * Guards the page from any failure inside lazy 3D scenes (missing WebGL,
 * driver issues, runtime errors). The 3D layer is decorative: on failure it
 * disappears and the page falls back to the static gradient background.
 */
export class Scene3DBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error: Error) {
    const detail = String(
      (error as Error)?.stack ?? (error as Error)?.message ?? error,
    ).slice(0, 2000);
    (window as unknown as { __sceneError?: string }).__sceneError = detail;
    console.warn("3D scene disabled:", detail);
  }

  render() {
    return this.state.failed ? null : this.props.children;
  }
}
