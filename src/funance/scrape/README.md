# Use Selenium Webdriver to scrape data from supported providers.

## Getting started

1. Export
    
    For regular usage/one-time run.
    
    This will:
   
    - start the chromedriver service & open a browser
    - scrape data & write json file
    - close the browser window
    - stop the chromedriver service

    ```
    (venv)$ funance scrape
    ```

    For development.
    
    This will:
    
    - start the chromedriver service & open a browser
    - write session data to a json file
    - scrape data & write json file
    - keep the chromedriver service running
    - keep the browser window open
    
    ```
    # start the service first to get a SESSION_ID
    (venv)$ funance service start
    Keeping service alive...
   
    # then in another terminal, re-use the session as many times as needed while code changes are being made.
    (venv)$ funance export --session
    ```

## JSON output

[JSON Spec](docs/spec.json)
