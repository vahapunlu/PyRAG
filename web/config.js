
const config = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || '', // Empty means same origin (internal API)
  defaultLanguage: 'en',
  theme: {
    primary: '#0ea5e9', // Sky 500
    secondary: '#64748b', // Slate 500
    background: '#0f172a', // Slate 900
  }
};

export default config;
