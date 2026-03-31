import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const uploadFile = async (file, sessionId) => {
  const formData = new FormData();
  formData.append('file', file);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const chat = async (question, sessionId, history = []) => {
  const response = await api.post('/chat', {
    question,
    session_id: sessionId,
    history,
  });
  return response.data;
};

// For streaming SSE response
export const streamChat = async (question, sessionId, history = [], onChunk, onError, onDone) => {
  try {
    const response = await fetch(`${API_BASE_URL}/stream-chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        session_id: sessionId,
        history,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Server is not available. Please try again.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let done = false;

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        const chunkStr = decoder.decode(value, { stream: true });
        // The SSE chunk returns "data: {token}\n\n"
        const lines = chunkStr.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6);
            if (dataStr === '[DONE]') {
              onDone();
              return;
            } else if (dataStr.startsWith('[ERROR]')) {
              throw new Error(dataStr.substring(8));
            } else {
              onChunk(dataStr);
            }
          }
        }
      }
    }
    onDone();
  } catch (error) {
    onError(error.message || 'Server error occurred.');
  }
};
