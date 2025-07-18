import re
from datetime import datetime


with open('sample-log.log', 'r') as file: 
    logs = file.read()

list_of_logs = logs.strip().split('\n')

# defining pattern to match each log to
log_pattern = re.compile(
    r'(?P<ip>\S+) - (?P<country>\S+) - \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) (?P<protocol>[^"]+)" '
    r'(?P<status>\d{3}) (?P<size>\d+) '
    r'"(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)" (?P<response_time>\d+)'
)


# organising each log into a dict with each component as a key
def groupdict_logs(logs):
    parsed_logs = []
    for log in logs:
        match = log_pattern.match(log)
        if match:
            log_dict = match.groupdict()
            log_dict['possible_bot'] = False # adding possible bot key to each dict
            parsed_logs.append(log_dict)
    return parsed_logs

parsed_logs = groupdict_logs(list_of_logs)

def check_user_agent(logs):
    for log in logs:
        user_agent = log['user_agent'].lower()
        if 'bot' in user_agent or 'crawler' in user_agent or 'spider' in user_agent: # check for bot keywords
            log['possible_bot'] = True

        if user_agent is None or user_agent == '-': # check if empty
            log['possible_bot'] = True
        
        if 'python' in user_agent or 'sql' in user_agent or 'curl' in user_agent: # check for script, sql injection keywords
            log['possible_bot'] = True 
    return logs

def check_high_requests(logs, time_window_seconds=60, threshold=10):
    for log in logs:
        log['datetime'] = datetime.strptime(log['timestamp'], "%d/%m/%Y:%H:%M:%S")

    # group logs from the same ip address
    logs_by_ip = {}
    for i, log in enumerate(logs):
        ip = log['ip']
        logs_by_ip.setdefault(ip, []).append((i, log['datetime']))  # store index and datetime

    # check frequency of requests in the time window
    for ip, entries in logs_by_ip.items():
        # sort entries by datetime
        entries.sort(key=lambda x: x[1])
        start = 0

        for end in range(len(entries)):
            while (entries[end][1] - entries[start][1]).total_seconds() > time_window_seconds:
                start += 1
            if (end - start + 1) > threshold:
                # mark all logs in window for this ip as possible bots
                for idx in range(start, end + 1):
                    log_index = entries[idx][0]
                    logs[log_index]['possible_bot'] = True
                break
    
    # remove unnecessary key
    for log in parsed_logs:
        log.pop('datetime', None)

    return parsed_logs

def check_response_time(logs):
    for log in logs:
        response_time = int(log['response_time'])
        if response_time <= 30:
            log['possible bot'] = True

    return logs

def sum_possible_bots(logs):
    sum = 0
    for log in logs:
        if log['possible_bot'] == True:
            sum += 1
    return sum

def calc_percentage_bots(logs, num_bots):
    percentage = round((num_bots/len(logs))*100, 2)
    return percentage


parsed_logs = check_user_agent(parsed_logs)
parsed_logs = check_high_requests(parsed_logs)
parsed_logs = check_response_time(parsed_logs)

num_possible_bots = sum_possible_bots(parsed_logs)
percentage_bots = calc_percentage_bots(parsed_logs, num_possible_bots)

print("The total number of bot-like logs: "+ str(num_possible_bots))
print("The total number of logs: "+ str(len(parsed_logs)))
print("The percentage of requests likely to be bots: "+ str(percentage_bots)+"%")




