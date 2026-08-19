import { supabase } from "@/lib/supabase";

export class ApiError extends Error {
    status: number;

    constructor(status: number, message: string) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}

export async function apiFetch<T>(
    input: RequestInfo | URL,
    init?: RequestInit,
): Promise<T> {
    const { data } = await supabase.auth.getSession();
    const headers = new Headers(init?.headers);

    if (data.session?.access_token) {
        headers.set("Authorization", `Bearer ${data.session.access_token}`);
    }

    const response = await fetch(input, { ...init, headers });
    const payload = await response.json().catch(() => null) as {
        detail?: string;
        message?: string;
    } | null;

    if (!response.ok) {
        throw new ApiError(
            response.status,
            payload?.detail || payload?.message || "Não foi possível concluir a operação.",
        );
    }

    return payload as T;
}