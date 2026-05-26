# import libraries 
import os
import json
import random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker
import streamlit as st
from dotenv import load_dotenv

# environment initialization 
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

fake = Faker('en_US')

# user request --> Google GenAI SDK --> JSON
def fetch_schema(user_prompt, validated_key):

    # SDK initialization 
    try:
        from google import genai
        client = genai.Client(api_key=validated_key)
    except Exception:
        st.error("Ensure SDK installation")
        return None

    # instruction set (GenAI guidelines behaviour rules)
    system_instruction = """
    You are a database architect. The user will ask for a type of dataset.
    You must output a raw, valid JSON object containing a parent-child table configuration blueprint.
    Do not include markdown blocks, text wrapping, or trailing commas. 

    The JSON must follow this exact structure:
    {
        "parent_name": "Users Table Name (e.g. Employees)",
        "child_name": "Linked Table Name (e.g. Timesheets)",
        "parent_schema": {
            "primary_id_col": {"type": "unique_id", "prefix": "EMP-", "digits": 5},
            "name_col": {"type": "faker_field", "provider": "name"},
            "secondary_col": {"type": "categorical", "choices": ["HR", "IT", "Sales"], "weights": [0.2, 0.5, 0.3]},
            "date_col": {"type": "faker_field", "provider": "date_between", "start_date": "-2y", "end_date": "today"}
        },
        "child_schema": {
            "child_id_name": "timesheet_id",
            "child_id_prefix": "TS-",
            "category_label": "task_type",
            "categories": {
                "Coding": [1.0, 8.0],
                "Meetings": [0.5, 3.0],
                "Admin": [0.5, 2.0]
            },
            "metric_label": "hours_logged",
            "extra_fields": {
                "status": {"type": "categorical", "choices": ["Approved", "Pending"]}
            }
        }
    }

    Rules for data types:
    - For unique IDs, use {"type": "unique_id", "prefix": "...", "digits": 5}
    - For typical profiles (names, emails, cities, jobs), use {"type": "faker_field", "provider": "..."}. Valid providers: name, email, city, company, job, phone_number, street_address, zipcode.
    - One field in the parent_schema MUST be a date field with provider "date_between".
    - For categories, use {"type": "categorical", "choices": [...], "weights": [...]}.
    - For the child_schema "categories", provide 3 to 5 realistic domain subcategories mapped to a list [min_value, max_value] representing financial/numerical transaction sizes.
    """

    # API call
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Generate a dataset schema blueprint for: {user_prompt}",
            config={"response_mime_type": "application/json", "system_instruction": system_instruction}
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Failed to generate schema: {e}")
        return None

# populating generated fields 
def parent_data(schema, num_rows):
    data = {}
    temporal_context = None     # to store --> sync with child
    temporal_col_name = None    # to store --> sync with child 
    
    # extraction 
    for col_name, rules in schema.items():
        col_type = rules.get("type")
        
        # TYPE == unique_id
        if col_type == "unique_id":
            prefix = rules.get("prefix", "ID-")
            digits = rules.get("digits", 5)
            pool = random.sample(range(10**(digits-1), (10**digits) - 1), num_rows)
            data[col_name] = [f"{prefix}{num}" for num in pool]

        # TYPE == categorical     
        elif col_type == "categorical":
            choices = rules.get("choices")
            weights = rules.get("weights", None)

            # (fix: data had mismatch in num(weight) & num(choice count) raising conflict)
            if weights and len(weights) != len(choices):
                weights = None
            data[col_name] = random.choices(choices, weights=weights, k=num_rows)
        
        # TYPE == faker_field
        elif col_type == "faker_field":
            provider = rules.get("provider", "name")

            # lookup in faker library 
            fake_method = getattr(fake, provider, fake.name)
            
            # date/time handling to avoid irrational relations 
            if provider == "date_between":
                date_objs = [fake_method(start_date=rules.get("start_date", "-2y"), end_date=rules.get("end_date", "today")) for _ in range(num_rows)]
                temporal_context = date_objs
                temporal_col_name = col_name
                data[col_name] = [d.strftime('%Y-%m-%d') for d in date_objs]
            
            # fields other than date/time are populated using the relevant faker method n times
            else:
                data[col_name] = [fake_method() for _ in range(num_rows)]
                
    # return
    return pd.DataFrame(data), temporal_context, temporal_col_name

