"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";

const Globe = dynamic(() => import("react-globe.gl"), { ssr: false });

type Props = {
  focus?: { lat: number; lng: number } | null;
  rotateSpeed?: number;
  className?: string;
  fillContainer?: boolean;
};

export default function GlobeBackground({
  focus,
  rotateSpeed = 0.12,
  className = "",
  fillContainer = false,
}: Props) {
  const globeRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 420, height: 220 });

  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setSize({
        width: Math.max(200, Math.round(width)),
        height: Math.max(180, Math.round(height)),
      });
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!globeRef.current) return;
    const controls = globeRef.current.controls();
    controls.autoRotate = true;
    controls.autoRotateSpeed = rotateSpeed;
    controls.enableZoom = false;

    if (focus) {
      globeRef.current.pointOfView({ lat: focus.lat, lng: focus.lng, altitude: 1.6 }, 2000);
    } else {
      globeRef.current.pointOfView({ lat: 20, lng: -20, altitude: 2.4 }, 1000);
    }
  }, [focus, rotateSpeed]);

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden ${fillContainer ? "h-full w-full" : "h-full w-full"} ${className}`}
    >
      <div className="absolute inset-0 flex items-center justify-center">
        <Globe
          ref={globeRef}
          globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
          bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
          backgroundColor="rgba(0,0,0,0)"
          atmosphereColor="#7dd3fc"
          atmosphereAltitude={0.12}
          width={size.width}
          height={size.height}
        />
      </div>
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_30%,rgba(20,20,23,0.85)_100%)]" />
    </div>
  );
}
