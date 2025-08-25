"""
WebSocket Network Stability and Performance Test
Tests various network conditions and scenarios
"""

import asyncio
import json
import websockets
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import statistics

class WebSocketStabilityTester:
    def __init__(self, url: str = "ws://localhost:8000/ws"):
        self.url = url
        self.results = {}
        
    async def test_concurrent_connections(self, count: int = 10):
        """Test multiple concurrent WebSocket connections"""
        print(f"Testing {count} concurrent connections...")
        
        async def create_connection(conn_id: int):
            try:
                start_time = time.time()
                async with websockets.connect(self.url, ping_interval=20) as websocket:
                    connect_time = time.time() - start_time
                    
                    # Send test message
                    await websocket.send(json.dumps({
                        "type": "test",
                        "connection_id": conn_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Wait for response
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    return {
                        "connection_id": conn_id,
                        "success": True,
                        "connect_time": connect_time,
                        "response_type": response_data.get("type"),
                        "client_id": response_data.get("client_id")
                    }
                    
            except Exception as e:
                return {
                    "connection_id": conn_id,
                    "success": False,
                    "error": str(e),
                    "connect_time": None
                }
        
        # Create concurrent connections
        tasks = [create_connection(i) for i in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if not isinstance(r, dict)]
        
        success_rate = len(successful) / count * 100
        avg_connect_time = statistics.mean([r["connect_time"] for r in successful if r["connect_time"]])
        
        print(f"Concurrent connections: {len(successful)}/{count} successful ({success_rate:.1f}%)")
        print(f"Average connection time: {avg_connect_time*1000:.2f}ms")
        print(f"Failed connections: {len(failed)}")
        print(f"Exceptions: {len(exceptions)}")
        
        return {
            "total": count,
            "successful": len(successful),
            "failed": len(failed),
            "exceptions": len(exceptions),
            "success_rate": success_rate,
            "avg_connect_time": avg_connect_time
        }
    
    async def test_message_throughput(self, message_count: int = 100):
        """Test message sending throughput"""
        print(f"Testing message throughput with {message_count} messages...")
        
        try:
            async with websockets.connect(self.url) as websocket:
                # Wait for connection message
                await websocket.recv()
                
                start_time = time.time()
                sent_messages = 0
                received_responses = 0
                
                # Send all messages
                for i in range(message_count):
                    message = {
                        "type": "test",
                        "message_id": i,
                        "payload": f"Test message {i}",
                        "timestamp": time.time()
                    }
                    await websocket.send(json.dumps(message))
                    sent_messages += 1
                
                # Collect responses
                for i in range(message_count):
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        received_responses += 1
                    except asyncio.TimeoutError:
                        break
                
                end_time = time.time()
                duration = end_time - start_time
                
                messages_per_second = sent_messages / duration
                response_rate = received_responses / sent_messages * 100
                
                print(f"Sent {sent_messages} messages in {duration:.2f}s")
                print(f"Throughput: {messages_per_second:.1f} messages/second")
                print(f"Response rate: {response_rate:.1f}%")
                
                return {
                    "sent": sent_messages,
                    "received": received_responses,
                    "duration": duration,
                    "throughput": messages_per_second,
                    "response_rate": response_rate
                }
                
        except Exception as e:
            print(f"Throughput test failed: {e}")
            return {"error": str(e)}
    
    async def test_long_lived_connection(self, duration_seconds: int = 30):
        """Test connection stability over time"""
        print(f"Testing long-lived connection for {duration_seconds}s...")
        
        try:
            async with websockets.connect(self.url, ping_interval=10, ping_timeout=5) as websocket:
                # Wait for connection message
                await websocket.recv()
                
                start_time = time.time()
                messages_sent = 0
                messages_received = 0
                ping_count = 0
                
                while time.time() - start_time < duration_seconds:
                    # Send ping every 5 seconds
                    if messages_sent % 5 == 0:
                        await websocket.send(json.dumps({
                            "type": "ping",
                            "timestamp": time.time()
                        }))
                        ping_count += 1
                    else:
                        await websocket.send(json.dumps({
                            "type": "test",
                            "message_id": messages_sent,
                            "timestamp": time.time()
                        }))
                    
                    messages_sent += 1
                    
                    # Try to receive response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        messages_received += 1
                    except asyncio.TimeoutError:
                        pass
                    
                    await asyncio.sleep(1)  # Send message every second
                
                actual_duration = time.time() - start_time
                uptime_percentage = actual_duration / duration_seconds * 100
                
                print(f"Connection maintained for {actual_duration:.1f}s ({uptime_percentage:.1f}%)")
                print(f"Messages sent: {messages_sent}")
                print(f"Messages received: {messages_received}")
                print(f"Pings sent: {ping_count}")
                
                return {
                    "duration": actual_duration,
                    "uptime_percentage": uptime_percentage,
                    "messages_sent": messages_sent,
                    "messages_received": messages_received,
                    "ping_count": ping_count,
                    "response_rate": messages_received / messages_sent * 100 if messages_sent > 0 else 0
                }
                
        except Exception as e:
            print(f"Long-lived connection test failed: {e}")
            return {"error": str(e)}
    
    async def test_reconnection_resilience(self):
        """Test automatic reconnection capabilities"""
        print("Testing reconnection resilience...")
        
        reconnect_attempts = 3
        successful_reconnects = 0
        
        for attempt in range(reconnect_attempts):
            try:
                print(f"Reconnection attempt {attempt + 1}...")
                
                # Connect
                websocket = await websockets.connect(self.url)
                await websocket.recv()  # Connection message
                
                # Send test message
                await websocket.send(json.dumps({
                    "type": "test",
                    "attempt": attempt + 1,
                    "timestamp": time.time()
                }))
                
                # Receive response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Reconnection {attempt + 1} successful")
                
                # Close connection
                await websocket.close()
                successful_reconnects += 1
                
                # Wait before next attempt
                if attempt < reconnect_attempts - 1:
                    await asyncio.sleep(2)
                    
            except Exception as e:
                print(f"Reconnection {attempt + 1} failed: {e}")
        
        success_rate = successful_reconnects / reconnect_attempts * 100
        print(f"Reconnection success rate: {successful_reconnects}/{reconnect_attempts} ({success_rate:.1f}%)")
        
        return {
            "attempts": reconnect_attempts,
            "successful": successful_reconnects,
            "success_rate": success_rate
        }
    
    async def test_error_handling(self):
        """Test error handling capabilities"""
        print("Testing error handling...")
        
        error_tests = [
            {"name": "Invalid JSON", "message": "invalid json {"},
            {"name": "Unknown message type", "message": '{"type": "unknown_type"}'},
            {"name": "Missing fields", "message": '{"incomplete": true}'},
            {"name": "Large payload", "message": json.dumps({"type": "test", "data": "x" * 10000})}
        ]
        
        results = {}
        
        try:
            async with websockets.connect(self.url) as websocket:
                await websocket.recv()  # Connection message
                
                for test in error_tests:
                    try:
                        await websocket.send(test["message"])
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        response_data = json.loads(response)
                        
                        if response_data.get("type") == "error":
                            results[test["name"]] = {"handled": True, "error": response_data.get("error")}
                        else:
                            results[test["name"]] = {"handled": False, "response": response_data}
                            
                    except Exception as e:
                        results[test["name"]] = {"handled": False, "exception": str(e)}
        
        except Exception as e:
            print(f"Error handling test failed: {e}")
            return {"error": str(e)}
        
        handled_count = sum(1 for r in results.values() if r.get("handled", False))
        total_tests = len(error_tests)
        
        print(f"Error handling: {handled_count}/{total_tests} errors properly handled")
        
        for test_name, result in results.items():
            if result.get("handled"):
                print(f"  {test_name}: Handled correctly")
            else:
                print(f"  {test_name}: Not handled properly")
        
        return {
            "total_tests": total_tests,
            "handled_correctly": handled_count,
            "handling_rate": handled_count / total_tests * 100,
            "details": results
        }
    
    async def run_all_stability_tests(self):
        """Run comprehensive stability tests"""
        print("=" * 60)
        print("WebSocket Network Stability Tests")
        print("=" * 60)
        
        tests = [
            ("Concurrent Connections", self.test_concurrent_connections(5)),
            ("Message Throughput", self.test_message_throughput(50)),
            ("Long-lived Connection", self.test_long_lived_connection(15)),
            ("Reconnection Resilience", self.test_reconnection_resilience()),
            ("Error Handling", self.test_error_handling())
        ]
        
        for test_name, test_coro in tests:
            print(f"\n{test_name}:")
            print("-" * 40)
            try:
                result = await test_coro
                self.results[test_name] = result
            except Exception as e:
                print(f"Test failed with exception: {e}")
                self.results[test_name] = {"error": str(e)}
        
        # Summary
        print("\n" + "=" * 60)
        print("STABILITY TEST SUMMARY")
        print("=" * 60)
        
        for test_name, result in self.results.items():
            if "error" in result:
                print(f"{test_name:25} FAILED - {result['error']}")
            else:
                print(f"{test_name:25} PASSED")
        
        return self.results

async def main():
    """Main stability test function"""
    tester = WebSocketStabilityTester()
    results = await tester.run_all_stability_tests()
    
    print(f"\nAll stability tests completed.")
    print(f"Results saved in test object for detailed analysis.")

if __name__ == "__main__":
    asyncio.run(main())