# Overview
This is an exploratory app to experiment with pandasai and create a bot with streamlit for data analytics.
- Clone repository to get started
  ```shell
  git clone https://github.com/ahmed-jibran/pandasai-streamlit-bot.git
  ```
# Create virtual environment with required packages
## Linux or MacOS
```shell
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```
## Windows
```shell
  py -m venv .venv
  # activate virtual environment
  .venv\Scripts\activate 
  # Install requirements
  py -m pip install -r requirements.txt
```

# Run App
After installing required packages successfully, application can be run using streamlit.
- Export OPENAI Key
    ```shell
    # Using Windows Power Shell
    Set-Item -Path env:OPEN_AI_API_KEY -Value "<your-openai-key>"
    
    # Using bash Linux / MacOS
    export OPEN_AI_API_KEY="<your-openai-key>"
    ```
- Run App
    ```shell
    streamlit run analytics-bot.py
    ```
Access application at http://localhost:8501

This app is tested using https://www.kaggle.com/datasets/aungpyaeap/supermarket-sales?select=supermarket_sales+-+Sheet1.csv

Following are some of the sample questions that can be asked

- Which city has the highest gross income
- Show me data for only Yangon city
- Plot gross income by city
- Which product line is most expensive and plot a pie graph for a product line

