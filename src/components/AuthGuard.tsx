"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Navigation from "@/components/Navigation";
import { supabase } from "@/lib/supabase";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const router = useRouter();
    const [loading, setLoading] = useState(pathname !== "/login");

    useEffect(() => {
        if (pathname === "/login") {
            setLoading(false);
            return;
        }

        let active = true;
        supabase.auth.getSession().then(({ data }) => {
            if (!active) return;
            if (!data.session) {
                router.replace("/login");
            } else {
                setLoading(false);
            }
        });

        const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
            if (!session) {
                router.replace("/login");
            } else {
                setLoading(false);
            }
        });

        return () => {
            active = false;
            listener.subscription.unsubscribe();
        };
    }, [pathname, router]);

    if (pathname === "/login") return <>{children}</>;
    if (loading) return <div className="p-10 text-center">Verificando sessão...</div>;

    return (
        <>
            <Navigation />
            <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">{children}</main>
        </>
    );
}