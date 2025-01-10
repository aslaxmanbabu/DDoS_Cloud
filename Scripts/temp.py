import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Define NGINX executable and config paths
NGINX_EXEC_PATH = "D:\\Official\\Final\\Implementation\\nginx\\nginx.exe"
NGINX_CONF_PATH = "D:\\Official\\Final\\Implementation\\nginx\\conf\\nginx.conf"


def start_nginx():
    """
    Function to start the NGINX server with a custom config file path.
    """
    try:
        subprocess.run(
            [r"start", r"D:\Official\Final\Implementation\nginx\nginx.exe"], shell=True, check=True)

        print("NGINX server started successfully.")
        logging.info("NGINX server started successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error starting NGINX: {e}")
        raise


# Test the NGINX start function
if __name__ == "__main__":
    start_nginx()
