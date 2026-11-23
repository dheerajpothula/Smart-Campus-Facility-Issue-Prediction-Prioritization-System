import { api } from './apiClient';
import type { TaxonomyHierarchyResponse } from '../types';

let cachedTaxonomy: TaxonomyHierarchyResponse | null = null;

export const taxonomyService = {
  getHierarchy: async (): Promise<TaxonomyHierarchyResponse> => {
    if (cachedTaxonomy) {
      return cachedTaxonomy;
    }
    const data = await api.get<TaxonomyHierarchyResponse>('/api/taxonomy/hierarchy');
    cachedTaxonomy = data;
    return data;
  },

  clearCache: () => {
    cachedTaxonomy = null;
  },
};
