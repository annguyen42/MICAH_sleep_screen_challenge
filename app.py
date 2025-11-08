import streamlit as st
import pandas as pd
import ssl
import certifi
import urllib3
import altair as alt
import requests  # <-- Add this
import io       # <-- Add this


st.title("MICAH Sleep Screen APP")

# Create a session with custom SSL configuration
#http = urllib3.PoolManager(
#    cert_reqs='CERT_REQUIRED',
#    ca_certs=certifi.where()
#)

# This line bypasses SSL verification.
ssl._create_default_https_context = ssl._create_unverified_context

# Replace this URL with your Google Sheet's sharing URL
#SHEET_URL = st.text_input(
#    "Enter your Google Sheet URL",
#    "https://docs.google.com/spreadsheets/d/1Til8NWWAy1MVv5An3yUzXXEBSHocgzfe8SgkjcvKOmg/edit#gid=0"
#)
# Paste your "Publish to web" CSV link here
# (Go to File > Share > Publish to web > Get link as CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRCbQDPet7-hUdVO0-CzfC3KrhHY6JbUO4UlMpUwbJJ_cp2LhqJSnX34jD-xqZcFAmI4FZZcEg9Wsuj/pub?output=csv"

# The *exact* column name for your classifier (teen, parent, teacher)
CLASSIFIER_COL = "Participant"  # Example: "Are you a teen, parent, or teacher?"

# The *exact* column name for the user's unique identifier
IDENTIFIER_COL = "Code Secret" # Example: "Email Address" or "Your Secret Code"

# The *exact* column names for the questions you want to plot
# I've included one numerical and one categorical example
NUMERICAL_QUESTION_COL = "SleepQuality"
CATEGORICAL_QUESTION_COL = "BedroomScreen"
# --- (End of configuration) ---


# --- 2. DATA LOADING ---

@st.cache_data(ttl=300)
def load_data(url):
    """Loads data from the published Google Sheet CSV link using requests."""
    try:
        # Use requests to get the data
        response = requests.get(url)
        
        # Raise an error if the download failed
        response.raise_for_status()
        
        # Use io.StringIO to treat the text content as a file
        # This is necessary for pandas to read the CSV from a string
        csv_data = io.StringIO(response.text)
        
        df = pd.read_csv(csv_data)
        return df
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error making request to Google Sheets: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error processing data: {e}. Is your SHEET_URL correct and published as CSV?")
        return pd.DataFrame()

# --- 3. HELPER FUNCTIONS ---

def plot_numerical_comparison(df, question_col, classifier_col, user_value):
    """
    Creates a histogram colored by the classifier, with a red line for the user's answer.
    """
    # Base chart: Histogram of all responses
    base = alt.Chart(df).mark_bar().encode(
        # X-axis: The numerical question, binned
        x=alt.X(f"{question_col}:Q", bin=True, title=question_col),
        # Y-axis: Count of responses
        y=alt.Y('count()', title="Number of Responses"),
        # Color: The classifier (teen, parent, teacher)
        color=alt.Color(f"{classifier_col}:N", title="Respondent Type"),
        # Tooltip to show details on hover
        tooltip=[f"{question_col}:Q", 'count()', f"{classifier_col}:N"]
    ).interactive()

    # Red rule: A vertical line for the user's specific answer
    rule = alt.Chart(pd.DataFrame({'my_answer': [user_value]})).mark_rule(color='red', strokeWidth=3).encode(
        x='my_answer:Q',
        tooltip=alt.Tooltip('my_answer', title="Your Answer")
    )
    
    # Combine the histogram and the red line
    return base + rule

def plot_categorical_comparison(df, question_col, classifier_col, user_value):
    """
    Creates a stacked bar chart for categorical data.
    """
    # Main chart: Stacked bar chart of all responses
    chart = alt.Chart(df).mark_bar().encode(
        # X-axis: The categorical question
        x=alt.X(f"{question_col}:N", title=question_col),
        # Y-axis: Count of responses
        y=alt.Y('count()', title="Number of Responses"),
        # Color: The classifier, creating the stack
        color=alt.Color(f"{classifier_col}:N", title="Respondent Type"),
        # Tooltip
        tooltip=[f"{question_col}:N", 'count()', f"{classifier_col}:N"]
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)
    
    # Also, explicitly show the user's answer
    st.markdown(f"**Your answer for this question was:** `{user_value}`")


# --- 4. STREAMLIT APP ---

