"use client";

import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { useEffect, useRef } from "react";
import type { Itinerary, TripOption } from "@/types/trip";

type Props = {
  trip: TripOption;
  mapboxToken: string;
  fullHeight?: boolean;
  itinerary?: Itinerary | null;
  activeActivityId?: string | null;
};

const DAY_COLORS = ["#f59e0b", "#38bdf8", "#a78bfa", "#34d399", "#f472b6"];

export default function TripMap({
  trip,
  mapboxToken,
  fullHeight = true,
  itinerary = null,
  activeActivityId = null,
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<Record<string, mapboxgl.Marker>>({});

  useEffect(() => {
    if (!containerRef.current || !mapboxToken) return;

    mapboxgl.accessToken = mapboxToken;
    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [trip.destination_lng, trip.destination_lat],
      zoom: 4,
      pitch: 40,
    });
    mapRef.current = map;

    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    map.on("load", () => {
      map.flyTo({
        center: [trip.destination_lng, trip.destination_lat],
        zoom: 11,
        pitch: 50,
        duration: 2800,
        essential: true,
      });

      new mapboxgl.Marker({ color: "#ffffff" })
        .setLngLat([trip.destination_lng, trip.destination_lat])
        .setPopup(
          new mapboxgl.Popup({ offset: 24 }).setHTML(
            `<strong>${trip.destination_city}</strong><br/>${trip.destination_airport}`,
          ),
        )
        .addTo(map);
    });

    return () => {
      map.remove();
      mapRef.current = null;
      markersRef.current = {};
    };
  }, [trip, mapboxToken]);

  // Draw activity markers + a per-day route line whenever the itinerary changes.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const render = () => {
      Object.values(markersRef.current).forEach((m) => m.remove());
      markersRef.current = {};

      ["itinerary-arrows", "itinerary-routes"].forEach((id) => {
        if (map.getLayer(id)) map.removeLayer(id);
      });
      if (map.getSource("itinerary-routes")) map.removeSource("itinerary-routes");

      if (!itinerary || !itinerary.days.length) return;

      const bounds = new mapboxgl.LngLatBounds();
      bounds.extend([trip.destination_lng, trip.destination_lat]);
      const routeFeatures: GeoJSON.Feature[] = [];
      let counter = 0;

      itinerary.days.forEach((day, dayIdx) => {
        const color = DAY_COLORS[dayIdx % DAY_COLORS.length];
        const dayCoords: [number, number][] = [];

        day.segments.forEach((segment) => {
          counter += 1;
          const { activity } = segment;
          const lngLat: [number, number] = [activity.lng, activity.lat];
          dayCoords.push(lngLat);
          bounds.extend(lngLat);

          // Mapbox controls `transform` (translate) on the marker root element,
          // so the visual/scaled part must live on an inner child element.
          const el = document.createElement("div");
          const pin = document.createElement("div");
          pin.className = "roam-activity-pin";
          pin.textContent = String(counter);
          pin.style.cssText = `display:flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:9999px;background:${color};color:#000;font-size:12px;font-weight:700;border:2px solid rgba(0,0,0,0.4);box-shadow:0 2px 6px rgba(0,0,0,0.5);cursor:pointer;transition:transform 0.15s;`;
          el.appendChild(pin);

          const marker = new mapboxgl.Marker({ element: el })
            .setLngLat(lngLat)
            .setPopup(
              new mapboxgl.Popup({ offset: 20 }).setHTML(
                `<div style="font-weight:600">${counter}. ${activity.name}</div>` +
                  `<div style="font-size:11px;color:#555">${segment.period} · ${segment.time_label}</div>` +
                  `<div style="font-size:11px;margin-top:2px">${activity.description}</div>`,
              ),
            )
            .addTo(map);
          markersRef.current[activity.id] = marker;
        });

        if (dayCoords.length > 1) {
          routeFeatures.push({
            type: "Feature",
            properties: { color },
            geometry: { type: "LineString", coordinates: dayCoords },
          });
        }
      });

      map.addSource("itinerary-routes", {
        type: "geojson",
        data: { type: "FeatureCollection", features: routeFeatures },
      });
      map.addLayer({
        id: "itinerary-routes",
        type: "line",
        source: "itinerary-routes",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": ["get", "color"],
          "line-width": 3,
          "line-opacity": 0.7,
          "line-dasharray": [1, 1.5],
        },
      });

      // Directional arrows along each day's route.
      map.addLayer({
        id: "itinerary-arrows",
        type: "symbol",
        source: "itinerary-routes",
        layout: {
          "symbol-placement": "line",
          "symbol-spacing": 70,
          "text-field": "▶",
          "text-size": 14,
          "text-keep-upright": false,
          "text-rotation-alignment": "map",
          "text-allow-overlap": true,
          "text-ignore-placement": true,
        },
        paint: {
          "text-color": ["get", "color"],
          "text-halo-color": "rgba(0,0,0,0.65)",
          "text-halo-width": 1.2,
        },
      });

      if (!bounds.isEmpty()) {
        map.fitBounds(bounds, { padding: 80, maxZoom: 13, duration: 1600 });
      }
    };

    if (map.isStyleLoaded()) {
      render();
    } else {
      map.once("load", render);
    }
  }, [itinerary, trip.destination_lat, trip.destination_lng]);

  // Emphasize the marker for the hovered itinerary item. Only touch the inner
  // pin's transform — the root element's transform is owned by Mapbox for
  // positioning, so overwriting it would fling every pin to the corner.
  useEffect(() => {
    Object.entries(markersRef.current).forEach(([id, marker]) => {
      const root = marker.getElement();
      const pin = root.firstElementChild as HTMLElement | null;
      const active = id === activeActivityId;
      if (pin) pin.style.transform = active ? "scale(1.35)" : "scale(1)";
      root.style.zIndex = active ? "10" : "1";
    });
  }, [activeActivityId]);

  return (
    <div className={fullHeight ? "absolute inset-0" : "h-[360px] w-full overflow-hidden rounded-2xl"}>
      <div ref={containerRef} className="h-full w-full" />
    </div>
  );
}
