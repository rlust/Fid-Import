/**
 * Portfolio Data Source
 * Supports multiple data loading strategies:
 * 1. Local import (bundled with app) - fastest
 * 2. GitHub raw URL (always fresh) - requires public repo
 * 3. GitHub API (private repos) - requires token
 */

import portfolioDataLocal from '@/data/portfolio-latest.json';
import { Snapshot } from './portfolioService';

export type DataSource = 'local' | 'github-raw' | 'github-api';

interface DataSourceConfig {
  source: DataSource;
  githubRepo?: string;
  githubBranch?: string;
  githubPath?: string;
  githubToken?: string;
}

const DEFAULT_CONFIG: DataSourceConfig = {
  source: 'local', // Default to bundled data
  githubRepo: 'rlust/fidelity-portfolio-18884',
  githubBranch: 'main',
  githubPath: 'src/data/portfolio-latest.json',
};

export class PortfolioDataSource {
  private config: DataSourceConfig;
  private cache: Snapshot[] | null = null;
  private cacheTimestamp: number = 0;
  private cacheDuration: number = 5 * 60 * 1000; // 5 minutes

  constructor(config: Partial<DataSourceConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Load portfolio data from configured source
   */
  async load(): Promise<Snapshot[]> {
    // Check cache first
    if (this.cache && Date.now() - this.cacheTimestamp < this.cacheDuration) {
      return this.cache;
    }

    let data: Snapshot[];

    switch (this.config.source) {
      case 'github-raw':
        data = await this.loadFromGitHubRaw();
        break;
      case 'github-api':
        data = await this.loadFromGitHubAPI();
        break;
      case 'local':
      default:
        data = this.loadFromLocal();
        break;
    }

    // Update cache
    this.cache = data;
    this.cacheTimestamp = Date.now();

    return data;
  }

  /**
   * Load from local import (bundled with app)
   * Fastest option, no network request
   */
  private loadFromLocal(): Snapshot[] {
    return portfolioDataLocal as unknown as Snapshot[];
  }

  /**
   * Load from GitHub raw URL
   * Works for public repositories
   * Always gets fresh data from GitHub
   */
  private async loadFromGitHubRaw(): Promise<Snapshot[]> {
    const { githubRepo, githubBranch, githubPath } = this.config;

    if (!githubRepo || !githubBranch || !githubPath) {
      throw new Error('GitHub configuration incomplete');
    }

    const url = `https://raw.githubusercontent.com/${githubRepo}/${githubBranch}/${githubPath}`;

    try {
      const response = await fetch(url, {
        cache: 'no-cache', // Always get fresh data
      });

      if (!response.ok) {
        throw new Error(`GitHub fetch failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data as Snapshot[];
    } catch (error) {
      console.error('Failed to load from GitHub raw URL:', error);
      // Fallback to local data
      console.warn('Falling back to local data');
      return this.loadFromLocal();
    }
  }

  /**
   * Load from GitHub API
   * Works for private repositories (requires token)
   * More reliable but requires authentication
   */
  private async loadFromGitHubAPI(): Promise<Snapshot[]> {
    const { githubRepo, githubBranch, githubPath, githubToken } = this.config;

    if (!githubRepo || !githubBranch || !githubPath) {
      throw new Error('GitHub configuration incomplete');
    }

    const url = `https://api.github.com/repos/${githubRepo}/contents/${githubPath}?ref=${githubBranch}`;

    const headers: HeadersInit = {
      Accept: 'application/vnd.github.v3.raw',
    };

    if (githubToken) {
      headers.Authorization = `token ${githubToken}`;
    }

    try {
      const response = await fetch(url, { headers });

      if (!response.ok) {
        throw new Error(`GitHub API failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data as Snapshot[];
    } catch (error) {
      console.error('Failed to load from GitHub API:', error);
      // Fallback to local data
      console.warn('Falling back to local data');
      return this.loadFromLocal();
    }
  }

  /**
   * Clear cache and force reload on next request
   */
  clearCache() {
    this.cache = null;
    this.cacheTimestamp = 0;
  }

  /**
   * Get cache status
   */
  getCacheStatus() {
    return {
      isCached: this.cache !== null,
      age: this.cache ? Date.now() - this.cacheTimestamp : 0,
      remainingTime: this.cache ? Math.max(0, this.cacheDuration - (Date.now() - this.cacheTimestamp)) : 0,
    };
  }
}

/**
 * Create data source with environment-based configuration
 */
export function createDataSource(): PortfolioDataSource {
  const config: Partial<DataSourceConfig> = {
    // Read from environment variables (set in .env file)
    source: (import.meta.env.VITE_DATA_SOURCE as DataSource) || 'local',
    githubRepo: import.meta.env.VITE_GITHUB_REPO || 'rlust/fidelity-portfolio-18884',
    githubBranch: import.meta.env.VITE_GITHUB_BRANCH || 'main',
    githubPath: import.meta.env.VITE_GITHUB_PATH || 'src/data/portfolio-latest.json',
    githubToken: import.meta.env.VITE_GITHUB_TOKEN, // Optional, for private repos
  };

  return new PortfolioDataSource(config);
}

// Export singleton instance
export const dataSource = createDataSource();
