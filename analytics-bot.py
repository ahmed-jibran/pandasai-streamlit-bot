import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from pandasai import SmartDatalake # for multiple files
from pandasai.llm.openai import OpenAI
from pandasai.responses.streamlit_response import StreamlitResponse
import matplotlib.pyplot as plt
import plotly.express as px
import logging
import time
import plotly.tools as tls

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to the console
        # You can add more handlers, like logging to a file, by adding additional handlers here
    ]
)

# TODO: Fix deprecated option
st.set_option('deprecation.showPyplotGlobalUse', False)

#set maximum row,column size for uploaded files
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

# load environment variables
load_dotenv()

# check open_ai_api_key in env, if it is not defined as a variable
#it can be added manually in the code below

if os.environ.get("OPEN_AI_API_KEY") is None or os.environ.get("OPEN_AI_API_KEY") =="":
    print("open_ai_api_key is not set as environment variable")
else:
    print("Open AI API Key is set")

#get open_ai_api_key
OPEN_AI_API_KEY= os.environ.get("OPEN_AI_API_KEY")

# set tittle for Streamlit UI
st.title("Analytics Bot")
st.info("Upload a file and start asking questions")

#set formats of files allowed to upload
file_formats = {
    "csv": pd.read_csv,
    "xls": pd.read_excel,
    "xlsx": pd.read_excel,
    "xlsm": pd.read_excel,
    "xlsb": pd.read_excel,
}

#define a function for file formats
#check the file format among the list above
def load_data(uploaded_file):
   # ext = os.path.splitext(uploaded_file.name)[1][1:].lower()
    try:
        ext = os.path.splitext(uploaded_file.name)[1][1:].lower()
    except:
        ext = uploaded_file.split(".")[-1]
    if ext in file_formats:
        return file_formats[ext](uploaded_file)
    #if file format does not match give message
    else:
        st.error(f"Unsupported file format: {ext}")
        return None


def try_show_plots(query: str):
    if plt.gcf():
        if 'pie' in query.lower():
            fig = px.pie({query})
            st.pyplot(plt.gcf())
            return True
        if  'bar' in query.lower():
            fig = px.bar({query})
            st.pyplot(plt.gcf())
            return True
        if 'bubble' in query.lower():
            fig=px.scatter({query})
            st.pyplot(plt.gcf())
            return True
        if 'dot' in query.lower():
            fig=px.scatter({query})
            st.pyplot(plt.gcf())
            return True
        if 'time series' in query.lower():
            fig=px.line({query})
            st.pyplot(plt.gcf())
            return True
        if 'histogram' in query.lower():
            fig=px.histogram({query})
            st.pyplot(plt.gcf())
            return True    
        if 'plot' in query.lower():
            st.pyplot(plt.gcf())
            return True

    return False

def process_query(query: str):
    response = df_ai.chat(query)
    code =df_ai.last_code_executed
    result = df_ai.last_result
    return response, code, result

def on_submit_query():
        user_query = st.session_state.user_query
        # Display user message in chat message container
        st.chat_message("user").markdown(user_query)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_query})        
        st.spinner("Calculating...")
        time.sleep(0.3)
        response, code, result = process_query(user_query)
        logging.debug(f"response: {response}")
        logging.debug(f"code: {code}")
        logging.debug(f"result: {result}")
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            handled = False
            if result:
                if result["type"] == "string":
                    handled = True
                    st.write(response)            
                elif result["type"] == "plot":
                    handled = True
                    st.write(f"Chart saved at: {response}")
                    try_show_plots(user_query)
                elif result["type"] == "dataframe":
                    handled = True
                    st.dataframe(result["value"])

                if not handled:
                    st.write(f"Cannot render response type: \"{result['type']}\"\n\nresponse: {response}")

        # Add assistant response to chat history
        # st.session_state.messages.append({"role": "assistant", "content": response})

# upload a file from ui
uploaded_files = st.file_uploader("Please upload data file",
                                 type =list(file_formats.keys()),)# accept_multiple_files=True,

#check the uploaded file whether empty or not
if uploaded_files:
    dataframe = load_data(uploaded_files)
    if dataframe.empty:
        #if file is empty give a message
        st.write("The given data is empty, please upload a full file for asking questions")
    # if file is full, list first 3 rows
    else:
        st.write(dataframe.head(3))
    # give a general description of data
    if st.sidebar.button("Statistics"):
        if dataframe.empty:
            st.write("No description for an empty file")
    # if uploaded file is full, return description of data
        else:
            df_desc = dataframe.describe()
            st.write(df_desc)
    if st.sidebar.button("Information"):
        df_info=dataframe.info()
        st.write(df_info)
    if st.sidebar.button("Mean"):
        df_mean=dataframe.mean()
        st.write(df_mean)
    if st.sidebar.button("Median"):
        df_med=dataframe.median()
        st.write(df_med)
    if st.sidebar.button("Sample"):
        df_sample=dataframe.sample()
        st.write(df_sample)
    if st.sidebar.button("Correlation"):
        df_corr = dataframe.corr()
        st.write(df_corr)
    if st.sidebar.button("Drop All Duplicates"):
        df_drop_all=dataframe.drop_duplicates()
        st.write(df_drop_all)
    if st.sidebar.button("Drop All Null Values"):
        df_drop_null =dataframe.dropna(how='all')
        st.write(df_drop_null)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if uploaded_files:
    #define preffered llm
    llm = OpenAI(api_token=OPEN_AI_API_KEY, model="gpt-3.5-turbo")

    # convert to SmartDatalake
    df_ai = SmartDatalake([dataframe],
                              config={"save_logs": True,
                                      "verbose": True,
                                      "enforce_privacy": True,
                                      "enable_cache": True,
                                      "use_error_correction_framework": True,
                                      "max_retries": 3,
                                      #"custom_prompts": {},
                                      "open_charts": True,
                                      "save_charts": False,
                                      "save_charts_path": "exports/charts",
                                      "custom_whitelisted_dependencies": [],
                                      "llm": llm,
                                      #"llm_options": null,
                                      "saved_dfs": []
                                    , "response_parser": StreamlitResponse
                                      #  share a custom sample head to the LLM  "custom_head": head_df

                                 }
                              )

# TODO: Convert it into conversational bot instead of using text area
# if uploaded_files:
#     user_query = st.chat_input(f"Ask me about: {uploaded_files.name}", on_submit=on_submit_query, key="user_query")

    user_query =st.text_area(f"Ask me about: {uploaded_files.name}")
    st.info("Hint: Specifiy chart type [pie | bar | 'bubble' | dot | time series | histogram] in query to draw specific chart")

    # get the request to generate an asnwer for the question
    if st.button("Generate Response"):
        # check uploaded file, if the file is empty give a message
        if dataframe.empty:
            st.write("No response for an empty file")
        #show the model's response as an answer
        else:
            if user_query:
                with st.spinner("Generating..."):
                    response, code, result = process_query(user_query)
                    tab_response, tab_code =st.tabs(["Response", "Code"])
                    with tab_response:
                        if result and result["type"] == "plot":
                            st.write(f"Chart is saved at: {response}")
                        else:
                            st.write(response)            
                        try_show_plots(user_query)
                    with tab_code:
                        st.write(f"Generated code for the {user_query} :")
                        st.code(df_ai.last_code_executed, language='python')
            #if the question is empty give a message
            else:
                st.warning("Please enter a question")
