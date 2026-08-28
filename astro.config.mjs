import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import tailwind from '@astrojs/tailwind';

// https://astro.build/config
export default defineConfig({
  // Static site — output is plain HTML/CSS/JS files
  output: 'static',
  // Deploy to Cloudflare Pages
  adapter: undefined,
  // Svelte components
  integrations: [
    svelte(),
    tailwind({ applyBaseStyles: false }),
  ],
  // Build into ./dist
  build: {
    assets: 'assets',
  },
  vite: {
    build: {
      // Smaller chunks for Cloudflare CDN
      chunkSizeWarningLimit: 1000,
    },
  },
});
