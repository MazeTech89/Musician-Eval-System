import React from "react";
import AppHeader from "./AppHeader";
import { useAuth } from "../contexts/AuthContext";

interface ProtectedLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}

/**
 * ProtectedLayout wraps protected page content with consistent header navigation
 * for both admin and musician account types
 */
const ProtectedLayout: React.FC<ProtectedLayoutProps> = ({
  children,
  title,
  subtitle,
}) => {
  const { user } = useAuth();

  // Only show layout if user is authenticated
  if (!user) {
    return <>{children}</>;
  }

  return (
    <>
      <AppHeader title={title} subtitle={subtitle} />
      <main
        className="min-h-screen"
        style={{ backgroundColor: "var(--bg-page)" }}
      >
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </>
  );
};

export default ProtectedLayout;
