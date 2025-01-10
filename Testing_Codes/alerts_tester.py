import requests
import time

# Function to send HTTP requests


def send_requests(url, num_requests, delay=1):
    for _ in range(num_requests):
        try:
            response = requests.get(url)
            print(
                f"Sent request to {url}, Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error sending request to {url}: {e}")
        time.sleep(delay)

# Test the conditions


def test_conditions(url):
    print(f"Testing DDoS conditions for {url}")

    # Condition 1: More than 10 requests in 2 seconds (burst traffic)
    print("Testing for more than 10 requests in 2 seconds...")
    # 11 requests with 0.1 second delay (should trigger alert)
    send_requests(url, 50, delay=0.1)

    # Condition 2: Large traffic increase (e.g., 50 requests)
    print("Testing for traffic increase > 50 requests...")
    # 51 requests with 0.1 second delay (should trigger alert)
    send_requests(url, 150, delay=0.1)

    # Condition 3: More than 5 requests to root URI ("/")
    print("Testing for more than 5 requests to root (/)...")
    # 6 requests to the root URI (should trigger alert)
    send_requests(f"{url}/", 20, delay=0.1)


if __name__ == "__main__":
    # Replace with your server's URL
    url_to_test = "http://127.0.0.1:80"
    test_conditions(url_to_test)
