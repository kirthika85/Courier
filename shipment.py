import streamlit as st
import pandas as pd
import os
import openai
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set API key for OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
csv_location = "data/courier_rates.csv"

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Load the CSV and return as a DataFrame
def df_to_json(csv_location):
    df = pd.read_csv(csv_location)
    return df

# Function to clear text input
def clear_text():
    st.session_state.my_text = st.session_state.widget
    st.session_state.widget = ""

# Define function to interact with OpenAI API
def query_openai(prompt, df):
    markdown_str = df.to_markdown(tablefmt="grid")
    messages = [
        {"role": "system", "content": "You are a helpful courier assistant."}
    ]
    
    for message in st.session_state["chat_history"]:
        messages.append({"role": message["role"], "content": message["content"]})

    messages.append({
        "role": "system",
        "content": f"""
            You are given a table of data which includes start location pincode, destination pincode, weight (in lbs), height, width, length in cms, and cost in dollars.
            Interactively ask for information with appropriate units until all relevant data is gathered. Do not expect the user to provide all details at once.
            Use the table to respond with the cost for the given details.
            If asked an irrelevant question, respond: 'I am sorry, this is not relevant to the context. Kindly ask a valid question.'
            \nActual data:\n{markdown_str}
        """
    })
    messages.append({"role": "user", "content": prompt})

    logger.debug("Sending messages to OpenAI: %s", messages)
    
    # Make API call to OpenAI with chat history included
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.2
    )
    answer = response.choices[0].message['content']
    logger.debug("Received response from OpenAI: %s", response)
    return answer

# Load data
df = df_to_json(csv_location)

# Set up Streamlit interface
st.title("Courier Agent")
st.write("I am a Smart Courier Agent! How can I help you?")

chat_container = st.empty()

def render_chat():
    chat_content = ""
    for message in st.session_state["chat_history"]:
        if message["role"] == "user":
            chat_content += f"**You:** {message['content']}\n\n"
        else:
            chat_content += f"**Courier Agent:** {message['content']}\n\n"
    chat_container.markdown(chat_content, unsafe_allow_html=True)

render_chat()
user_input = st.text_input("Enter your question:", placeholder=" (e.g., 'I want to send courier from pincode 00926 to 11368. I need to know the amount.')")

if user_input:
    with st.spinner("Fetching response..."):
        # Query OpenAI and update chat history
        answer = query_openai(user_input, df)
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        st.session_state["chat_history"].append({"role": "assistant", "content": answer})
        
        render_chat()
