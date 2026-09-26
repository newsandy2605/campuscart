const browserApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100';
const serverApiUrl = process.env.CAMPUSCART_INTERNAL_API_URL || browserApiUrl;
export const API_URL = typeof window === 'undefined' ? serverApiUrl : browserApiUrl;

export type AppUser = {
  id: number;
  name: string;
  email: string;
  phone?: string | null;
  role: string;
  email_verified?: boolean;
  phone_verified?: boolean;
  campuses?: { slug: string; name: string; verified: boolean }[];
};

export type OTPDelivery = { provider?: string | null; debug_code?: string | null };

export type AuthResponse = { token: string; user: AppUser; otp_challenge_id?: number; otp_delivery?: OTPDelivery; verification_channel?: 'email' | 'phone' };

export type Campus = {
  id: number;
  name: string;
  slug: string;
  city: string;
  state?: string;
  pincode?: string;
  email_domain: string;
  email_domains?: string[];
  description: string;
  member_count: number;
  current_semester?: string;
  semester_start?: string;
  semester_end?: string;
  pickup_locations?: { id: number; name: string; address: string; landmark: string; opening_hours: string }[];
  active?: boolean;
};

export type Seller = {
  id: number;
  user_id?: number;
  display_name: string;
  bio: string;
  verified: boolean;
  reputation_score: number;
  completed_orders: number;
  cancellations: number;
  response_rate: number;
  average_rating?: number;
};

export type Product = {
  id: string;
  name: string;
  slug?: string;
  thumbnail?: { url: string; alt?: string } | null;
  pricing?: { priceRange?: { start?: { gross?: { amount: number; currency: string } } } | null } | null;
};

export type Listing = {
  id: number;
  campus_slug: string;
  campus_name?: string;
  campus_city?: string;
  campus_state?: string;
  campus_pincode?: string;
  title: string;
  saleor_product_id?: string | null;
  seller_id: number;
  seller: Seller;
  category: string;
  subcategory?: string;
  condition: string;
  listing_type: string;
  price: number;
  price_override?: number | null;
  rental_price?: number | null;
  rental_period?: string;
  deposit?: number | null;
  description: string;
  status: string;
  pickup_area: string;
  pickup_landmark: string;
  pickup_instructions?: string;
  distance_km?: number | null;
  views: number;
  favorites: number;
  share_count: number;
  created_at: string;
  images: { id?: number; url: string; alt: string; sort_order?: number }[];
  product: Product;
};

export type Recommendation = { listing: Listing; score: number; reason: string };

export type Conversation = {
  id: number;
  listing_id: number;
  buyer_id: number;
  seller_id: number;
  buyer_name?: string;
  seller_name?: string;
  listing_title?: string;
  transaction_id?: number | null;
  blocked: boolean;
  last_message_at?: string | null;
  created_at: string;
};

export type Message = {
  id: number;
  conversation_id: number;
  sender_id: number;
  body: string;
  read_at?: string | null;
  created_at: string;
};

export type Offer = {
  id: number;
  listing_id: number;
  buyer_id: number;
  seller_id: number;
  buyer_name?: string;
  seller_name?: string;
  listing_title?: string;
  amount: number;
  message: string;
  status: string;
  expires_at?: string | null;
  created_at: string;
  responded_at?: string | null;
};

export type Transaction = {
  id: number;
  listing_id: number;
  offer_id?: number | null;
  swap_offer_id?: number | null;
  buyer_id: number;
  seller_id: number;
  buyer_name?: string;
  seller_name?: string;
  agreed_price: number;
  status: string;
  pickup_location_id?: number | null;
  pickup_address?: string;
  pickup_landmark?: string;
  pickup_date?: string | null;
  pickup_time?: string | null;
  buyer_handoff_confirmed: boolean;
  seller_handoff_confirmed: boolean;
  paid_at?: string | null;
  completed_at?: string | null;
  cancelled_at?: string | null;
  viewer_role?: 'buyer' | 'seller' | null;
  listing_title?: string | null;
  listing_status?: string | null;
  handoff_code?: string | null;
  payment_id?: number | null;
  payment_status?: string | null;
};

