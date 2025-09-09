const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_CONFIG = {
  MEETINGS_BASE: `${API_BASE_URL}/api/meetings`,
  CONNECTION_DETAILS: `${API_BASE_URL}/connection-details`,
};