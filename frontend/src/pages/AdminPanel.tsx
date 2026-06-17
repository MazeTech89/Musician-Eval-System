import React, { useState, useEffect } from "react";
import api from "../api/axios";
import { useAuth } from "../contexts/AuthContext";

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  role: string;
  is_active: boolean;
}

const AdminPanel: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editEmail, setEditEmail] = useState("");
  const [editFirstName, setEditFirstName] = useState("");
  const [editLastName, setEditLastName] = useState("");
  const [editRole, setEditRole] = useState("musician");
  const [editIsActive, setEditIsActive] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deletingUserId, setDeletingUserId] = useState<number | null>(null);
  const [confirmDeleteUserId, setConfirmDeleteUserId] = useState<number | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const openEditUser = (userToEdit: User) => {
    setEditingUser(userToEdit);
    setEditEmail(userToEdit.email);
    setEditFirstName(userToEdit.first_name ?? "");
    setEditLastName(userToEdit.last_name ?? "");
    setEditRole(userToEdit.role);
    setEditIsActive(userToEdit.is_active);
    setSuccessMessage(null);
    setError(null);
  };

  const confirmDeleteUser = (userId: number) => {
    setConfirmDeleteUserId(userId);
    setError(null);
    setSuccessMessage(null);
  };

  const cancelDelete = () => {
    setConfirmDeleteUserId(null);
    setError(null);
  };

  const closeEdit = () => {
    setEditingUser(null);
    setError(null);
    setSuccessMessage(null);
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) {
      return;
    }

    setSaving(true);
    try {
      await api.put(`/users/${editingUser.id}`, {
        email: editEmail,
        first_name: editFirstName || null,
        last_name: editLastName || null,
        role: editRole,
        is_active: editIsActive,
      });

      const response = await api.get("/users");
      setUsers(response.data);
      setSuccessMessage("User updated successfully.");
      closeEdit();
    } catch (err: unknown) {
      console.error("Failed to update user:", err);
      const message =
        err instanceof Error ? err.message : "Failed to update user";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    setDeletingUserId(userId);
    setError(null);
    setSuccessMessage(null);

    try {
      await api.delete(`/users/${userId}`);
      const response = await api.get("/users");
      setUsers(response.data);
      setSuccessMessage("User deactivated successfully.");
      cancelDelete();
    } catch (err: unknown) {
      console.error("Failed to deactivate user:", err);
      const message =
        err instanceof Error ? err.message : "Failed to deactivate user";
      setError(message);
    } finally {
      setDeletingUserId(null);
    }
  };

  useEffect(() => {
    if (!user || user.role !== "admin") {
      setLoading(false);
      return;
    }

    const fetchUsers = async () => {
      try {
        const response = await api.get("/users");
        setUsers(response.data);
      } catch (err: unknown) {
        console.error("Failed to fetch users:", err);
        const message =
          err instanceof Error ? err.message : "Failed to load users";
        setError(message);
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

  if (error) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-red-600 text-center">
          <p className="text-lg font-semibold">Error</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Admin Panel
              </h1>
            </div>
            <div className="flex items-center">
              <a href="/" className="text-indigo-600 hover:text-indigo-500">
                Back to Dashboard
              </a>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                User Management
              </h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Manage system users and their roles
              </p>
            </div>
            {successMessage && (
              <div className="px-4 py-4 sm:px-6">
                <div className="rounded-md bg-green-50 p-4">
                  <p className="text-sm text-green-700">{successMessage}</p>
                </div>
              </div>
            )}
            {confirmDeleteUserId !== null && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 py-6">
                <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Confirm Deactivation
                  </h3>
                  <p className="mt-2 text-sm text-gray-600">
                    This will deactivate the user and prevent sign-in. Are you sure?
                  </p>
                  <div className="mt-6 flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={cancelDelete}
                      className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteUser(confirmDeleteUserId)}
                      disabled={deletingUserId === confirmDeleteUserId}
                      className="inline-flex justify-center rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-red-700 disabled:opacity-50"
                    >
                      {deletingUserId === confirmDeleteUserId
                        ? "Deactivating..."
                        : "Deactivate user"}
                    </button>
                  </div>
                </div>
              </div>
            )}
            {editingUser && (
              <div className="px-4 py-4 sm:px-6 bg-gray-50 border-t border-b border-gray-200">
                <div className="mb-4">
                  <h4 className="text-md font-semibold text-gray-900">
                    Edit user: {editingUser.username}
                  </h4>
                  <p className="text-sm text-gray-500">
                    Update email, name, role, or active status.
                  </p>
                </div>
                <form onSubmit={handleUpdateUser} className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Email
                      </label>
                      <input
                        value={editEmail}
                        onChange={(e) => setEditEmail(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        type="email"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Role
                      </label>
                      <select
                        value={editRole}
                        onChange={(e) => setEditRole(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 bg-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      >
                        <option value="musician">Musician</option>
                        <option value="evaluator">Evaluator</option>
                        <option value="admin">Admin</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        First Name
                      </label>
                      <input
                        value={editFirstName}
                        onChange={(e) => setEditFirstName(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        type="text"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Last Name
                      </label>
                      <input
                        value={editLastName}
                        onChange={(e) => setEditLastName(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        type="text"
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <input
                        type="checkbox"
                        checked={editIsActive}
                        onChange={(e) => setEditIsActive(e.target.checked)}
                        className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      Active
                    </label>
                  </div>
                  {error && (
                    <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
                      {error}
                    </div>
                  )}
                  <div className="flex flex-wrap gap-3">
                    <button
                      type="submit"
                      disabled={saving}
                      className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                    >
                      {saving ? "Saving..." : "Save changes"}
                    </button>
                    <button
                      type="button"
                      onClick={closeEdit}
                      className="inline-flex justify-center rounded-md border border-gray-300 bg-white py-2 px-4 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}
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
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize bg-blue-100 text-blue-800">
                          {user.role}
                        </span>
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            user.is_active
                              ? "bg-green-100 text-green-800"
                              : "bg-red-100 text-red-800"
                          }`}
                        >
                          {user.is_active ? "Active" : "Inactive"}
                        </span>
                        <button
                          onClick={() => openEditUser(user)}
                          className="text-indigo-600 hover:text-indigo-900 text-sm"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => confirmDeleteUser(user.id)}
                          className="text-red-600 hover:text-red-900 text-sm"
                        >
                          Deactivate
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
