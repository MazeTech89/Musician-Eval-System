import React, { useEffect, useState } from "react";
import api from "../api/axios";
import AppHeader from "../components/AppHeader";
import { useAuth } from "../contexts/AuthContext";
import { getApiErrorMessage, validateEmail, validateRequired } from "../utils/form";

const SKILL_LEVEL_OPTIONS = [
  { value: "", label: "Select skill level" },
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
  { value: "expert", label: "Expert" },
];

const Profile: React.FC = () => {
  const { user, refreshUser } = useAuth();
  // Editable profile fields used by task recommendation and assignment workflows.
  const [profileForm, setProfileForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    instrument_type: "",
    skill_level: "",
    availability: "",
  });
  const [profileError, setProfileError] = useState("");
  const [profileMessage, setProfileMessage] = useState("");
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [mfaSecret, setMfaSecret] = useState("");
  const [mfaUrl, setMfaUrl] = useState("");
  const [enableCode, setEnableCode] = useState("");
  const [disableCode, setDisableCode] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [securityError, setSecurityError] = useState("");
  const [securityMessage, setSecurityMessage] = useState("");

  useEffect(() => {
    // Keep local form state synchronized with the authenticated user payload.
    if (!user) {
      return;
    }

    setProfileForm({
      first_name: user.first_name || "",
      last_name: user.last_name || "",
      email: user.email || "",
      instrument_type: user.instrument_type || "",
      skill_level: user.skill_level || "",
      availability: user.availability || "",
    });
    setMfaEnabled(Boolean(user.mfa_enabled));
  }, [user]);

  if (!user) {
    return <div>Loading...</div>;
  }

  const resetMessages = () => {
    // Centralized reset avoids stale security notices between MFA actions.
    setSecurityError("");
    setSecurityMessage("");
  };

  const handleProfileChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) => {
    setProfileForm((current) => ({
      ...current,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSaveProfile = async () => {
    // Validate required identity fields and email format before persistence.
    const emailError = validateEmail(profileForm.email);
    const firstNameError = validateRequired(profileForm.first_name, "First name");
    const lastNameError = validateRequired(profileForm.last_name, "Last name");

    if (emailError || firstNameError || lastNameError) {
      setProfileError(emailError || firstNameError || lastNameError || "Please fix the profile fields.");
      return;
    }

    setProfileError("");
    setProfileMessage("");
    setIsSavingProfile(true);
    try {
      // Optional profile fields are normalized to null for consistent backend storage.
      await api.put("/auth/me", {
        email: profileForm.email,
        first_name: profileForm.first_name,
        last_name: profileForm.last_name,
        instrument_type: profileForm.instrument_type || null,
        skill_level: profileForm.skill_level || null,
        availability: profileForm.availability || null,
      });
      await refreshUser();
      setProfileMessage("Profile updated successfully.");
    } catch (err: unknown) {
      setProfileError(getApiErrorMessage(err, "Unable to save profile."));
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleSetupMfa = async () => {
    // Step 1 of MFA: generate secret + OTP URL for authenticator enrollment.
    resetMessages();
    setIsSubmitting(true);
    try {
      const response = await api.post("/auth/mfa/setup");
      setMfaSecret(response.data.secret);
      setMfaUrl(response.data.otpauth_url);
      setSecurityMessage("MFA secret generated. Add it to your authenticator and verify with a code.");
    } catch (err: unknown) {
      setSecurityError(getApiErrorMessage(err, "Unable to generate MFA setup details."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEnableMfa = async () => {
    // Step 2 of MFA: verify TOTP code before enabling account protection.
    const codeError = validateRequired(enableCode, "MFA code");
    if (codeError) {
      setSecurityError(codeError);
      return;
    }

    resetMessages();
    setIsSubmitting(true);
    try {
      await api.post("/auth/mfa/enable", { code: enableCode });
      setMfaEnabled(true);
      setEnableCode("");
      setMfaSecret("");
      setMfaUrl("");
      setSecurityMessage("MFA has been enabled for your account.");
    } catch (err: unknown) {
      setSecurityError(getApiErrorMessage(err, "Unable to enable MFA."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDisableMfa = async () => {
    // Disable MFA requires a fresh code to prevent unauthorized deactivation.
    const codeError = validateRequired(disableCode, "MFA code");
    if (codeError) {
      setSecurityError(codeError);
      return;
    }

    resetMessages();
    setIsSubmitting(true);
    try {
      await api.post("/auth/mfa/disable", { code: disableCode });
      setMfaEnabled(false);
      setDisableCode("");
      setSecurityMessage("MFA has been disabled for your account.");
    } catch (err: unknown) {
      setSecurityError(getApiErrorMessage(err, "Unable to disable MFA."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const workflowSteps = [
    "1. Review and update your profile details first.",
    "2. Save your instrument, skill, and availability information.",
    "3. Generate MFA setup if you have not enabled security yet.",
    "4. Return to your role pages with your profile confirmed.",
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader title="Profile" subtitle="Check your account details, profile fields, and security settings." />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0 space-y-6">
          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Your workflow</h2>
            <ol className="space-y-2 text-sm text-gray-700">
              {workflowSteps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </section>

          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6 space-y-4">
              <h3 className="text-lg leading-6 font-medium text-gray-900">User Information</h3>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Username</label>
                  <div className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-500">
                    {user.username}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Role</label>
                  <div className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-500 capitalize">
                    {user.role}
                  </div>
                </div>
                <div>
                  <label htmlFor="profile-email" className="block text-sm font-medium text-gray-700">
                    Email
                  </label>
                  <input
                    id="profile-email"
                    name="email"
                    type="email"
                    value={profileForm.email}
                    onChange={handleProfileChange}
                    className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
                <div>
                  <label
                    htmlFor="profile-first-name"
                    className="block text-sm font-medium text-gray-700"
                  >
                    First Name
                  </label>
                  <input
                    id="profile-first-name"
                    name="first_name"
                    type="text"
                    value={profileForm.first_name}
                    onChange={handleProfileChange}
                    className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
                <div>
                  <label
                    htmlFor="profile-last-name"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Last Name
                  </label>
                  <input
                    id="profile-last-name"
                    name="last_name"
                    type="text"
                    value={profileForm.last_name}
                    onChange={handleProfileChange}
                    className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
                <div>
                  <label
                    htmlFor="profile-instrument-type"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Instrument Type
                  </label>
                  <input
                    id="profile-instrument-type"
                    name="instrument_type"
                    type="text"
                    value={profileForm.instrument_type}
                    onChange={handleProfileChange}
                    className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="e.g. Piano, Guitar, Violin"
                  />
                </div>
                <div>
                  <label
                    htmlFor="profile-skill-level"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Skill Level
                  </label>
                  <select
                    id="profile-skill-level"
                    name="skill_level"
                    value={profileForm.skill_level}
                    onChange={handleProfileChange}
                    className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2"
                  >
                    {SKILL_LEVEL_OPTIONS.map((option) => (
                      <option key={option.value || "blank"} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <label
                    htmlFor="profile-availability"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Availability
                  </label>
                  <textarea
                    id="profile-availability"
                    name="availability"
                    rows={3}
                    value={profileForm.availability}
                    onChange={handleProfileChange}
                    className="mt-1 w-full border border-gray-300 rounded-md px-3 py-2"
                    placeholder="Share your typical availability window"
                  />
                </div>
              </div>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <button
                  type="button"
                  onClick={() => void handleSaveProfile()}
                  disabled={isSavingProfile}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {isSavingProfile ? "Saving..." : "Save profile"}
                </button>
                <div className="text-sm text-gray-600">
                  Status: {user.is_active ? "Active" : "Inactive"}
                </div>
              </div>
              {profileError ? <p className="text-sm text-red-600">{profileError}</p> : null}
              {profileMessage ? <p className="text-sm text-green-600">{profileMessage}</p> : null}
            </div>
          </div>

          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Security</h3>
              <p className="text-sm text-gray-600">
                Multi-factor authentication status:{" "}
                <span
                  className={
                    mfaEnabled ? "text-green-700 font-medium" : "text-gray-700 font-medium"
                  }
                >
                  {mfaEnabled ? "Enabled" : "Disabled"}
                </span>
              </p>

              {!mfaEnabled ? (
                <div className="space-y-3">
                  <button
                    type="button"
                    onClick={handleSetupMfa}
                    disabled={isSubmitting}
                    className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                  >
                    Generate MFA setup
                  </button>

                  {mfaSecret ? (
                    <div className="p-3 rounded-md bg-gray-50 border border-gray-200">
                      <p className="text-sm text-gray-700 break-all">
                        <span className="font-medium">Secret:</span> {mfaSecret}
                      </p>
                      <p className="text-sm text-gray-700 break-all mt-1">
                        <span className="font-medium">OTP URL:</span> {mfaUrl}
                      </p>
                    </div>
                  ) : null}

                  <div>
                    <label
                      htmlFor="mfa-enable-code"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      MFA code
                    </label>
                    <input
                      id="mfa-enable-code"
                      type="text"
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      value={enableCode}
                      onChange={(e) => setEnableCode(e.target.value)}
                      className="w-full max-w-xs border border-gray-300 rounded-md px-3 py-2"
                      placeholder="6-digit code"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleEnableMfa}
                    disabled={isSubmitting}
                    className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    Enable MFA
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <label
                      htmlFor="mfa-disable-code"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      MFA code to disable
                    </label>
                    <input
                      id="mfa-disable-code"
                      type="text"
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      value={disableCode}
                      onChange={(e) => setDisableCode(e.target.value)}
                      className="w-full max-w-xs border border-gray-300 rounded-md px-3 py-2"
                      placeholder="6-digit code"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleDisableMfa}
                    disabled={isSubmitting}
                    className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50"
                  >
                    Disable MFA
                  </button>
                </div>
              )}

              {securityError ? <p className="text-sm text-red-600">{securityError}</p> : null}
              {securityMessage ? <p className="text-sm text-green-600">{securityMessage}</p> : null}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Profile;