export type WantedPost = {
  id: number;
  campus_slug?: string;
  owner_id?: number;
  title: string;
  category: string;
  description: string;
  budget_min?: number | null;
  budget_max?: number | null;
  needed_by?: string | null;
  created_at: string;
  status?: string;
  is_owner?: boolean;
};

export type Notification = {
  id: number;
  kind: string;
  title: string;
  body: string;
  link: string;
  read: boolean;
  created_at: string;
};

export type Address = {
  id: number;
  label: string;
  line1: string;
  line2: string;
  locality: string;
  city: string;
  state: string;
  pincode: string;
  landmark: string;
  is_default: boolean;
};

export type DemandItem = {
  name: string;
  wanted: number;
  supply: number;
  trend: string;
  range: string;
};

export type SemesterInfo = {
  campus_slug: string;
  current_semester: string;
  semester_start?: string;
  semester_end?: string;
  guidance: string;
};

export type LostFoundItem = {
  id: number;
  item_type: string;
  title: string;
  description: string;
  location_text: string;
  item_date?: string | null;
  status: string;
  claimant_id?: number | null;
  claim_message?: string;
  claimed_at?: string | null;
  resolved_at?: string | null;
  is_owner?: boolean;
  created_at: string;
};

export type SwapOffer = {
  id: number;
  proposer_id: number;
  receiver_id: number;
  proposer_name?: string | null;
  receiver_name?: string | null;
  offered_listing_id: number;
  offered_listing_title?: string | null;
  requested_listing_id: number;
  requested_listing_title?: string | null;
  message: string;
  status: string;
  compatibility: number;
  created_at: string;
  responded_at?: string | null;
  transaction_id?: number | null;
};

export function getToken() {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem('campuscart_token') || '';
}

export function getStoredUser(): AppUser | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem('campuscart_user');
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setSession(data: AuthResponse) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('campuscart_token', data.token);
  localStorage.setItem('campuscart_user', JSON.stringify(data.user));
  const campus = data.user.campuses?.find((x) => x.verified)?.slug;
  if (campus) localStorage.setItem('campuscart_campus', campus);
}

export function clearSession() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('campuscart_token');
  localStorage.removeItem('campuscart_user');
  localStorage.removeItem('campuscart_campus');
}

export function getCampusSlug() {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem('campuscart_campus') || '';
}

