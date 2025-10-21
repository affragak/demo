#!/usr/bin/env python3
"""
KEDA Autoscaling Load Test Script
Generates load to trigger Kubernetes autoscaling and monitors pod count
"""

import requests
import threading
import time
import sys
from collections import Counter
import subprocess
import re

class LoadTester:
    def __init__(self, url, duration=120, concurrent_users=10, requests_per_user=1000):
        self.url = url
        self.duration = duration
        self.concurrent_users = concurrent_users
        self.requests_per_user = requests_per_user
        self.results = []
        self.pod_names = []
        self.errors = 0
        self.success = 0
        self.running = True
        self.lock = threading.Lock()
        
    def make_requests(self, user_id):
        """Make continuous requests until duration expires"""
        start_time = time.time()
        user_requests = 0
        
        while self.running and (time.time() - start_time) < self.duration:
            try:
                response = requests.get(self.url, timeout=5)
                
                # Extract pod name
                match = re.search(r'nginx-[a-z0-9-]+', response.text)
                
                with self.lock:
                    if match:
                        pod_name = match.group(0)
                        self.pod_names.append(pod_name)
                        self.success += 1
                    else:
                        self.success += 1
                    
                user_requests += 1
                
                # Small delay to control request rate (optional)
                # time.sleep(0.01)
                
            except requests.exceptions.RequestException as e:
                with self.lock:
                    self.errors += 1
        
        print(f"User {user_id:2d} completed: {user_requests} requests")
    
    def get_pod_count(self):
        """Get current number of nginx pods"""
        try:
            result = subprocess.run(
                ['kubectl', 'get', 'pods', '-l', 'app=nginx', '--no-headers'],
                capture_output=True,
                text=True,
                timeout=5
            )
            pods = result.stdout.strip().split('\n')
            return len([p for p in pods if p])
        except:
            return 0
    
    def get_hpa_status(self):
        """Get HPA status"""
        try:
            result = subprocess.run(
                ['kubectl', 'get', 'hpa', 'keda-hpa-nginx-scaler', '-o', 'custom-columns=CURRENT:status.currentReplicas,DESIRED:status.desiredReplicas', '--no-headers'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except:
            return "N/A"
    
    def monitor_scaling(self):
        """Monitor pod scaling in real-time"""
        print("\n" + "="*70)
        print("MONITORING POD SCALING")
        print("="*70)
        print(f"{'Time (s)':<10} {'Pods':<10} {'Requests':<12} {'Errors':<10} {'HPA Status':<20}")
        print("-"*70)
        
        start_time = time.time()
        last_pod_count = 0
        
        while self.running:
            elapsed = int(time.time() - start_time)
            pod_count = self.get_pod_count()
            hpa_status = self.get_hpa_status()
            
            with self.lock:
                total_requests = self.success + self.errors
            
            print(f"{elapsed:<10} {pod_count:<10} {total_requests:<12} {self.errors:<10} {hpa_status:<20}", end='\r')
            
            # Alert on scaling events
            if pod_count != last_pod_count and last_pod_count > 0:
                print(f"\n🚀 SCALING EVENT: {last_pod_count} -> {pod_count} pods")
            
            last_pod_count = pod_count
            time.sleep(2)
        
        print()  # New line after monitoring
    
    def run_load_test(self):
        """Run the load test with multiple concurrent users"""
        print(f"\n{'='*70}")
        print(f"KEDA AUTOSCALING LOAD TEST")
        print(f"{'='*70}")
        print(f"Target URL: {self.url}")
        print(f"Duration: {self.duration} seconds")
        print(f"Concurrent Users: {self.concurrent_users}")
        print(f"Initial Pod Count: {self.get_pod_count()}")
        print(f"{'='*70}\n")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_scaling)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Start load generation threads
        threads = []
        start_time = time.time()
        
        for i in range(self.concurrent_users):
            thread = threading.Thread(target=self.make_requests, args=(i+1,))
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        self.running = False
        time.sleep(3)  # Wait for monitor to finish
        
        # Display final results
        self.display_results(time.time() - start_time)
    
    def display_results(self, actual_duration):
        """Display test results"""
        print("\n" + "="*70)
        print("LOAD TEST RESULTS")
        print("="*70)
        
        total_requests = self.success + self.errors
        
        print(f"\nTest Duration: {actual_duration:.1f} seconds")
        print(f"Total Requests: {total_requests}")
        print(f"Successful: {self.success}")
        print(f"Errors: {self.errors}")
        print(f"Requests/sec: {total_requests/actual_duration:.2f}")
        print(f"Final Pod Count: {self.get_pod_count()}")
        
        if self.pod_names:
            print("\n" + "="*70)
            print("POD DISTRIBUTION")
            print("="*70)
            
            counter = Counter(self.pod_names)
            
            for pod, count in counter.most_common():
                percentage = (count / len(self.pod_names)) * 100
                bar = "█" * int(percentage / 2)
                print(f"{pod}: {count:5d} ({percentage:5.1f}%) {bar}")
        
        print("\n" + "="*70)
        print("💡 TIP: Run 'kubectl get hpa' to see autoscaling details")
        print("💡 TIP: Run 'kubectl get pods -l app=nginx -w' to watch pods")
        print("="*70 + "\n")


if __name__ == "__main__":
    # Configuration
    default_url = "http://10.10.10.50"
    default_duration = 120  # 2 minutes
    default_concurrent_users = 20  # Concurrent threads
    
    # Parse command line arguments
    url = sys.argv[1] if len(sys.argv) > 1 else default_url
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else default_duration
    concurrent_users = int(sys.argv[3]) if len(sys.argv) > 3 else default_concurrent_users
    
    # Create and run load tester
    tester = LoadTester(url, duration, concurrent_users)
    
    try:
        tester.run_load_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        tester.running = False
        time.sleep(2)
        tester.display_results(duration)
