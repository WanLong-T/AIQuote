export interface AmapProjectPoint {
  dbId: number | undefined;
  id: number;
  name: string;
  lng: number;
  lat: number;
  amount: number;
  rating: 'A' | 'B' | 'C' | 'D' | '';
  province: string;
  city: string;
  district: string;
  owner: string;
  status: string;
  locationPrecision: string | undefined;
}
