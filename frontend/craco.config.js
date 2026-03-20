// craco.config.js
const path = require("path");
require("dotenv").config();

// Check if we're in development/preview mode (not production build)
// Craco sets NODE_ENV=development for start, NODE_ENV=production for build
const isDevServer = process.env.NODE_ENV !== "production";

// Environment variable overrides
const config = {
  enableHealthCheck: process.env.ENABLE_HEALTH_CHECK === "true",
};

// Conditionally load health check modules only if enabled
let WebpackHealthPlugin;
let setupHealthEndpoints;
let healthPluginInstance;

if (config.enableHealthCheck) {
  WebpackHealthPlugin = require("./plugins/health-check/webpack-health-plugin");
  setupHealthEndpoints = require("./plugins/health-check/health-endpoints");
  healthPluginInstance = new WebpackHealthPlugin();
}

let webpackConfig = {
  eslint: {
    configure: {
      extends: ["plugin:react-hooks/recommended"],
      rules: {
        "react-hooks/rules-of-hooks": "error",
        "react-hooks/exhaustive-deps": "warn",
      },
    },
  },
  webpack: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
    configure: (webpackConfig) => {

      // Add ignored patterns to reduce watched directories
        webpackConfig.watchOptions = {
          ...webpackConfig.watchOptions,
          ignored: [
            '**/node_modules/**',
            '**/.git/**',
            '**/build/**',
            '**/dist/**',
            '**/coverage/**',
            '**/public/**',
        ],
      };

      // Add health check plugin to webpack if enabled
      if (config.enableHealthCheck && healthPluginInstance) {
        webpackConfig.plugins.push(healthPluginInstance);
      }
      return webpackConfig;
    },
  },
};

webpackConfig.devServer = (devServerConfig) => {
  // Bot detection for SSR metadata - runs before historyApiFallback
  const BOT_PATTERNS = /twitterbot|facebookexternalhit|linkedinbot|slackbot|discordbot|telegrambot|whatsapp|googlebot|bingbot|yandexbot|baiduspider|duckduckbot|applebot|pinterestbot|redditbot|embedly|outbrain|quora|ahrefsbot|semrushbot|rogerbot|imessagebot/i;

  const existingBefore = devServerConfig.onBeforeSetupMiddleware;
  devServerConfig.onBeforeSetupMiddleware = function (devServer) {
    if (existingBefore) existingBefore(devServer);

    devServer.app.use((req, res, next) => {
      const ua = req.headers['user-agent'] || '';
      if (!BOT_PATTERNS.test(ua)) return next();

      const reqPath = req.path;
      let ssrPath = null;

      const listingMatch = reqPath.match(/^\/honeypot\/listing\/(.+)/);
      if (listingMatch) ssrPath = `/api/ssr/listing/${listingMatch[1]}`;

      const recordMatch = reqPath.match(/^\/record\/(.+)/);
      if (recordMatch) ssrPath = `/api/ssr/record/${recordMatch[1]}`;

      const profileMatch = reqPath.match(/^\/profile\/(.+)/);
      if (profileMatch) ssrPath = `/api/ssr/profile/${profileMatch[1]}`;

      if (reqPath === '/honeypot') ssrPath = '/api/ssr/honeypot';
      if (reqPath === '/' || reqPath === '/hive') ssrPath = '/api/ssr';

      // /vinyl/{artist}/{album}/{variant} -> /api/vinyl/ssr/{artist}/{album}/{variant}
      const vinylMatch = reqPath.match(/^\/vinyl\/([^/]+)\/([^/]+)\/([^/]+)/);
      if (vinylMatch) ssrPath = `/api/vinyl/ssr/${vinylMatch[1]}/${vinylMatch[2]}/${vinylMatch[3]}`;

      if (ssrPath) {
        const http = require('http');
        http.get(`http://localhost:8001${ssrPath}`, (proxyRes) => {
          res.writeHead(proxyRes.statusCode, { ...proxyRes.headers, 'content-type': 'text/html; charset=utf-8' });
          proxyRes.pipe(res);
        }).on('error', () => next());
        return;
      }
      next();
    });
  };

  // Keep existing setupMiddlewares for health check
  if (config.enableHealthCheck && setupHealthEndpoints && healthPluginInstance) {
    const originalSetupMiddlewares = devServerConfig.setupMiddlewares;
    devServerConfig.setupMiddlewares = (middlewares, devServer) => {
      if (originalSetupMiddlewares) {
        middlewares = originalSetupMiddlewares(middlewares, devServer);
      }
      setupHealthEndpoints(devServer, healthPluginInstance);
      return middlewares;
    };
  }

  return devServerConfig;
};

// Visual edits disabled — replaces index.html with a shell that has no #root div
// if (isDevServer) { ... withVisualEdits ... }

module.exports = webpackConfig;
