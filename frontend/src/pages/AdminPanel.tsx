import React, { useState, useEffect } from "react";
import api from "../api/axios";
import AppHeader from "../components/AppHeader";
import { useAuth } from "../contexts/AuthContext";
import { getApiErrorMessage } from "../utils/form";

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  role: string;
  is_active: boolean;
}

interface UserDraft {
  role: string;
  is_active: boolean;
}

const ROLE_OPTIONS = ["admin", "evaluator", "musician", "moderator", "analyst"];

const AdminPanel: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<number, UserDraft>>({});
  const [savingUserId, setSavingUserId] = useState<number | null>(null);
  const [deletingUserId, setDeletingUserId] = useState<number | null>(null);

  useEffect(() => {
    if (!user || user.role !== "admin") {
      setLoading(false);
      return;
    }

    const fetchUsers = async () => {
      try {
        const response = await api.get("/auth/users");
        setUsers(response.data);
        setDrafts(
          Object.fromEntries(
            response.data.map((loadedUser: User) => [
              loadedUser.id,
              { role: loadedUser.role, is_active: loadedUser.is_active },
            ]),
          ),
        );
      } catch (err: unknown) {
        console.error("Failed to fetch users:", err);
        setLoadError(getApiErrorMessage(err, "Failed to load users"));
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, [user]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        Loading...
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-600">
            Please log in to access admin panel
          </p>
        </div>
      </div>
    );
  }

  if (user.role !== "admin") {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center">
          <p className="text-lg font-semibold text-red-600">Access Denied</p>
          <p className="text-gray-600">
            You need admin privileges to access this page
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        Loading users...
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-red-600 text-center">
          <p className="text-lg font-semibold">Error</p>
          <p>{loadError}</p>
        </div>
      </div>
    );
  }

  const handleDraftChange = (
    userId: number,
    field: keyof UserDraft,
    value: string | boolean,
  ) => {
    setDrafts((current) => ({
      ...current,
      [userId]: {
        ...(current[userId] || { role: "musician", is_active: true }),
        [field]: value,
      },
    }));
  };

  const handleSaveUser = async (targetUser: User) => {
    const draft = drafts[targetUser.id];
    if (!draft) {
      return;
    }

    setSavingUserId(targetUser.id);
    setActionError(null);
    setSuccessMessage(null);

    try {
      const response = await api.put<User>(`/auth/users/${targetUser.id}`, {
        role: draft.role,
        is_active: draft.is_active,
      });
      const updatedUser = response.data;
      setUsers((current) =>
        current.map((existingUser) =>
          existingUser.id === updatedUser.id ? updatedUser : existingUser,
        ),
      );
      setDrafts((current) => ({
        ...current,
        [updatedUser.id]: {
          role: updatedUser.role,
          is_active: updatedUser.is_active,
        },
      }));
      setSuccessMessage(`Updated ${updatedUser.username} successfully.`);
    } catch (err: unknown) {
      setActionError(getApiErrorMessage(err, "Failed to update user"));
    } finally {
      setSavingUserId(null);
    }
  };

  const handleDeleteUser = async (targetUser: User) => {
    if (
      !window.confirm(
        `Delete account for ${targetUser.username}? This permanently removes the account and owned records.`,
      )
    ) {
      return;
    }

    setDeletingUserId(targetUser.id);
    setActionError(null);
    setSuccessMessage(null);

    try {
      await api.delete(`/auth/users/${targetUser.id}`);
      setUsers((current) => current.filter((existingUser) => existingUser.id !== targetUser.id));
      setDrafts((current) => {
        const nextDrafts = { ...current };
        delete nextDrafts[targetUser.id];
        return nextDrafts;
      });
      setSuccessMessage(`Deleted ${targetUser.username} successfully.`);
    } catch (err: unknown) {
      setActionError(getApiErrorMessage(err, "Failed to delete user"));
    } finally {
      setDeletingUserId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader
        title="Admin Panel"
        subtitle="Manage users, roles, and access to the system."
      />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0 space-y-4">
          {successMessage ? (
            <div className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
              {successMessage}
            </div>
          ) : null}
          {actionError ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {actionError}
            </div>
          ) : null}
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                User Management
              </h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Manage system users and their roles
              </p>
            </div>
            <ul className="divide-y divide-gray-200">
              {users.map((user) => (
                <li key={user.id}>
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                            <span className="text-gray-700 font-semibold">
                              {user.first_name
                                ? user.first_name[0]
                                : user.username[0]}
                              {user.last_name ? user.last_name[0] : ""}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {user.first_name && user.last_name
                              ? `${user.first_name} ${user.last_name}`
                              : user.username}
                          </div>
                          <div className="text-sm text-gray-500">
                            @{user.username} • {user.email}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <select
                          value={drafts[user.id]?.role ?? user.role}
                          onChange={(event) => handleDraftChange(user.id, "role", event.target.value)}
                          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
                        >
                          {ROLE_OPTIONS.map((roleOption) => (
                            <option key={roleOption} value={roleOption}>
                              {roleOption}
                            </option>
                          ))}
                        </select>
                        <select
                          value={String(drafts[user.id]?.is_active ?? user.is_active)}
                          onChange={(event) =>
                            handleDraftChange(user.id, "is_active", event.target.value === "true")
                          }
                          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
                        >
                          <option value="true">Active</option>
                          <option value="false">Inactive</option>
                        </select>
                        <button
                          type="button"
                          onClick={() => void handleSaveUser(user)}
                          disabled={savingUserId === user.id}
                          className="text-indigo-600 hover:text-indigo-900 text-sm disabled:opacity-50"
                        >
                          {savingUserId === user.id ? "Saving..." : "Save"}
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleDeleteUser(user)}
                          disabled={deletingUserId === user.id}
                          className="text-red-600 hover:text-red-800 text-sm disabled:opacity-50"
                        >
                          {deletingUserId === user.id ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminPanel;
