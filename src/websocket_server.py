"""
Green-Code FX WebSocket Server
Handles real-time preview streaming and live updates
"""

import json
import time
import asyncio
import threading
import base64
from typing import Dict, Set, Optional, Any
from datetime import datetime
from pathlib import Path

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = None

try:
    from .config import config
    from .video_generator import VideoGenerator
    import structlog
except ImportError:
    from config import config
    from video_generator import VideoGenerator
    import structlog

logger = structlog.get_logger()


class WebSocketManager:
    """Manages WebSocket connections and real-time streaming."""
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self.connections: Set[WebSocketServerProtocol] = set()
        self.preview_sessions: Dict[str, Dict[str, Any]] = {}
        self.server = None
        self.running = False
        self.video_generator = VideoGenerator()
        
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("WebSockets not available - install websockets package for real-time features")
    
    async def start_server(self, host: str = "localhost", port: int = 8083):
        """Start the WebSocket server."""
        if not WEBSOCKETS_AVAILABLE:
            logger.error("Cannot start WebSocket server - websockets package not installed")
            return False
        
        try:
            self.server = await websockets.serve(
                self.handle_connection,
                host,
                port,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            self.running = True
            logger.info("WebSocket server started", host=host, port=port)
            return True
            
        except Exception as e:
            logger.error("Failed to start WebSocket server", error=str(e))
            return False
    
    async def stop_server(self):
        """Stop the WebSocket server."""
        if self.server:
            self.running = False
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")
    
    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection."""
        self.connections.add(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}_{int(time.time())}"
        
        logger.info("WebSocket client connected", client_id=client_id, path=path)
        
        try:
            # Send welcome message
            await self.send_message(websocket, {
                "type": "connection",
                "status": "connected",
                "client_id": client_id,
                "server_time": datetime.now().isoformat()
            })
            
            # Handle incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, client_id, data)
                except json.JSONDecodeError:
                    await self.send_error(websocket, "Invalid JSON message")
                except Exception as e:
                    logger.error("Error handling WebSocket message", client_id=client_id, error=str(e))
                    await self.send_error(websocket, f"Message handling error: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket client disconnected", client_id=client_id)
        except Exception as e:
            logger.error("WebSocket connection error", client_id=client_id, error=str(e))
        finally:
            self.connections.discard(websocket)
            # Clean up any preview sessions for this client
            sessions_to_remove = [sid for sid, session in self.preview_sessions.items() 
                                if session.get("client_id") == client_id]
            for session_id in sessions_to_remove:
                del self.preview_sessions[session_id]
    
    async def handle_message(self, websocket: WebSocketServerProtocol, client_id: str, data: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        message_type = data.get("type")
        
        if message_type == "start_preview":
            await self.handle_start_preview(websocket, client_id, data)
        elif message_type == "stop_preview":
            await self.handle_stop_preview(websocket, client_id, data)
        elif message_type == "update_preview_settings":
            await self.handle_update_preview_settings(websocket, client_id, data)
        elif message_type == "ping":
            await self.send_message(websocket, {"type": "pong", "timestamp": time.time()})
        else:
            await self.send_error(websocket, f"Unknown message type: {message_type}")
    
    async def handle_start_preview(self, websocket: WebSocketServerProtocol, client_id: str, data: Dict[str, Any]):
        """Start a real-time preview session."""
        try:
            session_id = data.get("session_id", f"preview_{client_id}_{int(time.time())}")
            parameters = data.get("parameters", {})
            
            # Validate parameters
            if not parameters:
                await self.send_error(websocket, "Preview parameters are required")
                return
            
            # Create preview session
            self.preview_sessions[session_id] = {
                "client_id": client_id,
                "websocket": websocket,
                "parameters": parameters,
                "active": True,
                "created_at": time.time(),
                "frame_count": 0
            }
            
            # Start preview generation in background
            asyncio.create_task(self.generate_preview_stream(session_id))
            
            await self.send_message(websocket, {
                "type": "preview_started",
                "session_id": session_id,
                "status": "active"
            })
            
            logger.info("Preview session started", session_id=session_id, client_id=client_id)
            
        except Exception as e:
            logger.error("Failed to start preview", client_id=client_id, error=str(e))
            await self.send_error(websocket, f"Failed to start preview: {str(e)}")
    
    async def handle_stop_preview(self, websocket: WebSocketServerProtocol, client_id: str, data: Dict[str, Any]):
        """Stop a preview session."""
        session_id = data.get("session_id")
        
        if session_id in self.preview_sessions:
            self.preview_sessions[session_id]["active"] = False
            del self.preview_sessions[session_id]
            
            await self.send_message(websocket, {
                "type": "preview_stopped",
                "session_id": session_id
            })
            
            logger.info("Preview session stopped", session_id=session_id, client_id=client_id)
        else:
            await self.send_error(websocket, f"Preview session not found: {session_id}")
    
    async def handle_update_preview_settings(self, websocket: WebSocketServerProtocol, client_id: str, data: Dict[str, Any]):
        """Update preview settings in real-time."""
        session_id = data.get("session_id")
        new_parameters = data.get("parameters", {})
        
        if session_id in self.preview_sessions:
            session = self.preview_sessions[session_id]
            session["parameters"].update(new_parameters)
            
            await self.send_message(websocket, {
                "type": "preview_settings_updated",
                "session_id": session_id,
                "parameters": session["parameters"]
            })
            
            logger.info("Preview settings updated", session_id=session_id, client_id=client_id)
        else:
            await self.send_error(websocket, f"Preview session not found: {session_id}")
    
    async def generate_preview_stream(self, session_id: str):
        """Generate and stream preview frames."""
        try:
            session = self.preview_sessions.get(session_id)
            if not session:
                return
            
            websocket = session["websocket"]
            parameters = session["parameters"]
            
            # Generate preview frames (simplified for demo)
            frame_interval = 1.0 / 30  # 30 FPS
            
            while session.get("active", False) and session_id in self.preview_sessions:
                try:
                    # Generate a preview frame (this would be actual frame generation)
                    frame_data = await self.generate_preview_frame(parameters, session["frame_count"])
                    
                    if frame_data:
                        await self.send_message(websocket, {
                            "type": "preview_frame",
                            "session_id": session_id,
                            "frame_number": session["frame_count"],
                            "frame_data": frame_data,
                            "timestamp": time.time()
                        })
                        
                        session["frame_count"] += 1
                    
                    await asyncio.sleep(frame_interval)
                    
                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error("Error generating preview frame", session_id=session_id, error=str(e))
                    break
            
        except Exception as e:
            logger.error("Preview stream generation failed", session_id=session_id, error=str(e))
        finally:
            # Clean up session
            if session_id in self.preview_sessions:
                del self.preview_sessions[session_id]
    
    async def generate_preview_frame(self, parameters: Dict[str, Any], frame_number: int) -> Optional[str]:
        """Generate a single preview frame."""
        try:
            # This is a simplified preview generation
            # In a real implementation, this would generate actual video frames
            
            # For now, return a placeholder base64 image
            # This would be replaced with actual frame generation logic
            placeholder_data = f"Preview frame {frame_number} with settings: {json.dumps(parameters, indent=2)}"
            
            # Convert to base64 (in real implementation, this would be an actual image)
            frame_base64 = base64.b64encode(placeholder_data.encode()).decode()
            
            return frame_base64
            
        except Exception as e:
            logger.error("Failed to generate preview frame", frame_number=frame_number, error=str(e))
            return None
    
    async def send_message(self, websocket: WebSocketServerProtocol, message: Dict[str, Any]):
        """Send a message to a WebSocket client."""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error("Failed to send WebSocket message", error=str(e))
    
    async def send_error(self, websocket: WebSocketServerProtocol, error_message: str):
        """Send an error message to a WebSocket client."""
        await self.send_message(websocket, {
            "type": "error",
            "message": error_message,
            "timestamp": time.time()
        })
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        if not self.connections:
            return
        
        disconnected = set()
        for websocket in self.connections:
            try:
                await self.send_message(websocket, message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)
            except Exception as e:
                logger.error("Failed to broadcast message", error=str(e))
                disconnected.add(websocket)
        
        # Remove disconnected clients
        self.connections -= disconnected
    
    def get_status(self) -> Dict[str, Any]:
        """Get WebSocket server status."""
        return {
            "running": self.running,
            "connected_clients": len(self.connections),
            "active_preview_sessions": len(self.preview_sessions),
            "websockets_available": WEBSOCKETS_AVAILABLE
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


def start_websocket_server_thread(host: str = "localhost", port: int = 8083):
    """Start WebSocket server in a separate thread."""
    if not WEBSOCKETS_AVAILABLE:
        logger.warning("WebSocket server not started - websockets package not available")
        return False
    
    def run_server():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(websocket_manager.start_server(host, port))
        loop.run_forever()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    logger.info("WebSocket server thread started", host=host, port=port)
    return True
