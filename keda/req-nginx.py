#!/usr/bin/env python3
"""
Kubernetes Load Balancer Testing Script
Tests load balancing distribution across pods
"""

import requests
import re
from collections import Counter
import sys
import time

def test_load_balancing(url, num_requests=20, delay=0):
    """
    Test load balancing by making multiple requests and tracking which pods respond.
    
    Args:
        url: Service URL to test
        num_requests: Number of requests to make
        delay: Delay between requests in seconds
    """
    print(f"Testing load balancing for: {url}")
    print(f"Making {num_requests} requests...\n")
    
    pod_names = []
    
    for i in range(1, num_requests + 1):
        try:
            # Make request
            response = requests.get(url, timeout=5)
            
            # Extract pod name using regex
            match = re.search(r'nginx-[a-z0-9-]+', response.text)
            
            if match:
                pod_name = match.group(0)
                pod_names.append(pod_name)
                print(f"Request {i:2d}: {pod_name}")
            else:
                print(f"Request {i:2d}: Could not extract pod name")
            
            # Optional delay between requests
            if delay > 0 and i < num_requests:
                time.sleep(delay)
                
        except requests.exceptions.RequestException as e:
            print(f"Request {i:2d}: Error - {e}")
    
    # Display results
    print("\n" + "="*50)
    print("LOAD BALANCING RESULTS")
    print("="*50)
    
    if pod_names:
        counter = Counter(pod_names)
        
        print(f"\nTotal successful requests: {len(pod_names)}")
        print(f"Number of unique pods: {len(counter)}")
        print("\nDistribution:")
        
        for pod, count in counter.most_common():
            percentage = (count / len(pod_names)) * 100
            bar = "█" * int(percentage / 2)
            print(f"  {pod}: {count:2d} ({percentage:5.1f}%) {bar}")
        
        # Check if load balancing is working
        if len(counter) > 1:
            print("\n✓ Load balancing is WORKING - traffic distributed across multiple pods")
        else:
            print("\n⚠ WARNING: All traffic went to a single pod - load balancing may not be working")
    else:
        print("\n✗ ERROR: No successful requests")

if __name__ == "__main__":
    # Default URL (change this to your service URL)
    default_url = "http://10.10.10.50"
    
    # Get URL from command line or use default
    url = sys.argv[1] if len(sys.argv) > 1 else default_url
    
    # Get number of requests from command line or use default
    num_requests = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    # Get delay from command line or use default
    delay = float(sys.argv[3]) if len(sys.argv) > 3 else 0
    
    test_load_balancing(url, num_requests, delay)
