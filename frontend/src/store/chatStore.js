import { create } from 'zustand';
import client from '../api/client';

const useChatStore = create((set, get) => ({
    sessions: [],
    currentSession: null,
    isLoading: false,
    error: null,

    fetchSessions: async () => {
        set({ isLoading: true });
        try {
            const response = await client.get('/sessions');
            set({ sessions: response.data, isLoading: false });
        } catch (error) {
            set({ error: error.response?.data?.detail || 'Failed to fetch sessions', isLoading: false });
        }
    },

    createSession: async (title) => {
        set({ isLoading: true });
        try {
            const response = await client.post('/sessions', { title });
            set((state) => ({
                sessions: [...state.sessions, response.data],
                currentSession: response.data,
                isLoading: false,
            }));
            return response.data;
        } catch (error) {
            set({ error: error.response?.data?.detail || 'Failed to create session', isLoading: false });
            return null;
        }
    },

    fetchSessionMessages: async (sessionId) => {
        set({ isLoading: true });
        try {
            const response = await client.get(`/sessions/${sessionId}`);
            set((state) => ({
                currentSession: response.data,
                sessions: state.sessions.map(s =>
                    s.id === sessionId ? response.data : s
                ),
                isLoading: false
            }));
        } catch (error) {
            set({
                error: error.response?.data?.detail || 'Failed to fetch session messages',
                isLoading: false
            });
        }
    },

    setCurrentSession: (session) => {
        const { fetchSessionMessages } = get();
        set({ currentSession: session });
        fetchSessionMessages(session.id);  // Fetch messages when setting current session
    },

    sendMessage: async (message, sessionId) => {
        try {
            const chatResponse = await client.post('/chat', {
                query: message,
                session_id: sessionId,
            });

            set((state) => {
                const updatedSession = {
                    ...state.currentSession,
                    messages: [
                        ...(state.currentSession?.messages || []),
                        { sender: 'user', content: message },
                        { sender: 'assistant', content: chatResponse.data.message },
                    ],
                };
                return {
                    currentSession: updatedSession,
                    sessions: state.sessions.map((s) =>
                        s.id === sessionId ? updatedSession : s
                    ),
                };
            });

            return chatResponse.data;
        } catch (error) {
            set({ error: error.response?.data?.detail || 'Failed to send message' });
            return null;
        }
    },

    deleteSession: async (sessionId) => {
        try {
            await client.delete(`/chat/${sessionId}`);
            set((state) => ({
                sessions: state.sessions.filter((s) => s.id !== sessionId),
                currentSession: state.currentSession?.id === sessionId ? null : state.currentSession,
            }));
            return true;
        } catch (error) {
            set({ error: error.response?.data?.detail || 'Failed to delete session' });
            return false;
        }
    },

    renameSession: async (sessionId, newTitle) => {
        try {
            const response = await client.put(`/chat/${sessionId}/rename`, { new_title: newTitle });
            if (response.ok) {
                set((state) => ({
                    sessions: state.sessions.map((session) =>
                        session.id === sessionId ? { ...session, title: newTitle } : session
                    ),
                    currentSession:
                        state.currentSession?.id === sessionId
                            ? { ...state.currentSession, title: newTitle }
                            : state.currentSession,
                }));
                return true;
            } else {
                throw new Error('Failed to rename chat session');
            }
        } catch (error) {
            console.error('Error renaming chat session:', error);
            return false;
        }
    },
}));

export default useChatStore; 