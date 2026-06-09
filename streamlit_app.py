# Verbeteringen:
# Engels/Nederlands


# Import python packages
import streamlit as st
from snowflake.snowpark.context import get_active_session
from datetime import datetime, date


# =====================================================
# SNOWFLAKE SESSION & CONFIG
# =====================================================

session = get_active_session()

session.use_database("CV")
session.use_schema("CONTENT")

st.set_page_config(page_title="CV Generator", layout="wide")

# Alleen gebruiken tijdens development
# LET OP:
# Verwijder deze regel in productie
# st.session_state.clear()


# =====================================================
# BASIS HUISSTIJL
# =====================================================

st.set_page_config(
    page_title="Data Talents",
    page_icon="📊",
    layout="wide"
)

def load_datatalents_theme():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Red Hat Display:wght@400;700&display=swap" rel="stylesheet">
    <style>
    /* Globale stijlen voor alle tekst */
    * {
        font-family: 'Red Hat Display', sans-serif !important;
        color: #1ECAD3 !important;
    }
    /* Specifieke gewichten toekennen */
    body {
        font-weight: 400; /* Regular */
    }
    h1, h2, h3, h4, h5, h6 {
        color: #1ECAD3 !important;
        font-weight: 700; /* Bold */
    }
    .stSelectbox, .stTextInput, .stMarkdown, .stButton>button {
        font-weight: 500; /* Medium */
    }
    /* Voor tabellen (bijv. Snowflake-resultaten) */
    .dataframe {
        font-family: 'Red Hat Display', sans-serif !important;
        font-weight: 400; /* Regular */
    }
    .dataframe {
        font-size: 12px !important;
    }
    /* Achtergrond */
    .stApp {
        background-color: #F4F4F4;
    }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: white;
        border-right: 4px solid #1ECAD3;
    }
    /* Buttons */
    .stButton button {
        background-color: #B6FBFF;
        border-radius: 8px;
        border: none;
    }
    .stButton button:hover {
        background-color: #B6FBFF;
        border: 3px solid #1ECAD3;
    }
    </style>
    """, unsafe_allow_html=True)

load_datatalents_theme()

with session.file.get_stream(
    "@datatalents_huisstijl/DATA_TALENTS_RGB.png"
) as f:
    st.image(f.read(), width=200)


# =====================================================
# APP TITLE
# =====================================================

st.title("CV Generator")

# =====================================================
# CONFIG DEFINITIONS
# =====================================================

GENERAL_FIELDS = [
    {"key": "Full_Name", "label": "Full name", "type": "text"},
    {"key": "Title", "label": "Title", "type": "text"},
    {"key": "Email", "label": "Email address",  "type": "text"},
    {"key": "Phone", "label": "Phone number", "type": "text"},
    {"key": "Residence", "label": "Residence", "type": "text"},
    {"key": "Birthdate", "label": "Date of birth", "type": "date"},
    {"key": "Role_Description", "label": "Role description", "type": "text"},
    {"key": "Profile_Description", "label": "Profile (max. 1.500 characters)", "type": "textarea"},
]

# =====================================================
# SESSION STATE
# =====================================================

if "General" not in st.session_state:
    st.session_state.General = {}

for f in GENERAL_FIELDS:
    if f["key"] != "Birthdate":
        st.session_state.General.setdefault(f["key"], "")
    else:
        if "Birthdate" not in st.session_state.General:
            st.session_state.General["Birthdate"] = None  # 1. Date of Birth is nu optioneel

st.session_state.General.setdefault("CV_Name", "")

if "Competences" not in st.session_state:
    st.session_state.Competences = [{
        "Competence_Category": None,
        "Competence_Description": [],
        "New_Competence": "",
        "New_Descriptions": ""
    }]

if "Summary_Experience" not in st.session_state:
    st.session_state.Summary_Experience = [{
        "Role_Summary": "",
        "Employer_Summary": "",
        "Period_Summary": ""
    }]

if "Education" not in st.session_state:
    st.session_state.Education = [{
        "Education": "",
        "Education_Institution": "",
        "Education_Year": ""
    }]

if "Training_Certification" not in st.session_state:
    st.session_state.Training_Certification = [{  # 3. Wijzig single object naar lijst
        "Training_Description": "",
        "Training_Institution": "",
        "Training_Year": ""
    }]

if "Experience" not in st.session_state:
    st.session_state.Experience = [{
        "Experience_Employer": "",
        "Experience_Role": "",
        "Experience_Period": "",
        "Activities": [""],
        "Methods": [""]
    }]

# =====================================================
# FUNCTIONS
# =====================================================

def sla_alles_op():
    st.success("Save placeholder (unchanged logic here)")

# 2. Functie om competence options dynamisch te genereren en sorteren
def get_competence_data():
    competence_rows = session.sql(
        """
        SELECT Competence_ID, Competence_Category, Competence_Description
        FROM Competence
        ORDER BY Competence_Category, Competence_Description
        """
    ).collect()

    competence_dict = {}
    db_competences = set()

    for row in competence_rows:
        c = row["COMPETENCE_CATEGORY"]
        d = row["COMPETENCE_DESCRIPTION"]
        competence_dict.setdefault(c, []).append(d)
        db_competences.add(c)

    # Voeg nieuwe competences uit session state toe
    for comp in st.session_state.Competences:
        new_comp = comp.get("New_Competence", "").strip()
        if new_comp:
            db_competences.add(new_comp)

    return sorted(list(db_competences)), competence_dict

# =====================================================
# 1. GENERAL (UI)
# =====================================================

st.header("1. General")

for field in GENERAL_FIELDS:
    k = field["key"]
    label = field["label"]
    t = field["type"]

    if t == "text":
        st.session_state.General[k] = st.text_input(
            label,
            value=st.session_state.General[k]
        )

    elif t == "textarea":
        st.session_state.General[k] = st.text_area(
            label,
            value=st.session_state.General[k],
            height=300
        )

    elif t == "date":
        st.session_state.General[k] = st.date_input(
            label,
            value=st.session_state.General[k],  # Kan None zijn
            min_value=date(1950, 1, 1),
            max_value=date.today(),
            format="DD-MM-YYYY"
        )

# =====================================================
# DATA PREP
# =====================================================

# Gebruik dynamische functie in plaats van statische lijst
competence_options, competence_dict = get_competence_data()


# COMPETENCES STATE

if "Competences" not in st.session_state:
    st.session_state.Competences = [{
        "Competence_Category": None,
        "Competence_Description": [],
        "New_Competence": "",
        "New_Descriptions": ""
    }]

if "competences_finished" not in st.session_state:
    st.session_state.competences_finished = False


# HELPERS

def add_competence():
    st.session_state.Competences.append({
        "Competence_Category": None,
        "Competence_Description": [],        
        "New_Competence": "",
        "New_Descriptions": ""
    })

def remove_competence():
    if len(st.session_state.Competences) > 1:
        st.session_state.Competences.pop()

def get_activity_options():
    rows = session.sql("""
        SELECT Activity_ID, Activity_Description
        FROM Activity
        ORDER BY Activity_Description
    """).collect()

    return {
        row["ACTIVITY_DESCRIPTION"]: row["ACTIVITY_ID"]
        for row in rows
    }

def get_method_options():
    rows = session.sql("""
        SELECT Method_ID, Method_Description
        FROM Method
        ORDER BY Method_Description
    """).collect()

    return {
        row["METHOD_DESCRIPTION"]: row["METHOD_ID"]
        for row in rows
    }
    

# =====================================================
# 2. Competences
# =====================================================

st.header("2. Competences")

disabled = st.session_state.competences_finished

for i, comp in enumerate(st.session_state.Competences):

    st.markdown(f"### Competence {i+1}")

    comp_key = f"comp_{i}"

    selected_competence = st.selectbox(
        "Competence Category",
        options=[""] + competence_options,
        key=comp_key,
        disabled=disabled
    )

    if selected_competence == "":
        selected_competence = None

    new_comp = st.text_input(
        "Or add new Competence Category",
        value=comp.get("New_Competence", ""),
        key=f"new_comp_{i}",
        disabled=disabled
    )

    final_comp = new_comp.strip() if new_comp.strip() else selected_competence

    comp["Competence_Category"] = final_comp
    comp["New_Competence"] = new_comp

    description_options = (
        competence_dict.get(selected_competence, [])
        if selected_competence else []
    )

    prev_key = f"prev_comp_{i}"

    if prev_key not in st.session_state:
        st.session_state[prev_key] = selected_competence

    if st.session_state[prev_key] != selected_competence:
        comp["Competence_Description"] = []
        st.session_state[f"desc_{i}"] = []
        st.session_state[prev_key] = selected_competence

    desc_key = f"desc_{i}"

    if desc_key not in st.session_state:
        st.session_state[desc_key] = comp.get("Competence_Description", [])

    selected_desc = st.multiselect(
        "Competence Description",
        options=description_options,
        key=desc_key,
        disabled=disabled
    )

    new_desc = st.text_input(
        "Add new Competence Description",
        value=comp.get("New_Descriptions", ""),
        key=f"new_desc_{i}",
        disabled=disabled
    )

    comp["Competence_Description"] = selected_desc
    comp["New_Descriptions"] = new_desc

    st.divider()


# GLOBAL ACTIONS

col1, col2, col3 = st.columns(3)

with col1:
    if st.button(
        "➕ Add Competence",
        disabled=disabled
    ):
        add_competence()

with col2:
    if st.button(
        "➖ Remove Competence",
        disabled=disabled
    ):
        remove_competence()

with col3:
    if st.button("✔ Finish Competences"):
        st.session_state.competences_finished = True

    
# =====================================================
# 3. SUMMARY EXPERIENCE
# =====================================================

if "summary_finished" not in st.session_state:
    st.session_state.summary_finished = False

st.header("3. Summary Experience")

disabled = st.session_state.summary_finished

for i, s in enumerate(st.session_state.Summary_Experience):
    col1, col2, col3 = st.columns(3)
    s["Role_Summary"] = col1.text_input("Role", s["Role_Summary"], key=f"r{i}", disabled=disabled)
    s["Employer_Summary"] = col2.text_input("Employer", s["Employer_Summary"], key=f"e{i}", disabled=disabled)
    s["Period_Summary"] = col3.text_input("Period", s["Period_Summary"], key=f"p{i}", disabled=disabled)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("➕ Add Summary", disabled=disabled):
        st.session_state.Summary_Experience.append({
            "Role_Summary": "",
            "Employer_Summary": "",
            "Period_Summary": ""
        })
with col2:
    if st.button("➖ Remove Summary", disabled=disabled):
        if len(st.session_state.Summary_Experience) > 1:
            st.session_state.Summary_Experience.pop()
with col3:
    if st.button("✔ Finish Summary"):
        st.session_state.summary_finished = True


# =====================================================
# 4. EDUCATION
# =====================================================

if "education_finished" not in st.session_state:
    st.session_state.education_finished = False

st.header("4. Education")

disabled = st.session_state.education_finished

for i, e in enumerate(st.session_state.Education):
    st.markdown(f"### Education {i+1}")
    e["Education"] = st.text_input("Education", e["Education"], key=f"edu{i}", disabled=disabled)
    e["Education_Institution"] = st.text_input("Institution", e["Education_Institution"], key=f"eduI{i}", disabled=disabled)
    e["Education_Year"] = st.text_input("Year", e["Education_Year"], key=f"eduY{i}", disabled=disabled)
    st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("➕ Add Education", disabled=disabled):
        st.session_state.Education.append({
            "Education": "",
            "Education_Institution": "",
            "Education_Year": ""
        })
with col2:
    if st.button("➖ Remove Education", disabled=disabled):
        if len(st.session_state.Education) > 1:
            st.session_state.Education.pop()
with col3:
    if st.button("✔ Finish Education"):
        st.session_state.education_finished = True


# =====================================================
# 5. TRAINING
# =====================================================

if "training_finished" not in st.session_state:
    st.session_state.training_finished = False

st.header("5. Training")

disabled = st.session_state.training_finished

for i, t in enumerate(st.session_state.Training_Certification):
    st.markdown(f"### Training {i+1}")
    t["Training_Description"] = st.text_input("Certificate", t["Training_Description"], key=f"train_desc_{i}", disabled=disabled)
    t["Training_Institution"] = st.text_input("Institution", t["Training_Institution"], key=f"train_inst_{i}", disabled=disabled)
    t["Training_Year"] = st.text_input("Year", t["Training_Year"], key=f"train_year_{i}", disabled=disabled)
    st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("➕ Add Training", disabled=disabled):
        st.session_state.Training_Certification.append({
            "Training_Description": "",
            "Training_Institution": "",
            "Training_Year": ""
        })
with col2:
    if st.button("➖ Remove Training", disabled=disabled):
        if len(st.session_state.Training_Certification) > 1:
            st.session_state.Training_Certification.pop()
with col3:
    if st.button("✔ Finish Training"):
        st.session_state.training_finished = True

# =====================================================
# 6. EXPERIENCE
# =====================================================

if "experience_finished" not in st.session_state:
    st.session_state.experience_finished = False

st.header("6. Experience")

disabled = st.session_state.experience_finished

for i, exp in enumerate(st.session_state.Experience):

    st.markdown(f"### Experience {i+1}")

    exp["Experience_Employer"] = st.text_input(
        "Employer",
        value=exp["Experience_Employer"],
        key=f"exp_emp_{i}",
        disabled=disabled
    )

    exp["Experience_Role"] = st.text_input(
        "Role",
        value=exp["Experience_Role"],
        key=f"exp_role_{i}",
        disabled=disabled
    )

    exp["Experience_Period"] = st.text_input(
        "Period",
        value=exp["Experience_Period"],
        key=f"exp_period_{i}",
        disabled=disabled
    )

    # ==========================================
    # ACTIVITIES
    # ==========================================

    st.markdown("#### Activities")

    for j in range(len(exp["Activities"])):

        exp["Activities"][j] = st.text_input(
            f"Activity {j+1}",
            value=exp["Activities"][j],
            key=f"exp_{i}_activity_{j}",
            disabled=disabled
        )

    col_a1, col_a2 = st.columns(2)

    with col_a1:
        if st.button(
            f"➕ Add Activity",
            key=f"add_activity_{i}",
            disabled=disabled
        ):
            exp["Activities"].append("")
            st.rerun()

    with col_a2:
        if st.button(
            f"➖ Remove Activity",
            key=f"remove_activity_{i}",
            disabled=disabled
        ):
            if len(exp["Activities"]) > 1:
                exp["Activities"].pop()
                st.rerun()

    # ==========================================
    # METHODS
    # ==========================================

    st.markdown("#### Methods")

    for j in range(len(exp["Methods"])):

        exp["Methods"][j] = st.text_input(
            f"Method {j+1}",
            value=exp["Methods"][j],
            key=f"exp_{i}_method_{j}",
            disabled=disabled
        )

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        if st.button(
            f"➕ Add Method",
            key=f"add_method_{i}",
            disabled=disabled
        ):
            exp["Methods"].append("")
            st.rerun()

    with col_m2:
        if st.button(
            f"➖ Remove Method",
            key=f"remove_method_{i}",
            disabled=disabled
        ):
            if len(exp["Methods"]) > 1:
                exp["Methods"].pop()
                st.rerun()

    st.divider()

# =====================================================
# EXPERIENCE ACTIONS
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:
    if st.button(
        "➕ Add Experience",
        disabled=disabled
    ):
        st.session_state.Experience.append({
            "Experience_Employer": "",
            "Experience_Role": "",
            "Experience_Period": "",
            "Activities": [""],
            "Methods": [""]
        })
        st.rerun()

with col2:
    if st.button(
        "➖ Remove Experience",
        disabled=disabled
    ):
        if len(st.session_state.Experience) > 1:
            st.session_state.Experience.pop()
            st.rerun()

with col3:
    if st.button("✔ Finish Experience"):
        st.session_state.experience_finished = True
# =====================================================
# SAVE
# =====================================================

st.header("Save")

st.session_state.General["CV_Name"] = st.text_input(
    "CV Name",
    value=st.session_state.General["CV_Name"]
)

if st.button("Save All"):
    sla_alles_op()
