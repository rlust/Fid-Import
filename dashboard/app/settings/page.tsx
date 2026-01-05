'use client';

import { Settings as SettingsIcon, User, Bell, Shield, Database, Clock, RefreshCw, CheckCircle2 } from 'lucide-react';
import { useSyncStatus, useManualSync } from '@/hooks/useSync';
import { formatDistanceToNow } from 'date-fns';

export default function SettingsPage() {
  const { data: syncStatus, isLoading: statusLoading } = useSyncStatus();
  const manualSync = useManualSync();

  const handleManualSync = () => {
    manualSync.mutate();
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Manage your account and application preferences
        </p>
      </div>

      {/* Settings Sections */}
      <div className="space-y-6">
        {/* Account Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <User className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Account</h2>
          </div>
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            Account management features coming soon. You'll be able to update your profile, change password, and manage connected accounts.
          </p>
        </div>

        {/* Scheduled Updates */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Bell className="h-6 w-6 text-green-600 dark:text-green-400" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Portfolio Updates</h2>
            </div>
            {syncStatus?.agent_active && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Active
              </span>
            )}
          </div>

          {statusLoading ? (
            <div className="text-gray-500 dark:text-gray-400 text-sm">Loading sync status...</div>
          ) : syncStatus ? (
            <div className="space-y-4">
              {/* Sync Schedule */}
              <div className="flex items-start justify-between py-3 border-b border-gray-200 dark:border-gray-700">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <Clock className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">Sync Schedule</span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 ml-6">
                    {syncStatus.schedule}
                  </p>
                </div>
              </div>

              {/* Last Sync */}
              <div className="flex items-start justify-between py-3 border-b border-gray-200 dark:border-gray-700">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <CheckCircle2 className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">Last Update</span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 ml-6">
                    {syncStatus.last_sync
                      ? formatDistanceToNow(new Date(syncStatus.last_sync), { addSuffix: true })
                      : 'Never'}
                  </p>
                </div>
              </div>

              {/* Next Scheduled Sync */}
              <div className="flex items-start justify-between py-3 border-b border-gray-200 dark:border-gray-700">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <Clock className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">Next Scheduled Update</span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 ml-6">
                    {syncStatus.next_scheduled_sync
                      ? formatDistanceToNow(new Date(syncStatus.next_scheduled_sync), { addSuffix: true })
                      : 'Not scheduled'}
                  </p>
                </div>
              </div>

              {/* Manual Sync Button */}
              <div className="pt-2">
                <button
                  onClick={handleManualSync}
                  disabled={manualSync.isPending}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  <RefreshCw className={`h-4 w-4 ${manualSync.isPending ? 'animate-spin' : ''}`} />
                  <span>{manualSync.isPending ? 'Syncing...' : 'Update Now'}</span>
                </button>
                {manualSync.isSuccess && (
                  <p className="mt-2 text-sm text-green-600 dark:text-green-400">
                    Portfolio sync initiated! Data will update shortly.
                  </p>
                )}
                {manualSync.isError && (
                  <p className="mt-2 text-sm text-red-600 dark:text-red-400">
                    Failed to trigger sync. Please try again.
                  </p>
                )}
              </div>
            </div>
          ) : (
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Unable to load sync status.
            </p>
          )}
        </div>

        {/* Privacy & Security */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Shield className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Privacy & Security</h2>
          </div>
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            Manage your privacy settings, two-factor authentication, and API access tokens.
          </p>
        </div>

        {/* Data Management */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Database className="h-6 w-6 text-orange-600 dark:text-orange-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Data Management</h2>
          </div>
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            Export your data, import from other platforms, and manage data retention settings.
          </p>
        </div>
      </div>

      {/* Info */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <div className="flex items-center space-x-3 mb-2">
          <SettingsIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300">
            Settings Under Development
          </h3>
        </div>
        <p className="text-sm text-blue-800 dark:text-blue-400">
          We're actively building out these settings features. Check back soon for updates!
        </p>
      </div>
    </div>
  );
}