export function setCampusSlug(slug: string) {
  if (typeof window !== 'undefined') localStorage.setItem('campuscart_campus', slug);
}

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const authToken = token ?? getToken();
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (authToken) headers.set('Authorization', `Bearer ${authToken}`);

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    cache: 'no-store',
  });

  if (!response.ok) {
    const text = await response.text();
    let message = text || `Request failed with ${response.status}`;
    try {
      const parsed = JSON.parse(text);
      message = parsed.detail || message;
    } catch {}
    if (response.status === 401 && typeof window !== 'undefined') clearSession();
    throw new Error(message);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

export function getCampuses() { return request<Campus[]>('/api/campuses'); }
export function getCampusMembership(slug: string) { return request<{ campus_slug: string; campus_name: string; status: 'approved'|'pending_review'|'not_joined'; verified: boolean; verification_method?: string | null; verified_at?: string | null }>(`/api/campuses/${encodeURIComponent(slug)}/membership`); }

export function getCampus(slug: string) { return request<Campus>(`/api/campuses/${encodeURIComponent(slug)}`); }
export function getMe() { return request<AppUser>('/api/auth/me'); }
export function requestPasswordResetOtp(channel: 'email' | 'phone', destination: string) { return request<{ message: string; otp_delivery?: OTPDelivery }>('/api/auth/otp/request', { method: 'POST', body: JSON.stringify({ channel, destination, purpose: 'password_reset' }) }); }
export function resetPassword(resetToken: string, newPassword: string) { return request<{ ok: boolean; message: string }>('/api/auth/password/reset', { method: 'POST', body: JSON.stringify({ reset_token: resetToken, new_password: newPassword }) }); }

export function getMarketplace(
  slug: string,
  opts: { search?: string; category?: string; condition?: string; listingType?: string; minPrice?: string; maxPrice?: string; sort?: string } = {},
) {
  const params = new URLSearchParams({ campus_slug: slug });
  if (opts.search) params.set('search', opts.search);
  if (opts.category) params.set('category', opts.category);
  if (opts.condition) params.set('condition', opts.condition.toLowerCase().replace('like new', 'like-new'));
  if (opts.listingType) params.set('listing_type', opts.listingType);
  if (opts.minPrice) params.set('min_price', opts.minPrice);
  if (opts.maxPrice) params.set('max_price', opts.maxPrice);
  if (opts.sort) params.set('sort', opts.sort);
  return request<Listing[]>(`/api/marketplace?${params.toString()}`);
}

export function getListing(id: number | string) { return request<Listing>(`/api/listings/${id}`); }
export function updateListing(id: number, body: Record<string, unknown>) { return request<Listing>(`/api/listings/${id}`, { method: 'PATCH', body: JSON.stringify(body) }); }
export function attachListingImage(id: number, body: { url: string; alt?: string; sort_order?: number }) { return request<{ id: number; listing_id: number; url: string; alt: string; sort_order: number }>(`/api/listings/${id}/images`, { method: 'POST', body: JSON.stringify(body) }); }
export function deleteListingImage(id: number, imageId: number) { return request(`/api/listings/${id}/images/${imageId}`, { method: 'DELETE' }); }
export function removeListing(id: number) { return request(`/api/listings/${id}`, { method: 'DELETE' }); }
export function favoriteListing(id: number) { return request<{ favorite: boolean; favorites: number }>(`/api/listings/${id}/favorite`, { method: 'POST' }); }
export function shareListing(id: number) { return request<{ share_count: number; whatsapp_url: string }>(`/api/listings/${id}/share`, { method: 'POST' }); }
export function trackEvent(eventType: string, campusSlug: string, listingId?: number, category?: string, query?: string) {
  const params = new URLSearchParams({ event_type: eventType, campus_slug: campusSlug });
  if (listingId) params.set('listing_id', String(listingId));
  if (category) params.set('category', category);
  if (query) params.set('query', query);
  return request<{ recorded: boolean }>(`/api/listing-tools/track?${params.toString()}`, { method: 'POST' });
}
export function getRecommendations(slug: string) { return request<{ items: Recommendation[] }>(`/api/recommendations?campus_slug=${encodeURIComponent(slug)}`); }
export function getBundles(slug: string) { return request<{ name: string; category: string; items: Listing[]; total: number }[]>(`/api/recommendations/bundles?campus_slug=${encodeURIComponent(slug)}`); }
export function getSemesterInfo(slug: string) { return request<SemesterInfo>(`/api/listing-tools/semester?campus_slug=${encodeURIComponent(slug)}`); }
export function getListingCopilot(body: { title: string; description: string; category: string; condition: string }) {
  return request<{ suggested_title: string; category: string; condition: string; detected_attributes: string[]; description_cleanup: string; assistant_note: string }>('/api/listing-tools/copilot', { method: 'POST', body: JSON.stringify(body) });
}

export function registerUser(body: { name: string; email?: string; phone?: string; password: string; verification_channel: 'email' | 'phone' }) { return request<AuthResponse>('/api/auth/register', { method: 'POST', body: JSON.stringify(body) }); }
export function loginUser(body: { identifier: string; password: string }) { return request<AuthResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify(body) }); }
export function requestOtp(body: { channel: 'email' | 'phone'; destination: string; purpose?: string }) {
  return request<{ message: string; challenge_id: number; channel?: string; purpose?: string; otp_delivery?: OTPDelivery; verified?: boolean }>('/api/auth/otp/request', { method: 'POST', body: JSON.stringify({ ...body, purpose: body.purpose || 'verification' }) });
}
export function verifyOtp(body: { channel: 'email' | 'phone'; destination: string; code: string; purpose?: string }) {
  return request<AuthResponse & { verified: boolean; channel: string; reset_token?: string }>('/api/auth/otp/verify', { method: 'POST', body: JSON.stringify({ ...body, purpose: body.purpose || 'verification' }) });
}
export function joinCampus(slug: string, studentId = '') { return request<{ message: string; verified: boolean; status: 'approved' | 'pending_review'; verification_method: string; campus_slug: string }>(`/api/campuses/${encodeURIComponent(slug)}/join`, { method: 'POST', body: JSON.stringify({ student_id: studentId }) }); }

