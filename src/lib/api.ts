
export const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://zufar.onrender.com";

export async function health(): Promise<boolean> {
  try {
    const r = await fetch(`${API_BASE}/healthz`);
    return r.ok;
  } catch {
    return false;
  }
}

export type RegisterPayload = {
  email: string;
  password: string;
  full_name?: string | null;
};

export async function registerUser(payload: RegisterPayload) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}
