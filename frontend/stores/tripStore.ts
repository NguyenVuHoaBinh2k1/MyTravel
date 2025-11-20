import { create } from "zustand";
import { Trip, TripAccommodation, TripRestaurant, TripActivity } from "@/types";

interface TripState {
  currentTrip: Trip | null;
  trips: Trip[];
  isLoading: boolean;
  error: string | null;

  // Actions
  setCurrentTrip: (trip: Trip | null) => void;
  setTrips: (trips: Trip[]) => void;
  addTrip: (trip: Trip) => void;
  updateTrip: (tripId: string, updates: Partial<Trip>) => void;
  deleteTrip: (tripId: string) => void;

  // Accommodations
  addAccommodation: (accommodation: TripAccommodation) => void;
  updateAccommodation: (accId: string, updates: Partial<TripAccommodation>) => void;
  removeAccommodation: (accId: string) => void;

  // Restaurants
  addRestaurant: (restaurant: TripRestaurant) => void;
  updateRestaurant: (restId: string, updates: Partial<TripRestaurant>) => void;
  removeRestaurant: (restId: string) => void;

  // Activities
  addActivity: (activity: TripActivity) => void;
  updateActivity: (actId: string, updates: Partial<TripActivity>) => void;
  removeActivity: (actId: string) => void;

  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useTripStore = create<TripState>((set) => ({
  currentTrip: null,
  trips: [],
  isLoading: false,
  error: null,

  setCurrentTrip: (trip) => set({ currentTrip: trip }),

  setTrips: (trips) => set({ trips }),

  addTrip: (trip) =>
    set((state) => ({
      trips: [...state.trips, trip],
    })),

  updateTrip: (tripId, updates) =>
    set((state) => ({
      trips: state.trips.map((t) =>
        t.id === tripId ? { ...t, ...updates } : t
      ),
      currentTrip:
        state.currentTrip?.id === tripId
          ? { ...state.currentTrip, ...updates }
          : state.currentTrip,
    })),

  deleteTrip: (tripId) =>
    set((state) => ({
      trips: state.trips.filter((t) => t.id !== tripId),
      currentTrip:
        state.currentTrip?.id === tripId ? null : state.currentTrip,
    })),

  addAccommodation: (accommodation) =>
    set((state) => {
      if (!state.currentTrip) return state;
      return {
        currentTrip: {
          ...state.currentTrip,
          accommodations: [...(state.currentTrip.accommodations || []), accommodation],
        },
      };
    }),

  updateAccommodation: (accId, updates) =>
    set((state) => {
      if (!state.currentTrip) return state;
      return {
        currentTrip: {
          ...state.currentTrip,
          accommodations: state.currentTrip.accommodations?.map((a) =>
            a.id === accId ? { ...a, ...updates } : a
          ),
        },
      };
    }),

  removeAccommodation: (accId) =>
    set((state) => {
      if (!state.currentTrip) return state;
      return {
        currentTrip: {
          ...state.currentTrip,
          accommodations: state.currentTrip.accommodations?.filter(
            (a) => a.id !== accId
          ),
        },
      };
    }),

  addRestaurant: (restaurant) =>
    set((state) => {
      if (!state.currentTrip) return state;
      return {
        currentTrip: {
          ...state.currentTrip,
          restaurants: [...(state.currentTrip.restaurants || []), restaurant],
        },
      };
    }),

  updateRestaurant: (restId, updates) =>
    set((state) => {
      if (!state.currentTrip) return state;
      return {
        currentTrip: {
          ...state.currentTrip,
          restaurants: state.currentTrip.restaurants?.map((r) =>
            r.id === restId ? { ...r, ...updates } : r
          ),
        },
      };
    }),

  removeRestaurant: (restId) =>
    set((state) => {
      if (!state.currentTrip) return state;
      return {
        currentTrip: {
          ...state.currentTrip,
          restaurants: state.currentTrip.restaurants?.filter(
            (r) => r.id !== restId
          ),
        },
      };
    }),

  addActivity: (activity) =>
    set((state) => {
      if (!state.currentTrip) return state;
      return {
        currentTrip: {
          ...state.currentTrip,
          activities: [...(state.currentTrip.activities || []), activity],
        },
      };
    }),

  updateActivity: (actId, updates) =>
    set((state) => {
      if (!state.currentTrip) return state;
      return {
        currentTrip: {
          ...state.currentTrip,
          activities: state.currentTrip.activities?.map((a) =>
            a.id === actId ? { ...a, ...updates } : a
          ),
        },
      };
    }),

  removeActivity: (actId) =>
    set((state) => {
      if (!state.currentTrip) return state;
      return {
        currentTrip: {
          ...state.currentTrip,
          activities: state.currentTrip.activities?.filter(
            (a) => a.id !== actId
          ),
        },
      };
    }),

  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));
