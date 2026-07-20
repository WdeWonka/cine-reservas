export interface MovieCreate {
  title: string;
  duration_min: number;
  age_rating?: string | null;
}

export interface MovieUpdate {
  title?: string;
  duration_min?: number;
  age_rating?: string | null;
}

export interface MovieOut {
  movie_id: number;
  title: string;
  duration_min: number;
  age_rating: string | null;
  is_active: boolean;
}
