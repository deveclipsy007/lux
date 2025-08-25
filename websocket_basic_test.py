"""
Basic WebSocket Connection Test
Tests the fundamental WebSocket functionality without importing complex modules
"""

import asyncio
import json
import websockets
from datetime import datetime
from typing import Optional
import time

class WebSocketBasicTester:
    def __init__(self, url: str = "ws://localhost:8000/ws"):
        self.url = url
        self.test_results = []
        
    async def test_connection_lifecycle(self):
        """Test basic connection and disconnection"""
        print("Testing WebSocket connection lifecycle...")
        
        try:
            start_time = time.time()
            
            # Test connection
            async with websockets.connect(self.url, ping_interval=20, ping_timeout=10) as websocket:
                connect_time = time.time() - start_time
                print(f"✅ Connection established in {connect_time:.3f}s")
                
                # Test sending a message
                test_message = {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"test": "connection_test"}
                }
                
                await websocket.send(json.dumps(test_message))
                print("✅ Message sent successfully")
                
                # Test receiving response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"✅ Response received: {response[:100]}...")
                except asyncio.TimeoutError:
                    print("⚠️  No response received within timeout")
                
            print("✅ Connection closed successfully")
            return True
            
        except ConnectionRefusedError:
            print("❌ Connection refused - WebSocket server may not be running")
            return False
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    async def test_multiple_connections(self, count: int = 5):
        """Test multiple concurrent connections"""
        print(f"🔄 Testing {count} concurrent connections...")
        
        async def create_connection(conn_id: int):
            try:
                async with websockets.connect(self.url) as websocket:
                    await websocket.send(json.dumps({
                        "type": "test",
                        "connection_id": conn_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                    return f"Connection {conn_id} successful"
            except Exception as e:
                return f"Connection {conn_id} failed: {e}"
        
        # Create multiple connections concurrently
        tasks = [create_connection(i) for i in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if "successful" in str(r))
        print(f"✅ {successful}/{count} connections successful")
        
        return successful == count
    
    async def test_message_latency(self, message_count: int = 10):
        """Test message sending latency"""
        print(f"🔄 Testing message latency with {message_count} messages...")
        
        try:
            async with websockets.connect(self.url) as websocket:
                latencies = []
                
                for i in range(message_count):
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
                        print(f"⚠️  Message {i} timed out")
                
                if latencies:
                    avg_latency = sum(latencies) / len(latencies)
                    min_latency = min(latencies)
                    max_latency = max(latencies)
                    
                    print(f"📊 Latency Stats:")
                    print(f"   Average: {avg_latency*1000:.2f}ms")
                    print(f"   Min: {min_latency*1000:.2f}ms")
                    print(f"   Max: {max_latency*1000:.2f}ms")
                    print(f"   Success rate: {len(latencies)}/{message_count}")
                    
                    return avg_latency < 0.1  # Less than 100ms average
                
        except Exception as e:
            print(f"❌ Latency test failed: {e}")
            return False
    
    async def test_reconnection(self):
        """Test reconnection capability"""
        print("🔄 Testing reconnection capability...")
        
        try:
            # First connection
            websocket1 = await websockets.connect(self.url)
            await websocket1.send(json.dumps({"type": "test", "phase": "first"}))
            print("✅ First connection established")
            
            # Close connection
            await websocket1.close()
            print("✅ First connection closed")
            
            # Wait a moment
            await asyncio.sleep(1)
            
            # Reconnect
            websocket2 = await websockets.connect(self.url)
            await websocket2.send(json.dumps({"type": "test", "phase": "reconnect"}))
            print("✅ Reconnection successful")
            
            await websocket2.close()
            return True
            
        except Exception as e:
            print(f"❌ Reconnection test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all WebSocket tests"""
        print("=" * 60)
        print("🚀 Starting WebSocket Basic Tests")
        print("=" * 60)
        
        tests = [
            ("Connection Lifecycle", self.test_connection_lifecycle()),
            ("Multiple Connections", self.test_multiple_connections(3)),
            ("Message Latency", self.test_message_latency(5)),
            ("Reconnection", self.test_reconnection())
        ]
        
        results = {}
        
        for test_name, test_coro in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                result = await test_coro
                results[test_name] = result
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   Result: {status}")
            except Exception as e:
                results[test_name] = False
                print(f"   Result: ❌ ERROR - {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:25} {status}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! WebSocket implementation is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the WebSocket server status and configuration.")
        
        return results

async def main():
    """Main test function"""
    # Check if server is running on different ports
    ports = [8000, 3000, 8080]
    
    for port in ports:
        url = f"ws://localhost:{port}/ws"
        print(f"\n🔍 Checking WebSocket server on port {port}...")
        
        try:
            async with websockets.connect(url, ping_timeout=5) as ws:
                print(f"✅ Found WebSocket server on port {port}")
                tester = WebSocketBasicTester(url)
                await tester.run_all_tests()
                break
        except Exception as e:
            print(f"❌ No server on port {port}: {e}")
    else:
        print("\n⚠️  No WebSocket server found on common ports.")
        print("   Please ensure the WebSocket server is running.")
        print("   Common commands:")
        print("   - python backend/main.py")
        print("   - uvicorn backend.main:app --reload")

if __name__ == "__main__":
    asyncio.run(main())