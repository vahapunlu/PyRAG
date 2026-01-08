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
    const response = await api.post('/query', {
      question: query,
      return_sources: true
    });
    return response.data;
  } catch (error) {
    console.error('Search error:', error);
    throw error;
  }
};

export const getHealth = async () => {
    try {
        const response = await api.get('/health');
        return response.data;
    } catch (error) {
        return { status: 'offline' };
    }
}

export default api;
