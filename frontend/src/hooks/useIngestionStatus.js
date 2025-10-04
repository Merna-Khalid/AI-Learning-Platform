import { useEffect, useRef, useState } from 'react';
import api from '../api/api';

const useIngestionStatus = (materialId) => {
  const [status, setStatus] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(Date.now());
  const ws = useRef(null);
  const pollInterval = useRef(null);
  const reconnectTimeout = useRef(null);

  const fetchStatus = async () => {
    try {
      const response = await api.get(`/courses/materials/${materialId}/status`);
      if (response.data) {
        setStatus(response.data);
        setLastUpdate(Date.now());
        
        // If status is completed or failed, we can stop polling
        if (response.data.status === 'completed' || response.data.status === 'failed') {
          stopPolling();
        }
      }
    } catch (error) {
      console.error('Error fetching material status:', error);
      // If we can't reach the status endpoint, create a fallback status
      setStatus({
        material_id: materialId,
        status: "processing",
        progress: 50,
        message: "Processing file... (fallback status)"
      });
    }
  };

  const startPolling = () => {
    if (pollInterval.current) clearInterval(pollInterval.current);
    
    // Fetch immediately
    fetchStatus();
    
    // Then poll every 3 seconds
    pollInterval.current = setInterval(fetchStatus, 3000);
  };

  const stopPolling = () => {
    if (pollInterval.current) {
      clearInterval(pollInterval.current);
      pollInterval.current = null;
    }
  };

  const connectWebSocket = () => {
    if (!materialId) return;

    const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const wsUrl = backendUrl.replace('http', 'ws') + `/ws/ingestion/${materialId}`;
    
    console.log('Attempting WebSocket connection:', wsUrl);
    
    try {
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        setIsConnected(true);
        stopPolling(); // Stop polling if WebSocket connects
        console.log('✅ WebSocket connected for material:', materialId);
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket status update:', data);
          setStatus(data);
          setLastUpdate(Date.now());
          
          // If we get a final status, we can close the connection after a bit
          if (data.status === 'completed' || data.status === 'failed') {
            setTimeout(() => {
              if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                ws.current.close();
              }
            }, 5000); // Close 5 seconds after final status
          }
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      };

      ws.current.onclose = (event) => {
        setIsConnected(false);
        console.log('WebSocket disconnected:', {
          materialId,
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
        
        // Only start polling if the closure wasn't clean (unexpected disconnect)
        if (!event.wasClean) {
          console.log('🔄 Starting polling fallback due to unclean disconnect');
          startPolling();
        }
        
        // Attempt reconnect after delay if not a final status
        if (status?.status !== 'completed' && status?.status !== 'failed') {
          reconnectTimeout.current = setTimeout(() => {
            console.log('🔄 Attempting WebSocket reconnection...');
            connectWebSocket();
          }, 3000);
        }
      };

      ws.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setIsConnected(false);
        console.log('🔄 Starting polling fallback due to WebSocket error');
        startPolling();
      };

    } catch (error) {
      console.error('❌ WebSocket creation failed:', error);
      console.log('🔄 Using polling as primary method');
      startPolling();
    }
  };

  useEffect(() => {
    if (!materialId) return;

    console.log('Setting up status tracking for material:', materialId);
    connectWebSocket();

    return () => {
      console.log('Cleaning up status tracking for material:', materialId);
      
      // Clean up WebSocket
      if (ws.current) {
        ws.current.close(1000, 'Component unmounted');
        ws.current = null;
      }
      
      // Clean up polling
      stopPolling();
      
      // Clean up reconnect timeout
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
        reconnectTimeout.current = null;
      }
      
      setIsConnected(false);
    };
  }, [materialId]);

  // Fallback: if we haven't received updates in a while, show a warning
  const isStale = Date.now() - lastUpdate > 10000; // 10 seconds without updates

  return { 
    status, 
    isConnected,
    isStale,
    lastUpdate: new Date(lastUpdate).toLocaleTimeString()
  };
};

export default useIngestionStatus;