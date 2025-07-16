import { create } from 'zustand';
import client from '../api/client';

const useDocumentStore = create((set) => ({
    documents: [],
    isLoading: false,
    error: null,

    fetchDocuments: async (status, page = 1, pageSize = 10) => {
        set({ isLoading: true });
        try {
            const response = await client.get('/document', {
                params: { status, page, page_size: pageSize },
            });
            set({ documents: response.data, isLoading: false });
        } catch (error) {
            set({ error: error.response?.data?.detail || 'Failed to fetch documents', isLoading: false });
        }
    },

    uploadDocuments: async (files) => {
        set({ isLoading: true });
        try {
            const formData = new FormData();
            files.forEach((file) => formData.append('files', file));

            const response = await client.post('/document/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            set((state) => ({
                documents: [...state.documents, ...response.data.documents],
                isLoading: false,
            }));
            return response.data;
        } catch (error) {
            set({ error: error.response?.data?.detail || 'Failed to upload documents', isLoading: false });
            return null;
        }
    },

    indexDocument: async (docId, forceReindex = false) => {
        try {
            const response = await client.post(`/document/${docId}/index`, {
                force_reindex: forceReindex,
            });
            set((state) => ({
                documents: state.documents.map((doc) =>
                    doc.id === docId ? { ...doc, status: 'indexed' } : doc
                ),
            }));
            return response.data;
        } catch (error) {
            set({ error: error.response?.data?.detail || 'Failed to index document' });
            return null;
        }
    },

    getDocument: async (docId) => {
        try {
            const response = await client.get(`/document/${docId}`);
            return response.data;
        } catch (error) {
            set({ error: error.response?.data?.detail || 'Failed to get document' });
            return null;
        }
    },
}));

export default useDocumentStore; 