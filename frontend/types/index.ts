// User Types
export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  preferences?: UserPreferences;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  language: "vi" | "en";
  currency: string;
  dietary_restrictions?: string[];
  travel_style?: "budget" | "mid-range" | "luxury";
}

// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Trip Types
export interface Trip {
  id: string;
  user_id: string;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  budget: number;
  currency: string;
  status: TripStatus;
  travelers_count: number;
  notes?: string;
  accommodations?: TripAccommodation[];
  restaurants?: TripRestaurant[];
  transportations?: TripTransportation[];
  activities?: TripActivity[];
  expenses?: TripExpense[];
  created_at: string;
  updated_at: string;
}

export type TripStatus = "planning" | "booked" | "ongoing" | "completed" | "cancelled";

export interface TripAccommodation {
  id: string;
  trip_id: string;
  name: string;
  type: string;
  address: string;
  latitude?: number;
  longitude?: number;
  check_in_date: string;
  check_out_date: string;
  price_per_night: number;
  total_price: number;
  currency: string;
  booking_url?: string;
  status: "suggested" | "selected" | "booked";
  rating?: number;
  image_url?: string;
  amenities?: string[];
  notes?: string;
}

export interface TripRestaurant {
  id: string;
  trip_id: string;
  name: string;
  cuisine_type: string;
  address: string;
  latitude?: number;
  longitude?: number;
  price_range: string;
  rating?: number;
  image_url?: string;
  specialty_dishes?: string[];
  opening_hours?: string;
  phone?: string;
  status: "suggested" | "selected" | "visited";
  notes?: string;
}

export interface TripTransportation {
  id: string;
  trip_id: string;
  type: "flight" | "bus" | "train" | "taxi" | "grab" | "motorbike" | "other";
  from_location: string;
  to_location: string;
  departure_time: string;
  arrival_time: string;
  provider?: string;
  booking_reference?: string;
  price: number;
  currency: string;
  status: "suggested" | "selected" | "booked";
  notes?: string;
}

export interface TripActivity {
  id: string;
  trip_id: string;
  name: string;
  description?: string;
  location: string;
  latitude?: number;
  longitude?: number;
  day_number: number;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  price?: number;
  currency: string;
  category: string;
  status: "suggested" | "selected" | "completed";
  rating?: number;
  image_url?: string;
  notes?: string;
}

export interface TripExpense {
  id: string;
  trip_id: string;
  category: string;
  description: string;
  amount: number;
  currency: string;
  date: string;
  is_planned: boolean;
  notes?: string;
}

// Chat/Conversation Types
export interface Conversation {
  id: string;
  trip_id?: string;
  user_id: string;
  title?: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  agent_type?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

// Chat Request/Response Types
export interface ChatRequest {
  message: string;
  trip_id?: number;
  conversation_id?: number;
}

export interface ChatResponse {
  message: Message;
  conversation_id: number;
  agent_type?: string;
  data?: AgentData;
  suggestions: string[];
  actions: AgentAction[];
}

export interface AgentAction {
  type: string;
  label: string;
  payload?: Record<string, unknown>;
}

// Agent Response Types
export interface AgentResponse {
  message: string;
  agent_type: string;
  data?: AgentData;
  suggestions?: string[];
}

export interface AgentData {
  accommodations?: TripAccommodation[];
  restaurants?: TripRestaurant[];
  transportations?: TripTransportation[];
  activities?: TripActivity[];
  budget_summary?: BudgetSummary;
}

export interface BudgetSummary {
  total_budget: number;
  total_spent: number;
  total_planned: number;
  remaining: number;
  breakdown: {
    category: string;
    planned: number;
    actual: number;
  }[];
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
