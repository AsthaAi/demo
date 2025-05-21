import React, { useState } from 'react';

interface AgentTestProps {
  onResult: (result: any) => void;
}

const AgentTest: React.FC<AgentTestProps> = ({ onResult }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const testAgent = async (agentType: 'fake' | 'market') => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/test-${agentType}-agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'payment_processing',
          data: {}
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.success) {
        onResult(data.result);
      } else {
        setError(data.error || 'Failed to test agent');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error testing agent:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Agent Communication Test</h2>
      <div className="space-y-4">
        <button
          onClick={() => testAgent('fake')}
          disabled={loading}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-blue-300"
        >
          {loading ? 'Testing...' : 'Test Fake Agent'}
        </button>
        <button
          onClick={() => testAgent('market')}
          disabled={loading}
          className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-green-300"
        >
          {loading ? 'Testing...' : 'Test Market Agent'}
        </button>
        {error && (
          <div className="p-3 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentTest; 