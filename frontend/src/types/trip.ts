export type ListingItem = {
  category: "flight" | "hotel" | "car";
  title: string;
  description: string;
  price: number;
  currency?: string;
  details?: Record<string, unknown>;
};

export type WeatherInfo = {
  summary: string;
  high_f?: number | null;
  low_f?: number | null;
  precipitation_chance?: number | null;
  alerts?: string[];
};

export type TripOption = {
  id: string;
  destination_city: string;
  destination_state?: string | null;
  destination_airport: string;
  destination_lat: number;
  destination_lng: number;
  origin_airport: string;
  total_price: number;
  currency?: string;
  flight_price: number;
  hotel_price: number;
  car_price: number;
  listings: ListingItem[];
  why?: string[];
  weather?: WeatherInfo | null;
  departure_date?: string | null;
  return_date?: string | null;
  within_budget?: boolean;
  over_budget_by?: number;
};

export type Activity = {
  id: string;
  name: string;
  category: string;
  description: string;
  lat: number;
  lng: number;
  cost_estimate?: number;
  duration_hours?: number;
};

export type ItinerarySegment = {
  period: "Morning" | "Afternoon" | "Evening";
  time_label: string;
  activity: Activity;
};

export type ItineraryDay = {
  day_index: number;
  date?: string | null;
  title: string;
  segments: ItinerarySegment[];
};

export type Itinerary = {
  option_id: string;
  destination_city: string;
  destination_state?: string | null;
  days: ItineraryDay[];
  activities: Activity[];
};

export type Recommendations = {
  option_id: string;
  destination: string;
  packing: string[];
  tips: string[];
  weather_notes: string[];
  itinerary_highlights: string[];
};

export type AppView = "landing" | "planning" | "selected";
