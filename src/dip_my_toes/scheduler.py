from datetime import date, datetime,timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import time
scheduler = BackgroundScheduler()


# Start the scheduler
scheduler.start()

# Define the function that is to be executed
def my_job():
    # datetime object containing current date and time
    now = datetime.now()

    # dd/mm/YY H:M:S
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)

dd = datetime.now() + timedelta(seconds=2)
scheduler.add_job(my_job, 'date',run_date=dd)
time.sleep(4)