export function getAdminOverview() { return request<{ users:number; campuses:number; active_listings:number; transactions:number; open_reports:number }>('/api/admin/overview'); }
export function getAdminCampuses() { return request<Campus[]>('/api/admin/campuses'); }
export function getAdminCourses(campusId?: number) { const q = campusId ? `?campus_id=${campusId}` : ''; return request<{ id:number; campus_id:number; code:string; name:string; semester:string }[]>(`/api/admin/courses${q}`); }
export function createAdminCourse(campusId: number, body: { code:string; name:string; semester?:string }) { return request(`/api/admin/campuses/${campusId}/courses`, { method: 'POST', body: JSON.stringify(body) }); }
export function createAdminCampus(body: { name: string; slug: string; city: string; state: string; pincode: string; email_domains: string[]; description: string; current_semester: string }) { return request<Campus>('/api/admin/campuses', { method: 'POST', body: JSON.stringify(body) }); }
export function updateAdminCampus(campusId:number, body:Partial<{name:string;slug:string;city:string;state:string;pincode:string;description:string;current_semester:string;active:boolean}>) { return request<Campus>(`/api/admin/campuses/${campusId}`, { method: 'PATCH', body: JSON.stringify(body) }); }
export function addAdminCampusDomain(campusId: number, domain: string) { return request(`/api/admin/campuses/${campusId}/domains`, { method: 'POST', body: JSON.stringify({ domain }) }); }

export function getFavorites() { return request<Listing[]>('/api/favorites'); }
export function getFavoriteIds() { return request<{ listing_ids: number[] }>('/api/favorites/ids'); }
export function saveFavorite(listingId: number) { return request<{ saved: boolean; favorites: number }>(`/api/favorites/${listingId}`, { method: 'POST' }); }
export function removeFavorite(listingId: number) { return request<{ saved: boolean; favorites: number }>(`/api/favorites/${listingId}`, { method: 'DELETE' }); }

export function applySeller(body: { display_name: string; bio: string }) { return request<Seller>('/api/sellers/apply', { method: 'POST', body: JSON.stringify(body) }); }
export function getMySeller() { return request<Seller>('/api/sellers/me'); }
export function getMyListings() { return request<Listing[]>('/api/sellers/me/listings'); }
export function getSeller(id: number) { return request<Seller>(`/api/sellers/${id}`); }
export function getSellerAnalytics() { return request<{ estimated_sales: number; active_listings: number; offers: number; views: number; saves: number; shares: number; completed_orders: number; reputation_score: number }>('/api/analytics/seller'); }
export function getCampusAnalytics(slug: string) { return request<{ members: number; active_listings: number; completed_transactions: number; total_traded: number }>(`/api/analytics/campus?campus_slug=${encodeURIComponent(slug)}`); }
export function createListing(body: unknown) { return request<Listing>('/api/listings', { method: 'POST', body: JSON.stringify(body) }); }
export function getListingCourses(id: number) { return request<{ id: number; code: string; name: string; semester: string; campus_slug: string }[]>(`/api/course-inventory/listing/${id}/courses`); }
export function attachListingCourse(listingId: number, courseId: number) { return request(`/api/course-inventory/listing/${listingId}/course/${courseId}`, { method: 'POST' }); }
export function detachListingCourse(listingId: number, courseId: number) { return request(`/api/course-inventory/listing/${listingId}/course/${courseId}`, { method: 'DELETE' }); }
export function uploadListingImage(file: File) { const form = new FormData(); form.append('file', file); return request<{ url: string; filename: string; content_type: string; size: number }>('/api/uploads/listing-image', { method: 'POST', body: form }); }

