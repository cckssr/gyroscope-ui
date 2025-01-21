import threading
import random
import time

# Global data variable
data = []

# Function to generate random numbers and append to data
def generate_random_numbers():
    global data
    while True:
        number = random.randint(1, 100)
        data.append(number)
        interval = random.uniform(0.1, 1.0)
        time.sleep(interval)

# Main function to print the total of data every second
def main():
    global data
    threading.Thread(target=generate_random_numbers, daemon=True).start()
    try:
        while True:
            time.sleep(1)
            total = sum(data)
            print(f"Total: {total}")
    except KeyboardInterrupt:
        print("Stopping the thread.")
    # while True:
    #     time.sleep(1)
    #     total = sum(data)
    #     print(f"Total: {total}")

if __name__ == "__main__":
    main()