import time


print("Stub process running. Stop the container to exit.")

try:
	while True:
		time.sleep(60)
except KeyboardInterrupt:
	print("Shutting down.")