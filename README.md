# yet another telegram bot

A Telegram bot that might help you set reminders and schedule messages. It's designed to work in a specific group and for a specific user. It includes features like restricted access for group admins and personal use... probably.



## Features

- Set reminders and schedule messages.
- Restricted access for group admins and a specific user.
- Supports various time units for scheduling (seconds, minutes, hours, days).
- Customizable unauthorized access messages.
- More features will be added... eventually. 😉 (...maybe)


## Setup

### Prerequisites

- Python 3.8+
- A Telegram bot token from [BotFather](https://core.telegram.org/bots#botfather)
- SQLite3

### Installation

1. Clone the repository:


2. Create a virtual environment and activate it in the cloned folder:

    ```sh
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3. Install the required packages:

    ```sh
    pip install -r requirements.txt
    ```

4. Set up your environment variables in a `.env` file:

    ```env
    BOT_TOKEN=your_telegram_bot_token
    LIST_OF_USERS=123456789,987654321  # Comma-separated list of admin user IDs
    GROUP_ID=-1002197057973  # Your group ID
    PERSONAL_USER_ID=123456789  # Your personal user ID
    ```



### Running the Bot

1. Start the bot:

    ```sh
    python main.py
    ```

## Usage

### Commands

- `/start` - Start the bot and get a welcome message.
- `/help` - Get help on how to use the bot.
- `/set <message> <time_offset>` - Schedule a message to be sent after a certain time. Example: `/set Hello 10m`
- `/remind <message> <interval>` - Set a recurring reminder. Example: `/remind Hello daily`
- `/cancel <job_id>` - Cancel a reminder by its ID.
- `/all` - View all reminders.

| Time Units | Intervals |
|------------|-----------|
| `s` - seconds | `daily` |
| `m` - minutes | `weekly` |
| `h` - hours | `hourly` |
| `hr` - hours | |
| `d` - days | |
| `w` - weeks | |
### Example

```sh
/set "Reminder message" 10m
/remind "Reminder message" daily