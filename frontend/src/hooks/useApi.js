import { useState, useCallback } from 'react';
import axios from 'axios';

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const baseURL = process.env.REACT_APP_BACKEND_URL || '/api';
  const axiosInstance = axios.create({ baseURL });

  const request = useCallback(async (config) => {
    try {
      setLoading(true);
      setError(null);
      const response = await axiosInstance(config);
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || '请求失败';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [axiosInstance]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    loading,
    error,
    request,
    clearError
  };
};