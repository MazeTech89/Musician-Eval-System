import React, { useEffect, useState } from "react";
import api from "../api/axios";
import AppHeader from "../components/AppHeader";
import { useAuth } from "../contexts/AuthContext";
import { getApiErrorMessage, validateRequired } from "../utils/form";

const Profile: React.FC = () => {
  const { user } = useAuth();
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [mfaSecret, setMfaSecret] = useState("");
  const [mfaUrl, setMfaUrl] = useState("");
  const [enableCode, setEnableCode] = useState("");
  const [disableCode, setDisableCode] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [securityError, setSecurityError] = useState("");
  const [securityMessage, setSecurityMessage] = useState("");

  useEffect(() => {
    setMfaEnabled(Boolean(user?.mfa_enabled));
  }, [user?.mfa_enabled]);

  if (!user) {
    return <div>Loading...</div>;
  }

  const resetMessages = () => {
    setSecurityError("");
    setSecurityMessage("");
  };

  const handleSetupMfa = async () => {
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
    "1. Check your account details first.",
    "2. Generate MFA setup if you have not enabled security yet.",
    "3. Verify the code in your authenticator app.",
    "4. Return to your role pages with security confirmed.",
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader title="Profile" subtitle="Check your account details and security settings." />

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
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                User Information
              </h3>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Username
                  </label>
                  <div className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-500">
                    {user.username}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Email
                  </label>
                  <div className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-500">
                    {user.email}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    First Name
                  </label>
                  <div className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-500">
                    {user.first_name}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Last Name
                  </label>
                  <div className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-500">
                    {user.last_name}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Role
                  </label>
                  <div className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-500 capitalize">
                    {user.role}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Status
                  </label>
                  <div className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-500">
                    {user.is_active ? "Active" : "Inactive"}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="bg-white shadow rounded-lg mt-6">
            <div className="px-4 py-5 sm:p-6 space-y-4">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Security</h3>
              <p className="text-sm text-gray-600">
                Multi-factor authentication status:{" "}
                <span className={mfaEnabled ? "text-green-700 font-medium" : "text-gray-700 font-medium"}>
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
                    <label htmlFor="mfa-enable-code" className="block text-sm font-medium text-gray-700 mb-1">
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
                    <label htmlFor="mfa-disable-code" className="block text-sm font-medium text-gray-700 mb-1">
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