export function listConversations() { return request<Conversation[]>('/api/messages/conversations'); }
export function createConversation(listingId: number) { return request<Conversation>('/api/messages/conversations', { method: 'POST', body: JSON.stringify({ listing_id: listingId }) }); }
export function getConversation(id: number) { return request<{ conversation: Conversation; messages: Message[] }>(`/api/messages/conversations/${id}`); }
export function sendMessage(id: number, body: string) { return request<Message>(`/api/messages/conversations/${id}/messages`, { method: 'POST', body: JSON.stringify({ body }) }); }
export function blockConversation(id: number) { return request<{ blocked: boolean }>(`/api/messages/conversations/${id}/block`, { method: 'POST' }); }

export function createOffer(body: { listing_id: number; amount: number; message?: string; expires_hours?: number }) { return request<Offer>('/api/offers', { method: 'POST', body: JSON.stringify(body) }); }
export function getOffersInbox() { return request<Offer[]>('/api/offers/inbox'); }
export function getOffersSent() { return request<Offer[]>('/api/offers/sent'); }
export function acceptOffer(id: number) { return request<{ offer: Offer; transaction_id: number; listing_status: string }>(`/api/offers/${id}/accept`, { method: 'POST' }); }
export function rejectOffer(id: number) { return request<Offer>(`/api/offers/${id}/reject`, { method: 'POST' }); }
export function withdrawOffer(id: number) { return request<Offer>(`/api/offers/${id}/withdraw`, { method: 'POST' }); }

export function listWanted(slug: string) { return request<WantedPost[]>(`/api/wanted?campus_slug=${encodeURIComponent(slug)}`); }
export function createWanted(body: { campus_slug: string; title: string; category: string; description?: string; budget_min?: number; budget_max?: number; needed_by?: string }) { return request<WantedPost>('/api/wanted', { method: 'POST', body: JSON.stringify(body) }); }
export function getWantedMatches(id: number) { return request<{ listing_id: number; score: number; reason: string }[]>(`/api/wanted/${id}/matches`); }
export function closeWanted(id: number) { return request<{ id: number; status: string }>(`/api/wanted/${id}/close`, { method: 'POST' }); }

export async function getDemandRadar(slug: string) {
  const raw = await request<{ campus_slug: string; items: { category: string; wanted: number; active_listings: number; demand_supply_ratio: number; typical_accepted_price?: number | null; recent_interest_events: number }[] }>(`/api/demand/radar?campus_slug=${encodeURIComponent(slug)}`);
  return {
    campus_slug: raw.campus_slug,
    items: raw.items.map((x) => ({
      name: x.category,
      wanted: x.wanted,
      supply: x.active_listings,
      trend: x.recent_interest_events ? `+${x.recent_interest_events}` : '—',
      range: x.typical_accepted_price ? `₹${Math.round(x.typical_accepted_price * 0.85)}–₹${Math.round(x.typical_accepted_price * 1.15)}` : 'No completed-sales data',
    })),
  };
}
export function getDemandPulse(slug: string) { return request<{ active_listings: number; wanted_posts: number; completed_transactions: number; total_traded: number }>(`/api/demand/pulse?campus_slug=${encodeURIComponent(slug)}`); }
export function getPriceInsight(slug: string, category: string) { return request<{ category: string; sample_size: number; low: number | null; median: number | null; high: number | null }>(`/api/demand/price-insight?campus_slug=${encodeURIComponent(slug)}&category=${encodeURIComponent(category)}`); }

