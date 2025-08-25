"""
WebSocket Performance and Latency Analysis
Detailed performance metrics and benchmarks
"""

import asyncio
import json
import websockets
import time
import statistics
from datetime import datetime
import psutil
import gc

class WebSocketPerformanceTester:
    def __init__(self, url: str = "ws://localhost:8000/ws"):
        self.url = url
        self.performance_data = {}
        
    async def test_latency_distribution(self, samples: int = 100):
        """Test latency distribution with statistical analysis"""
        print(f"Testing latency distribution with {samples} samples...")
        
        try:
            async with websockets.connect(self.url) as websocket:
                await websocket.recv()  # Connection message
                
                latencies = []
                
                for i in range(samples):
                    start_time = time.perf_counter()
                    
                    message = {
                        "type": "ping",
                        "sequence": i,
                        "timestamp": start_time
                    }
                    
                    await websocket.send(json.dumps(message))
                    response = await websocket.recv()
                    
                    end_time = time.perf_counter()
                    latency = (end_time - start_time) * 1000  # Convert to ms
                    latencies.append(latency)
                    
                    # Small delay to avoid overwhelming the server
                    if i % 10 == 0:
                        await asyncio.sleep(0.001)
                
                # Statistical analysis
                mean_latency = statistics.mean(latencies)
                median_latency = statistics.median(latencies)
                std_dev = statistics.stdev(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
                
                # Percentiles
                p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
                p99 = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
                
                print(f"Latency Statistics ({samples} samples):")
                print(f"  Mean: {mean_latency:.2f}ms")
                print(f"  Median: {median_latency:.2f}ms")
                print(f"  Std Dev: {std_dev:.2f}ms")
                print(f"  Min: {min_latency:.2f}ms")
                print(f"  Max: {max_latency:.2f}ms")
                print(f"  95th percentile: {p95:.2f}ms")
                print(f"  99th percentile: {p99:.2f}ms")
                
                return {
                    "samples": samples,
                    "mean": mean_latency,
                    "median": median_latency,
                    "std_dev": std_dev,
                    "min": min_latency,
                    "max": max_latency,
                    "p95": p95,
                    "p99": p99,
                    "raw_data": latencies
                }
                
        except Exception as e:
            print(f"Latency test failed: {e}")
            return {"error": str(e)}
    
    async def test_memory_usage(self, connections: int = 10, duration: int = 30):
        """Test memory usage under load"""
        print(f"Testing memory usage with {connections} connections for {duration}s...")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        connections_list = []
        
        try:
            # Create multiple connections
            for i in range(connections):
                websocket = await websockets.connect(self.url)
                await websocket.recv()  # Connection message
                connections_list.append(websocket)
            
            print(f"Created {len(connections_list)} connections")
            
            # Monitor memory for duration
            memory_samples = []
            start_time = time.time()
            
            while time.time() - start_time < duration:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_samples.append(current_memory)
                
                # Send messages through all connections
                for i, ws in enumerate(connections_list):
                    try:
                        await ws.send(json.dumps({
                            "type": "test",
                            "connection": i,
                            "timestamp": time.time()
                        }))
                        await ws.recv()  # Consume response
                    except Exception:
                        pass  # Connection may have closed
                
                await asyncio.sleep(1)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Close connections
            for ws in connections_list:
                try:
                    await ws.close()
                except Exception:
                    pass
            
            # Force garbage collection
            gc.collect()
            await asyncio.sleep(2)
            
            cleanup_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            memory_increase = final_memory - initial_memory
            memory_per_connection = memory_increase / connections if connections > 0 else 0
            cleanup_efficiency = (final_memory - cleanup_memory) / memory_increase * 100 if memory_increase > 0 else 0
            
            print(f"Memory Analysis:")
            print(f"  Initial memory: {initial_memory:.2f} MB")
            print(f"  Peak memory: {max(memory_samples):.2f} MB")
            print(f"  Final memory: {final_memory:.2f} MB")
            print(f"  After cleanup: {cleanup_memory:.2f} MB")
            print(f"  Memory per connection: {memory_per_connection:.2f} MB")
            print(f"  Cleanup efficiency: {cleanup_efficiency:.1f}%")
            
            return {
                "initial_memory": initial_memory,
                "peak_memory": max(memory_samples),
                "final_memory": final_memory,
                "cleanup_memory": cleanup_memory,
                "memory_increase": memory_increase,
                "memory_per_connection": memory_per_connection,
                "cleanup_efficiency": cleanup_efficiency,
                "memory_samples": memory_samples
            }
            
        except Exception as e:
            # Clean up connections
            for ws in connections_list:
                try:
                    await ws.close()
                except Exception:
                    pass
            print(f"Memory test failed: {e}")
            return {"error": str(e)}
    
    async def test_cpu_usage(self, duration: int = 20):
        """Test CPU usage under WebSocket load"""
        print(f"Testing CPU usage for {duration}s...")
        
        try:
            async with websockets.connect(self.url) as websocket:
                await websocket.recv()  # Connection message
                
                cpu_samples = []
                start_time = time.time()
                message_count = 0
                
                while time.time() - start_time < duration:
                    # Sample CPU usage
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    cpu_samples.append(cpu_percent)
                    
                    # Send high-frequency messages
                    for _ in range(10):
                        await websocket.send(json.dumps({
                            "type": "test",
                            "message_id": message_count,
                            "timestamp": time.time()
                        }))
                        
                        try:
                            await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        except asyncio.TimeoutError:
                            pass
                        
                        message_count += 1
                
                avg_cpu = statistics.mean(cpu_samples)
                max_cpu = max(cpu_samples)
                messages_per_second = message_count / duration
                
                print(f"CPU Usage Analysis:")
                print(f"  Average CPU: {avg_cpu:.1f}%")
                print(f"  Peak CPU: {max_cpu:.1f}%") 
                print(f"  Messages sent: {message_count}")
                print(f"  Messages/second: {messages_per_second:.1f}")
                print(f"  CPU per message: {avg_cpu/messages_per_second:.4f}% per msg/s")
                
                return {
                    "duration": duration,
                    "message_count": message_count,
                    "messages_per_second": messages_per_second,
                    "avg_cpu": avg_cpu,
                    "max_cpu": max_cpu,
                    "cpu_per_message": avg_cpu/messages_per_second if messages_per_second > 0 else 0,
                    "cpu_samples": cpu_samples
                }
                
        except Exception as e:
            print(f"CPU test failed: {e}")
            return {"error": str(e)}
    
    async def test_scaling_performance(self, max_connections: int = 20):
        """Test performance scaling with increasing connections"""
        print(f"Testing scaling performance up to {max_connections} connections...")
        
        scaling_data = []
        
        for conn_count in range(1, max_connections + 1, 2):
            print(f"Testing with {conn_count} connections...")
            
            connections = []
            try:
                start_time = time.perf_counter()
                
                # Create connections
                for i in range(conn_count):
                    ws = await websockets.connect(self.url)
                    await ws.recv()  # Connection message
                    connections.append(ws)
                
                connection_time = time.perf_counter() - start_time
                
                # Test throughput
                messages_sent = 0
                throughput_start = time.perf_counter()
                
                for ws in connections:
                    await ws.send(json.dumps({
                        "type": "test",
                        "timestamp": time.perf_counter()
                    }))
                    messages_sent += 1
                
                # Collect responses
                responses_received = 0
                for ws in connections:
                    try:
                        await asyncio.wait_for(ws.recv(), timeout=2.0)
                        responses_received += 1
                    except asyncio.TimeoutError:
                        pass
                
                throughput_time = time.perf_counter() - throughput_start
                throughput = messages_sent / throughput_time if throughput_time > 0 else 0
                
                scaling_data.append({
                    "connections": conn_count,
                    "connection_time": connection_time,
                    "messages_sent": messages_sent,
                    "responses_received": responses_received,
                    "throughput": throughput,
                    "response_rate": responses_received / messages_sent * 100 if messages_sent > 0 else 0
                })
                
                # Clean up
                for ws in connections:
                    try:
                        await ws.close()
                    except Exception:
                        pass
                
                await asyncio.sleep(0.5)  # Brief pause between tests
                
            except Exception as e:
                print(f"Scaling test failed at {conn_count} connections: {e}")
                # Clean up
                for ws in connections:
                    try:
                        await ws.close()
                    except Exception:
                        pass
                break
        
        print(f"Scaling Performance Results:")
        print(f"{'Connections':<12} {'Conn Time':<10} {'Throughput':<12} {'Response Rate':<12}")
        print("-" * 50)
        
        for data in scaling_data:
            print(f"{data['connections']:<12} {data['connection_time']*1000:<10.1f}ms {data['throughput']:<12.1f} {data['response_rate']:<12.1f}%")
        
        return scaling_data
    
    async def run_performance_tests(self):
        """Run comprehensive performance tests"""
        print("=" * 60)
        print("WebSocket Performance Analysis")
        print("=" * 60)
        
        tests = [
            ("Latency Distribution", self.test_latency_distribution(100)),
            ("Memory Usage", self.test_memory_usage(5, 15)),
            ("CPU Usage", self.test_cpu_usage(15)),
            ("Scaling Performance", self.test_scaling_performance(10))
        ]
        
        for test_name, test_coro in tests:
            print(f"\n{test_name}:")
            print("-" * 40)
            try:
                result = await test_coro
                self.performance_data[test_name] = result
            except Exception as e:
                print(f"Test failed with exception: {e}")
                self.performance_data[test_name] = {"error": str(e)}
        
        return self.performance_data
    
    def generate_performance_report(self):
        """Generate performance summary report"""
        print("\n" + "=" * 60)
        print("PERFORMANCE ANALYSIS SUMMARY")
        print("=" * 60)
        
        if "Latency Distribution" in self.performance_data:
            latency = self.performance_data["Latency Distribution"]
            if "error" not in latency:
                print(f"Latency Performance: EXCELLENT")
                print(f"  Average latency: {latency['mean']:.2f}ms")
                print(f"  95% of requests under: {latency['p95']:.2f}ms")
        
        if "Memory Usage" in self.performance_data:
            memory = self.performance_data["Memory Usage"]
            if "error" not in memory:
                efficiency = "GOOD" if memory['memory_per_connection'] < 5 else "FAIR" if memory['memory_per_connection'] < 10 else "NEEDS IMPROVEMENT"
                print(f"Memory Efficiency: {efficiency}")
                print(f"  Memory per connection: {memory['memory_per_connection']:.2f}MB")
        
        if "CPU Usage" in self.performance_data:
            cpu = self.performance_data["CPU Usage"]
            if "error" not in cpu:
                efficiency = "EXCELLENT" if cpu['avg_cpu'] < 20 else "GOOD" if cpu['avg_cpu'] < 40 else "FAIR"
                print(f"CPU Efficiency: {efficiency}")
                print(f"  Average CPU usage: {cpu['avg_cpu']:.1f}%")
        
        if "Scaling Performance" in self.performance_data:
            scaling = self.performance_data["Scaling Performance"]
            if "error" not in scaling and scaling:
                max_tested = max(item['connections'] for item in scaling)
                avg_response_rate = statistics.mean(item['response_rate'] for item in scaling)
                scalability = "EXCELLENT" if avg_response_rate > 95 else "GOOD" if avg_response_rate > 80 else "FAIR"
                print(f"Scalability: {scalability}")
                print(f"  Tested up to {max_tested} concurrent connections")
                print(f"  Average response rate: {avg_response_rate:.1f}%")

async def main():
    """Main performance test function"""
    tester = WebSocketPerformanceTester()
    
    print("Starting WebSocket performance analysis...")
    await tester.run_performance_tests()
    tester.generate_performance_report()
    
    print("\nPerformance analysis completed.")

if __name__ == "__main__":
    asyncio.run(main())