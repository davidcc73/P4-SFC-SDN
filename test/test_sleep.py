import time

def main():
    num_iterations = 500
    sleep_durations_s = 0.001
    sleep_durations = []

    for _ in range(num_iterations):
        start_time = time.time()
        time.sleep(sleep_durations_s)
        end_time = time.time()

        elapsed_time_ms = (end_time - start_time) * 1000
        sleep_durations.append(elapsed_time_ms)

    # Exclude the maximum sleep duration
    max_duration = max(sleep_durations)
    sleep_durations.remove(max_duration)

    # Calculate the average of the remaining durations
    average_duration = sum(sleep_durations) / len(sleep_durations)

    # Print the average duration
    print(f"\nAverage duration (excluding the longest): {average_duration:.2f} milliseconds")

    # Calculate and print the deviation from the assigned sleep period in milliseconds
    deviation = average_duration - sleep_durations_s * 1000
    print(f"Deviation from assigned sleep period: {deviation:.3f} milliseconds")

if __name__ == "__main__":
    main()
