import { api } from '../../services/api.js';

export const authService = {
  login(email, password) {
    return api.login(email, password);
  },

  getCurrentUser() {
    return api.getCurrentUser();
  },

  logout() {
    return api.logout();
  },
};