export function getSwapMatches(listingId: number) { return request<{ listing_id: number; title: string; seller_id: number; score: number }[]>(`/api/swaps/matches?have_listing_id=${listingId}`); }
export function proposeSwap(body: { offered_listing_id: number; requested_listing_id: number; message?: string }) { return request<SwapOffer>('/api/swaps', { method: 'POST', body: JSON.stringify(body) }); }
export function getSwapInbox() { return request<SwapOffer[]>('/api/swaps/inbox'); }
export function getSwapSent() { return request<SwapOffer[]>('/api/swaps/sent'); }
export function acceptSwap(id: number) { return request<SwapOffer & { transaction_id: number; transaction_status: string }>(`/api/swaps/${id}/accept`, { method: 'POST' }); }
export function rejectSwap(id: number) { return request<SwapOffer>(`/api/swaps/${id}/reject`, { method: 'POST' }); }
export function getSwapCycles(slug: string) { return request<{ path: number[]; score: number }[]>(`/api/swaps/cycles?campus_slug=${encodeURIComponent(slug)}`); }

export function getTransactions() { return request<Transaction[]>('/api/transactions'); }
export function getTransaction(id: number) { return request<Transaction>(`/api/transactions/${id}`); }
export function schedulePickup(id: number, body: { pickup_location_id?: number; pickup_address_id?: number; pickup_date: string; pickup_time: string }) { return request<{ transaction: Transaction; handoff_code?: string }>(`/api/transactions/${id}/pickup`, { method: 'POST', body: JSON.stringify(body) }); }
export function confirmHandoff(id: number, code: string) { return request<Transaction>(`/api/transactions/${id}/handoff`, { method: 'POST', body: JSON.stringify({ code }) }); }
export function cancelTransaction(id: number) { return request<Transaction>(`/api/transactions/${id}/cancel`, { method: 'POST' }); }
export function reviewTransaction(id: number, rating: number, comment: string) { return request(`/api/transactions/${id}/review`, { method: 'POST', body: JSON.stringify({ rating, comment }) }); }

export function createPaymentOrder(transactionId: number) { return request<{ payment_id: number; provider: string; order: Record<string, unknown>; key_id?: string | null }>('/api/payments/create-order', { method: 'POST', body: JSON.stringify({ transaction_id: transactionId, method: 'upi' }) }); }
export function verifyPayment(body: { provider_order_id: string; provider_payment_id: string; signature: string }) { return request<{ ok: boolean; payment_id: number; transaction_id: number; status: string }>('/api/payments/verify', { method: 'POST', body: JSON.stringify(body) }); }
export function getPayment(id: number) { return request<{ id: number; transaction_id: number; provider: string; provider_order_id: string; provider_payment_id?: string; amount: number; currency: string; method: string; status: string; signature_verified: boolean; paid_at?: string }>(`/api/payments/${id}`); }
export function refundPayment(id: number) { return request<{ ok: boolean; payment_id: number; transaction_id: number; status: string }>(`/api/payments/${id}/refund`, { method: 'POST' }); }

export function getNotifications() { return request<Notification[]>('/api/notifications'); }
export function markNotificationRead(id: number) { return request('/api/notifications/' + id + '/read', { method: 'POST' }); }

export function getAddresses() { return request<Address[]>('/api/addresses'); }
export function addAddress(body: Omit<Address, 'id'>) { return request<Address>('/api/addresses', { method: 'POST', body: JSON.stringify(body) }); }
export function updateAddress(id: number, body: Omit<Address, 'id'>) { return request<Address>(`/api/addresses/${id}`, { method: 'PATCH', body: JSON.stringify(body) }); }
export function deleteAddress(id: number) { return request(`/api/addresses/${id}`, { method: 'DELETE' }); }

export function getCourses(slug: string) { return request<{ id: number; code: string; name: string; semester: string }[]>(`/api/courses?campus_slug=${encodeURIComponent(slug)}`); }
export function enrollCourse(id: number) { return request(`/api/courses/${id}/enroll`, { method: 'POST' }); }
export function unenrollCourse(id: number) { return request(`/api/courses/${id}/enroll`, { method: 'DELETE' }); }

export function reportTarget(body: { target_type: string; target_id: number; reason: string; notes?: string }) { return request<{ id: number; status: string }>('/api/reports', { method: 'POST', body: JSON.stringify(body) }); }

