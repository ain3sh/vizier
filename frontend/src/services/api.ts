import axios, { AxiosRequestConfig } from 'axios';

// API base URL - configure based on your environment
const API_BASE_URL = 'http://localhost:8000';

// Source interface
export interface Source {
  id: string;
  title: string;
  url: string;
  date?: string;
  author?: string;
  snippet?: string;
  root?: string;
}

// Source review interface
export interface SourceReview {
  included: string[];
  excluded: string[];
  reranked_urls: string[];
}

// Utility for handling authentication
const getAuthHeader = (): AxiosRequestConfig => {
  const token = localStorage.getItem('jwt');
  return {
    headers: {
      Authorization: `Bearer ${token}`
    }
  };
};

// Query API methods
const queryAPI = {
  // Create a new query
  createQuery: async (initialQuery: string): Promise<string> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/queries`,
        { query: initialQuery },
        getAuthHeader()
      );
      return response.data.query_id;
    } catch (error) {
      console.error('Error creating query:', error);
      throw error;
    }
  },

  // Refine a query with initial text
  refineQuery: async (queryId: string, queryText: string): Promise<any> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/queries/${queryId}/refine`,
        { query: queryText },
        getAuthHeader()
      );
      return response.data;
    } catch (error) {
      console.error('Error refining query:', error);
      throw error;
    }
  },

  // Get sources for a query
  getSources: async (queryId: string): Promise<Source[]> => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/queries/${queryId}/sources`,
        getAuthHeader()
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching sources:', error);
      throw error;
    }
  },

  // Submit source review
  submitSourceReview: async (queryId: string, review: SourceReview): Promise<any> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/queries/${queryId}/sources/review`,
        review,
        getAuthHeader()
      );
      return response.data;
    } catch (error) {
      console.error('Error submitting source review:', error);
      throw error;
    }
  },

  // Create SSE connection for query progress
  createEventSource: (queryId: string): EventSource => {
    return new EventSource(`${API_BASE_URL}/queries/stream/${queryId}`);
  }
};

// Draft API methods
const draftAPI = {
  // Generate a draft
  generateDraft: async (queryId: string): Promise<any> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/drafts/generate`,
        { query_id: queryId },
        getAuthHeader()
      );
      return response.data;
    } catch (error) {
      console.error('Error generating draft:', error);
      throw error;
    }
  },

  // Get draft content
  getDraft: async (draftId: string): Promise<any> => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/drafts/${draftId}`,
        getAuthHeader()
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching draft:', error);
      throw error;
    }
  },

  // Accept draft
  acceptDraft: async (draftId: string): Promise<any> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/drafts/${draftId}/accept`,
        {},
        getAuthHeader()
      );
      return response.data;
    } catch (error) {
      console.error('Error accepting draft:', error);
      throw error;
    }
  },

  // Reject draft
  rejectDraft: async (draftId: string, feedback: string): Promise<any> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/drafts/${draftId}/reject`,
        { feedback },
        getAuthHeader()
      );
      return response.data;
    } catch (error) {
      console.error('Error rejecting draft:', error);
      throw error;
    }
  },

  // Create SSE connection for draft generation
  createEventSource: (draftId: string): EventSource => {
    return new EventSource(`${API_BASE_URL}/drafts/stream/${draftId}`);
  }
};

export { queryAPI, draftAPI };
export default queryAPI;