st.set_page_config(page_title="Survey Results Dashboard", layout="wide")
st.title("📊 Survey Results Dashboard")

# Load the main dataframe
all_data = load_data(SHEET_URL)

if all_data.empty:
    st.stop()

# --- User Identification ---
st.header("Find Your Responses")
st.markdown(f"Enter the **{IDENTIFIER_COL}** you used when you filled out the form to see your results.")

# Get the user's unique ID
user_id = st.text_input(f"Your {IDENTIFIER_COL}:")

if not user_id:
    st.info("Please enter your identifier above to see your personalized report.")
    st.stop()

# --- Filter to find the user's data ---
# We use .str.lower() and .strip() to make matching more forgiving (e.g., " Me@Email.com " == "me@email.com")
try:
    user_data_row = all_data[all_data[IDENTIFIER_COL].str.lower().str.strip() == user_id.lower().strip()]
except AttributeError:
    # This happens if the identifier column isn't text (e.g., numbers)
    user_data_row = all_data[all_data[IDENTIFIER_COL] == user_id]


if user_data_row.empty:
    st.error(f"**Identifier not found:** We couldn't find any responses for `{user_id}`. Please check that you entered it correctly.")
    st.stop()

# Get the *first* match (in case of duplicates) as a simple Series
user_data = user_data_row.iloc[0]
user_classifier = user_data[CLASSIFIER_COL]

st.success(f"**Welcome!** We found your responses. You are in the **{user_classifier}** group.")
st.markdown("---")


# --- Results Display ---
st.header("Your Responses vs. All Responses")

# --- Plot 1: Numerical Question ---
st.subheader(f"Comparison for: {NUMERICAL_QUESTION_COL}")
try:
    user_numerical_answer = user_data[NUMERICAL_QUESTION_COL]
    
    # Check if data is valid before plotting
    if pd.isna(user_numerical_answer):
        st.warning(f"You did not provide an answer for '{NUMERICAL_QUESTION_COL}'.")
    else:
        # Create and display the plot
        numerical_chart = plot_numerical_comparison(
            df=all_data,
            question_col=NUMERICAL_QUESTION_COL,
            classifier_col=CLASSIFIER_COL,
            user_value=user_numerical_answer
        )
        st.altair_chart(numerical_chart, use_container_width=True)
        st.markdown(f"The red line shows your answer: **{user_numerical_answer}**")

except Exception as e:
    st.error(f"Could not plot numerical chart. Check your column names. Error: {e}")


# --- Plot 2: Categorical Question ---
st.subheader(f"Comparison for: {CATEGORICAL_QUESTION_COL}")
try:
    user_categorical_answer = user_data[CATEGORICAL_QUESTION_COL]
    
    if pd.isna(user_categorical_answer):
        st.warning(f"You did not provide an answer for '{CATEGORICAL_QUESTION_COL}'.")
    else:
        # Create and display the plot
        plot_categorical_comparison(
            df=all_data,
            question_col=CATEGORICAL_QUESTION_COL,
            classifier_col=CLASSIFIER_COL,
            user_value=user_categorical_answer
        )
        
except Exception as e:
    st.error(f"Could not plot categorical chart. Check your column names. Error: {e}")


# --- Show All Data (Optional) ---
st.markdown("---")
if st.checkbox("Show all raw (anonymized) data"):
    # Drop the identifier column before showing to anonymize it
    st.dataframe(all_data.drop(columns=[IDENTIFIER_COL]))


#if SHEET_URL:
#    try:
#        # Convert the Google Sheets URL to CSV export URL
#        sheet_id = SHEET_URL.split('/d/')[-1].split('/')[0]
#        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
#        
#        # Read the CSV data using urllib3 with proper SSL verification
#        response = http.request('GET', csv_url)
#        if response.status == 200:
#            # Create a DataFrame from the response content
#            from io import StringIO
#            df = pd.read_csv(StringIO(response.data.decode('utf-8')))
#            
#            # Display the data
#            st.dataframe(df)
#            
#            # Show some basic statistics
#            st.subheader("Data Summary")
#            st.write(df.describe())
#        else:
#            st.error(f"Failed to fetch data: HTTP {response.status}")
#            
#    except Exception as e:
#        st.error(f"An error occurred: {str(e)}")
#        st.info("Make sure the Google Sheet is publicly accessible (Anyone with the link can view)")
#
#st.subheader("Results")
## Print results.
#for row in df.itertuples():
#    st.write(f"{row.nom} has a :{row.animal}:")