export function claimLostFound(id: number, message = '') { return request<{ id: number; status: string; claimant_id?: number | null }>(`/api/lost-found/${id}/claim`, { method: 'POST', body: JSON.stringify({ message }) }); }
export function confirmLostFoundClaim(id: number) { return request<{ id: number; status: string }>(`/api/lost-found/${id}/confirm`, { method: 'POST' }); }
export function rejectLostFoundClaim(id: number) { return request<{ id: number; status: string }>(`/api/lost-found/${id}/reject-claim`, { method: 'POST' }); }
export function closeLostFound(id: number) { return request<{ id: number; status: string }>(`/api/lost-found/${id}/close`, { method: 'POST' }); }

export function listLostFound(slug: string, type = '') {
  const query = new URLSearchParams({ campus_slug: slug });
  if (type) query.set('type', type);
  return request<LostFoundItem[]>(`/api/lost-found?${query.toString()}`);
}
export function createLostFound(body: { campus_slug: string; item_type: string; title: string; description?: string; location_text?: string; item_date?: string }) {
  return request<LostFoundItem>('/api/lost-found', { method: 'POST', body: JSON.stringify(body) });
}

export function getMyCourses(slug: string) { return request<{ id: number; code: string; name: string; semester: string; campus_slug: string }[]>(`/api/courses/mine?campus_slug=${encodeURIComponent(slug)}`); }
export function getCourseListings(id: number) { return request<Listing[]>(`/api/course-inventory/course/${id}/listings`); }
export function getReports() { return request<{ id: number; reporter_id: number; target_type: string; target_id: number; reason: string; notes: string; status: string; created_at: string; resolved_at?: string | null }[]>('/api/reports'); }
export function getAdminMembers(campusId?: number, pendingOnly = true) { const q = new URLSearchParams(); if (campusId) q.set('campus_id', String(campusId)); q.set('pending_only', String(pendingOnly)); return request<{ id: number; user_id: number; name: string; email: string; phone?: string | null; campus_id: number; campus_name: string; verification_method: string; verified: boolean; joined_at: string }[]>(`/api/admin/campus-members?${q.toString()}`); }
export function approveCampusMember(id: number) { return request(`/api/admin/campus-members/${id}/approve`, { method: 'POST' }); }
export function revokeCampusMember(id: number) { return request(`/api/admin/campus-members/${id}/revoke`, { method: 'POST' }); }
export function getAdminUsers(q = '', active?: boolean) { const params = new URLSearchParams(); if (q) params.set('q', q); if (active !== undefined) params.set('active', String(active)); return request<{ id: number; name: string; email: string; phone?: string | null; role: string; active: boolean; email_verified: boolean; phone_verified: boolean; created_at: string }[]>(`/api/admin/users?${params.toString()}`); }
export function setAdminUserStatus(id: number, active: boolean) { return request(`/api/admin/users/${id}`, { method: 'PATCH', body: JSON.stringify({ active }) }); }
export function getAdminTransactions(q = '') { return request<{ id: number; listing_id: number; listing_title: string; buyer_name: string; buyer_email: string; seller_id: number; agreed_price: number; status: string; created_at: string; paid_at?: string | null; completed_at?: string | null }[]>(`/api/admin/transactions?q=${encodeURIComponent(q)}`); }
export function moderateListing(id: number) { return request(`/api/admin/listings/${id}/remove`, { method: 'POST' }); }
export function getAdminListings(q = '') { return request<{ id: number; title: string; seller_name: string; campus_name: string; price: number; status: string; created_at: string }[]>(`/api/admin/listings?q=${encodeURIComponent(q)}`); }
export function getAdminAuditLogs(q = '') { return request<{ id: number; actor_user_id?: number | null; action: string; resource_type: string; resource_id: string; detail: string; ip_address: string; created_at: string }[]>(`/api/admin/audit-logs?q=${encodeURIComponent(q)}`); }
export function resolveReport(id: number, status: 'resolved' | 'dismissed') { return request<{ id: number; status: string }>(`/api/reports/${id}/resolve`, { method: 'POST', body: JSON.stringify({ status }) }); }
