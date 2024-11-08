import streamlit as st
import pandas as pd
import os
import openai
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load API key from environment variables
openai.api_key = os.environ.get("OPENAI_API_KEY")
csv_location = "courier_rates.csv"

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

def df_to_json(csv_location):
    df = pd.read_csv(csv_location)
    return df

def clear_text():
    st.session_state.my_text = st.session_state.widget
    st.session_state.widget = ""

# Function to interact with OpenAI, including chat history and shipment data
def query_openai(prompt, df):
    markdown_str = df.to_markdown(tablefmt="grid")
    messages = [
        {"role": "system", "content": "You are a helpful courier assistant."}
    ]
    
    for message in st.session_state["chat_history"]:
        messages.append({"role": message["role"], "content": message["content"]})

    # Add current system message and user prompt
    messages.append({
        "role": "system",
        "content": f"""
            You are given with a table of actual data which includes start location pincode, destination or end pincode, weight (in lbs), height, width, length in cms, and cost in dollars.
            Ask questions interactively to gather information needed to determine courier cost. Use units appropriately. Do not calculate rates.
            When all details are gathered, consult the table and provide the cost based on the available data.
            If asked an unrelated question, respond: 'I am sorry, this is not relevant to the context. Kindly ask a valid question.'
            \nActual data:\n{markdown_str}
        """
    })
    messages.append({"role": "user", "content": prompt})

    logger.debug("Sending messages to OpenAI: %s", messages)

    # Call OpenAI API
    #response = openai.ChatCompletion.create(
    #    model="gpt-4",  # Confirm your model name
    #    messages=messages,
    #    temperature=0.2
    #)
    openai.api_key = OPENAI_API_KEY
    response = openai.Chat.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=0.2
        )
    answer = response.choices[0].message['content']
    logger.debug("Received response from OpenAI: %s", response)
    return answer

# Read data from CSV
df = df_to_json(csv_location)

# Streamlit UI
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
user_input = st.text_input("Enter your question:", placeholder="(e.g., 'I want to send courier from pincode 00926 to 11368. I need to know the amount.')")

if user_input:
    with st.spinner("Fetching response..."):
        # Query OpenAI and update chat history
        answer = query_openai(user_input, df)
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        st.session_state["chat_history"].append({"role": "assistant", "content": answer})
        
        # Clear the input box after sending
        st.experimental_rerun()
