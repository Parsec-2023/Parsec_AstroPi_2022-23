from datetime import datetime, timedelta
from time import sleep

#this code runs a group of tasks for 30 sec. Each task is programmed to run at a different frequency, so the main loop calls each of them when the required time has passed. While the program is waiting to run each task, it isn't stopped by delays, so it can do other things. It performs 1000 loops per second continuously checking for tasks to do.

#task 1 runs each 2 sec
#task 2 runs each 5 sec
#task 3 runs each 1 sec

# Create a `datetime` variable to store the start time
start_time = datetime.now()
# Create a `datetime` variable to store the current time
now_time = start_time
#store the time each task has run for the last time
prev_time_task1 = now_time
prev_time_task2 = now_time
prev_time_task3 = now_time
#...
# Run a loop for 30 seconds since start time
while (now_time < start_time + timedelta(seconds=30)):
  #check if it is time to run task 1
  if (now_time >= prev_time_task1 + timedelta(seconds = 2)):
    print("task that runs every 2 sec")
    prev_time_task1 = now_time
  #check if it is time to run task 2
  if (now_time >= prev_time_task2 + timedelta(seconds = 5)):
    print("task that runs every 5 sec")
    prev_time_task2 = now_time
  #check if it is time to run task 3
  if (now_time >= prev_time_task3 + timedelta(seconds = 1)):
    print("task that runs every 1 sec")
    prev_time_task3 = now_time
  sleep(0.001) #wait 1 millisec
    # Update the current time
  now_time = datetime.now()
# tell us when the loop has finished
print("30 sec elapsed")