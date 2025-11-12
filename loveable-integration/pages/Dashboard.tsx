/**
 * Main Portfolio Dashboard Page
 * Combines all portfolio components into a comprehensive dashboard
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PortfolioSummary } from '@/components/PortfolioSummary';
import { HoldingsTable } from '@/components/HoldingsTable';
import { PortfolioChart } from '@/components/PortfolioChart';
import { SectorAllocation } from '@/components/SectorAllocation';
import { RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

// Create a query client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 60, // 1 hour
      gcTime: 1000 * 60 * 60 * 24, // 24 hours
      refetchOnWindowFocus: false,
    },
  },
});

function DashboardContent() {
  const handleRefresh = () => {
    queryClient.invalidateQueries();
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Portfolio Dashboard</h1>
              <p className="text-muted-foreground">Fidelity Portfolio Tracker</p>
            </div>
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Data
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* Portfolio Summary Cards */}
          <section>
            <PortfolioSummary />
          </section>

          {/* Charts Section */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PortfolioChart />
            <SectorAllocation />
          </section>

          {/* Holdings Table */}
          <section>
            <HoldingsTable />
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t mt-12">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <p>
              Data updates daily at 6:00 PM via automated export from Fidelity Portfolio Tracker
            </p>
            <p>
              Last sync: <span className="font-medium">Check portfolio summary card</span>
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

/**
 * Main Dashboard Component with QueryClientProvider
 */
export function Dashboard() {
  return (
    <QueryClientProvider client={queryClient}>
      <DashboardContent />
    </QueryClientProvider>
  );
}

export default Dashboard;
