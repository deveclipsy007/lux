"""
Simple WebSocket Connection Test
Tests basic WebSocket functionality
"""

import asyncio
import json
import websockets
from datetime import datetime
import time

class WebSocketTester:
    def __init__(self, url: str = "ws://localhost:8000/ws"):
        self.url = url
        
    async def test_connection(self):
        """Test basic connection"""
        print("Testing WebSocket connection...")
        
        try:
            start_time = time.time()
            
            async with websockets.connect(self.url, ping_interval=20, ping_timeout=10) as websocket:
                connect_time = time.time() - start_time
                print(f"Connection established in {connect_time:.3f}s")
                
                test_message = {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"test": "connection_test"}
                }
                
                await websocket.send(json.dumps(test_message))
                print("Message sent successfully")
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"Response received: {response[:100]}...")
                except asyncio.TimeoutError:
                    print("No response received within timeout")
                
            print("Connection closed successfully")
            return True
            
        except ConnectionRefusedError:
            print("Connection refused - WebSocket server may not be running")
            return False
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    async def test_latency(self, count: int = 5):
        """Test message latency"""
        print(f"Testing message latency with {count} messages...")
        
        try:
            async with websockets.connect(self.url) as websocket:
                latencies = []
                
                for i in range(count):
                    start_time = time.time()
                    
                    message = {
                        "type": "latency_test",
                        "message_id": i,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send(json.dumps(message))
                    
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        latency = time.time() - start_time
                        latencies.append(latency)
                    except asyncio.TimeoutError:
                        print(f"Message {i} timed out")
                
                if latencies:
                    avg_latency = sum(latencies) / len(latencies)
                    print(f"Average latency: {avg_latency*1000:.2f}ms")
                    print(f"Success rate: {len(latencies)}/{count}")
                    return avg_latency < 0.1
                
        except Exception as e:
            print(f"Latency test failed: {e}")
            return False
    
    async def run_tests(self):
        """Run all tests"""
        print("=" * 50)
        print("WebSocket Tests")
        print("=" * 50)
        
        connection_result = await self.test_connection()
        print(f"Connection test: {'PASS' if connection_result else 'FAIL'}")
        
        if connection_result:
            latency_result = await self.test_latency()
            print(f"Latency test: {'PASS' if latency_result else 'FAIL'}")
        else:
            latency_result = False
            print("Latency test: SKIP (no connection)")
        
        print("\n" + "=" * 50)
        print("Summary:")
        print(f"Connection: {'OK' if connection_result else 'FAIL'}")
        print(f"Latency: {'OK' if latency_result else 'FAIL'}")
        
        return connection_result and latency_result

async def main():
    """Check for WebSocket server and run tests"""
    ports = [8000, 3000, 8080]
    
    for port in ports:
        url = f"ws://localhost:{port}/ws"
        print(f"\nChecking WebSocket server on port {port}...")
        
        try:
            async with websockets.connect(url, ping_timeout=3) as ws:
                print(f"Found WebSocket server on port {port}")
                tester = WebSocketTester(url)
                result = await tester.run_tests()
                break
        except Exception as e:
            print(f"No server on port {port}")
    else:
        print("\nNo WebSocket server found on common ports.")
        print("Server may not be running. Try:")
        print("  python backend/main.py")
        print("  uvicorn backend.main:app --reload")

if __name__ == "__main__":
    asyncio.run(main())