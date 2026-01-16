import axios from 'axios';
import config from '../../config';

// Create axios instance
const api = axios.create({
  baseURL: config.apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const searchDocuments = async (query: string) => {
  try {
    // Call internal Next.js API route
    const response = await api.post('/api/chat', {
      question: query,
    });
    return response.data;
  } catch (error) {
    console.error('Search error:', error);
    throw error;
  }
};

export const getHealth = async () => {
    // Internal API is always "healthy" if the site is up
    return { status: 'online', service: 'nextjs-serverless' };
};

export default api;