def child_data(df_parent, parent_dates, child_config, num_rows):

    # id extraction and look-up dictionary 
    parent_id_col = df_parent.columns[0]
    parent_ids = df_parent[parent_id_col].tolist()
    parent_date_map = dict(zip(parent_ids, parent_dates))
    
    categories = child_config["categories"]
    cat_keys = list(categories.keys())
    now_dt = datetime.now() # max time bound
    
    # array master to hold rows
    rows = []   
    for i in range(num_rows):
        pid = random.choice(parent_ids)
        cat = random.choice(cat_keys)
        min_val, max_val = categories[cat][0], categories[cat][1]
        val = round(random.uniform(min_val, max_val), 2)
        
        # ensures parent child temporal integrity 
        base_date = parent_date_map[pid]
        base_datetime = datetime.combine(base_date, datetime.min.time())
        max_seconds = int((now_dt - base_datetime).total_seconds())
        offset = random.randint(0, max(0, max_seconds))
        event_timestamp = base_datetime + timedelta(seconds=offset)
        
        # data population
        record = {
            child_config["child_id_name"]: f"{child_config['child_id_prefix']}{100000 + i}",
            parent_id_col: pid,
            "timestamp": event_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            child_config["category_label"]: cat,
            child_config["metric_label"]: val
        }
        
        # safeguard
        for extra_col, extra_rules in child_config.get("extra_fields", {}).items():
            # categorical rule --> choices 
            if isinstance(extra_rules, dict) and "choices" in extra_rules:
                record[extra_col] = random.choice(extra_rules["choices"])
            else:
                # ternary check if 1. dict type & default found 2. dict type & default absent 3. not dict type
                record[extra_col] = extra_rules.get("default", "N/A") if isinstance(extra_rules, dict) else extra_rules
        
        # rows to master
        rows.append(record) 
        
    # return 
    df_child = pd.DataFrame(rows)
    return df_child.sort_values(by="timestamp").reset_index(drop=True)

# streamlit integration 

# mainframe configuration 
st.set_page_config(page_title="SynGenAI | Dataset Generator", layout="wide")
st.title("AI Based Synthetic Data Generator")
st.write("Type anything you want. The AI builds the custom relational architecture and the engine generates the rows.")

# sidebar configuration
with st.sidebar:
    st.header("🔑 Connection Status")
    if api_key:
        st.success("Connected via configuration file.")
        active_key = api_key
    else:
        st.error("API connection failure.")
        active_key = st.text_input("Manually enter Gemini Key here:", type="password")
        
    st.markdown("---")
    st.header("Dataset Sizing Rules")
    parent_count = st.slider("Primary Table Row Count", 10, 500, 100)
    child_count = st.slider("Relational Table Row Count", 20, 2000, 300)

# User Request Text Input Box
user_request = st.text_input(
    "What specific type of database do you want to generate?",
    placeholder="e.g. A hospital system with patients and custom laboratory blood tests"
)

if st.button("Build Custom Dataset Architecture"):
    if not active_key:
        st.warning("Please verify your API key configuration before running.")
    elif not user_request:
        st.warning("Please enter a text description specifying the dataset target concept.")
    else:
        with st.spinner("Architecting the specific database structures..."):
            blueprint = fetch_schema(user_request, active_key)
            
        if blueprint:
            st.success("✅ Custom schema engineered dynamically by AI!")
            
            with st.expander("🔍 View AI-Generated Schema Blueprint JSON"):
                st.json(blueprint)
                
            with st.spinner("Compiling structural database records from scratch..."):
                df_parent, date_ctx, date_col = parent_data(blueprint["parent_schema"], parent_count)
                
                # safeguard checks
                if date_ctx is None:
                    date_ctx = [fake.date_between(start_date="-2y", end_date="today") for _ in range(parent_count)]
                
                df_child = child_data(df_parent, date_ctx, blueprint["child_schema"], child_count)
                
            # render preview and download
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(f"Primary: {blueprint['parent_name']}")
                st.dataframe(df_parent.head(15))
                st.download_button(f"Download {blueprint['parent_name']}.csv", df_parent.to_csv(index=False), "parent.csv", "text/csv")
                
            with col2:
                st.subheader(f"Relational: {blueprint['child_name']}")
                st.dataframe(df_child.head(15))
                st.download_button(f"Download {blueprint['child_name']}.csv", df_child.to_csv(index=False), "child.csv", "text/csv")