import streamlit as st
import pandas as pd
import ssl
import certifi
import urllib3
import altair as alt
import requests
import io

# This line bypasses SSL verification.
ssl._create_default_https_context = ssl._create_unverified_context

# Configuration de la page (DOIT être la première commande st)
st.set_page_config(
    page_title="Ton Bilan",
    page_icon="🌙",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile optimization and better styling
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .stApp {
        max-width: 100%;
        padding: 0;
    }
    
    /* Adjust padding for mobile */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.5rem !important;
        }
        
        /* Make charts responsive */
        .vega-embed {
            width: 100% !important;
        }
        
        /* Smaller headers on mobile */
        h1 {
            font-size: 1.8rem !important;
        }
        h2 {
            font-size: 1.4rem !important;
        }
        h3 {
            font-size: 1.2rem !important;
        }
        
        /* Adjust tab styling for mobile */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.2rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 0.8rem;
            font-size: 0.9rem;
        }
    }
    
    /* Success/error message styling */
    .stSuccess, .stError, .stWarning, .stInfo {
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Input field styling */
    .stTextInput input {
        border-radius: 0.5rem;
        font-size: 1rem;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #4A90E2;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 2rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: #357ABD;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Card-like sections */
    .metric-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Custom divider */
    .custom-divider {
        height: 2px;
        background: linear-gradient(to right, #4A90E2, #E5E5E5);
        margin: 2rem 0;
        border-radius: 1px;
    }
</style>
""", unsafe_allow_html=True)

# Configuration - CSV link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRCbQDPet7-hUdVO0-CzfC3KrhHY6JbUO4UlMpUwbJJ_cp2LhqJSnX34jD-xqZcFAmI4FZZcEg9Wsuj/pub?output=csv"

# Column configurations
CLASSIFIER_COL = "Tu es :"
IDENTIFIER_COL = "Choisis ton code secret"

SCALE_QUESTIONS = [
    "A quel point ton sommeil est-il réparateur ?",
    "Quelle est la qualité de ton sommeil ?"
]

CATEGORY_QUESTIONS = [
    "As tu des écrans dans ta chambre (smartphone compris) ?",
    "Scénario – \"22 h 30\"",
    "Regardes-tu ton téléphone dès le réveil ?"
]

# Color schemes
COLOR_SCHEME_SCALE = ['#3366CC', '#DC3912', '#FF9900', '#109618']
COLOR_SCHEME_CATEGORY = ['#4285F4', '#EA4335', '#FBBC04', '#34A853']

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_data(url):
    """Charge les données depuis le lien CSV publié."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        csv_data = io.StringIO(response.text)
        df = pd.read_csv(csv_data)
        return df
    except Exception as e:
        st.error(f"Erreur de chargement des données : {e}")
        return pd.DataFrame()

# --- ENHANCED PLOTTING FUNCTIONS ---

def plot_numerical_comparison(df, question_col, classifier_col, user_value):
    """
    Crée un histogramme amélioré avec un design moderne et mobile-friendly.
    """
    # Prepare safe column names for Altair
    df_plot = df.copy()
    col_map = {col: (col.replace(':', '\\:') if isinstance(col, str) and ':' in col else col)
               for col in df_plot.columns}
    if any(col_map[c] != c for c in col_map):
        df_plot = df_plot.rename(columns=col_map)

    q_field = col_map.get(question_col, question_col)
    cls_field = col_map.get(classifier_col, classifier_col)

    # Calculate statistics for context
    user_percentile = (df_plot[col_map.get(question_col, question_col)] <= user_value).mean() * 100

    # Enhanced histogram with better styling
    base = alt.Chart(df_plot).mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4,
        opacity=0.8
    ).encode(
        x=alt.X(f"{q_field}:Q", 
                bin=alt.Bin(maxbins=10),
                title=question_col,
                axis=alt.Axis(
                    labelAngle=0,
                    titleFontSize=14,
                    labelFontSize=12,
                    grid=True,
                    gridOpacity=0.3
                )),
        y=alt.Y('count()', 
                title="Nombre de réponses",
                axis=alt.Axis(
                    titleFontSize=14,
                    labelFontSize=12,
                    grid=True,
                    gridOpacity=0.3
                )),
        color=alt.Color(f"{cls_field}:N", 
                       title="Type de répondant",
                       scale=alt.Scale(scheme='tableau10'),
                       legend=alt.Legend(
                           orient='bottom',
                           titleFontSize=12,
                           labelFontSize=11
                       )),
        tooltip=[
            alt.Tooltip(q_field, type='quantitative', title=question_col),
            alt.Tooltip(cls_field, type='nominal', title=classifier_col),
            alt.Tooltip('count()', title='Nombre')
        ]
    )

    # User's response line with enhanced visibility
    rule = alt.Chart(pd.DataFrame({'ma_reponse': [user_value]})).mark_rule(
        color='#E53E3E',
        strokeWidth=3,
        strokeDash=[5, 5]
    ).encode(
        x='ma_reponse:Q'
    )
    
    # Add text annotation for user's value
    text = alt.Chart(pd.DataFrame({
        'ma_reponse': [user_value],
        'y_pos': [df_plot.shape[0] * 0.1],
        'label': [f'Ta réponse: {user_value}']
    })).mark_text(
        align='center',
        baseline='bottom',
        dy=-5,
        fontSize=12,
        fontWeight='bold',
        color='#E53E3E'
    ).encode(
        x='ma_reponse:Q',
        y='y_pos:Q',
        text='label:N'
    )
    
    # Combine all elements
    chart = (base + rule + text).properties(
        width='container',
        height=300,
        title={
            "text": f"Distribution des réponses",
            "fontSize": 16,
            "anchor": "start"
        }
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        domainWidth=1
    )
    
    return chart, user_percentile

def plot_categorical_comparison(df, question_col, classifier_col, user_value):
    """
    Crée un graphique à barres amélioré pour les catégories.
    """
    # Prepare safe column names
    df_plot = df.copy()
    col_map = {col: (col.replace(':', '\\:') if isinstance(col, str) and ':' in col else col)
               for col in df_plot.columns}
    if any(col_map[c] != c for c in col_map):
        df_plot = df_plot.rename(columns=col_map)

    q_field = col_map.get(question_col, question_col)
    cls_field = col_map.get(classifier_col, classifier_col)

    # Calculate percentage for each category
    grouped = df_plot.groupby([q_field, cls_field]).size().reset_index(name='count')
    total = grouped.groupby(q_field)['count'].transform('sum')
    grouped['percentage'] = (grouped['count'] / total * 100).round(1)

    # Enhanced bar chart
    chart = alt.Chart(grouped).mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4
    ).encode(
        x=alt.X(f"{q_field}:N", 
                title=None,
                axis=alt.Axis(
                    labelAngle=-45 if len(grouped[q_field].unique()) > 3 else 0,
                    labelFontSize=12
                )),
        y=alt.Y('count:Q', 
                title="Nombre de réponses",
                stack='zero',
                axis=alt.Axis(
                    titleFontSize=14,
                    labelFontSize=12,
                    grid=True,
                    gridOpacity=0.3
                )),
        color=alt.Color(f"{cls_field}:N", 
                       title="Type de répondant",
                       scale=alt.Scale(scheme='category10'),
                       legend=alt.Legend(
                           orient='bottom',
                           titleFontSize=12,
                           labelFontSize=11
                       )),
        opacity=alt.condition(
            alt.datum[q_field] == user_value,
            alt.value(1.0),
            alt.value(0.4)
        ),
        tooltip=[
            alt.Tooltip(q_field, type='nominal', title=question_col),
            alt.Tooltip(cls_field, type='nominal', title=classifier_col),
            alt.Tooltip('count:Q', title='Nombre'),
            alt.Tooltip('percentage:Q', title='Pourcentage', format='.1f')
        ]
    )
    
    # Add percentage labels on bars
    text = alt.Chart(grouped).mark_text(
        dy=-5,
        fontSize=11,
        fontWeight='bold'
    ).encode(
        x=alt.X(f"{q_field}:N"),
        y=alt.Y('count:Q', stack='zero'),
        text=alt.Text('percentage:Q', format='.0f'),
        color=alt.value('white'),
        opacity=alt.condition(
            alt.datum[q_field] == user_value,
            alt.value(1.0),
            alt.value(0)
        )
    )
    
    final_chart = (chart + text).properties(
        width='container',
        height=350,
        title={
            "text": f"Répartition des réponses par groupe",
            "fontSize": 16,
            "anchor": "start"
        }
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        domainWidth=1
    )
    
    return final_chart

# --- MAIN APPLICATION ---

# Header with emoji and styling
st.markdown("# 🌙 Ton Bilan Sommeil")
st.markdown("### Découvre comment tu te situes par rapport aux autres participants")

# Load data
with st.spinner('Chargement des données...'):
    all_data = load_data(SHEET_URL)

if all_data.empty:
    st.stop()

# User identification section with improved styling
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown("## 🔐 Retrouve tes résultats")

col1, col2 = st.columns([3, 1])
with col1:
    user_id = st.text_input(
        "Entre ton code secret:",
        placeholder="Tape ton code ici...",
        help="C'est le code que tu as créé lors du questionnaire"
    )

if not user_id:
    st.info("💡 Entre ton code secret ci-dessus pour voir tes résultats personnalisés.")
    st.stop()

# Filter user data
try:
    user_data_row = all_data[all_data[IDENTIFIER_COL].str.lower().str.strip() == user_id.lower().strip()]
except AttributeError:
    user_data_row = all_data[all_data[IDENTIFIER_COL] == user_id]

if user_data_row.empty:
    st.error(f"❌ Code non trouvé: '{user_id}'. Vérifie l'orthographe et réessaie.")
    st.stop()

user_data = user_data_row.iloc[0]
user_classifier = user_data[CLASSIFIER_COL]

# Success message with custom styling
st.markdown(f"""
<div class="metric-card">
    <h3>✨ Bienvenue!</h3>
    <p>Nous avons trouvé tes réponses.</p>
    <p><strong>Tu fais partie du groupe:</strong> <span style="color: #4A90E2; font-size: 1.2em;">{user_classifier}</span></p>
</div>
""", unsafe_allow_html=True)

# Results section
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown("## 📊 Tes réponses en détail")

# Scale questions section
if SCALE_QUESTIONS:
    st.markdown("### 📈 Questions sur une échelle (1-10)")
    
    for i, q_col in enumerate(SCALE_QUESTIONS):
        with st.expander(f"📌 {q_col}", expanded=(i==0)):
            try:
                user_answer = user_data[q_col]
                if pd.isna(user_answer):
                    st.warning("Tu n'as pas répondu à cette question.")
                else:
                    chart, percentile = plot_numerical_comparison(
                        df=all_data,
                        question_col=q_col,
                        classifier_col=CLASSIFIER_COL,
                        user_value=user_answer
                    )
                    st.altair_chart(chart, use_container_width=True)
                    
                    # Add insight
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Ta réponse", f"{user_answer}/10")
                    with col2:
                        st.metric("Position", f"{percentile:.0f}e percentile")
                    
                    if percentile > 75:
                        st.success("👍 Tu es dans le quart supérieur!")
                    elif percentile < 25:
                        st.info("💭 Tu es dans le quart inférieur.")
                        
            except Exception as e:
                st.error(f"Erreur: {e}")

# Categorical questions section
if CATEGORY_QUESTIONS:
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📋 Questions à choix")
    
    for i, q_col in enumerate(CATEGORY_QUESTIONS):
        with st.expander(f"📌 {q_col}", expanded=(i==0)):
            try:
                user_answer = user_data[q_col]
                if pd.isna(user_answer):
                    st.warning("Tu n'as pas répondu à cette question.")
                else:
                    chart = plot_categorical_comparison(
                        df=all_data,
                        question_col=q_col,
                        classifier_col=CLASSIFIER_COL,
                        user_value=user_answer
                    )
                    st.altair_chart(chart, use_container_width=True)
                    
                    # Show user's answer prominently
                    st.info(f"🎯 **Ta réponse:** {user_answer}")
                    
                    # Calculate how many people gave the same answer
                    same_answer = all_data[all_data[q_col] == user_answer].shape[0]
                    total = all_data[q_col].notna().sum()
                    percentage = (same_answer / total * 100) if total > 0 else 0
                    
                    st.markdown(f"*{same_answer} personnes ({percentage:.0f}%) ont donné la même réponse*")
                    
            except Exception as e:
                st.error(f"Erreur: {e}")

# Summary statistics
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
with st.expander("📊 Statistiques globales"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Participants totaux", all_data.shape[0])
    with col2:
        st.metric("Groupes", all_data[CLASSIFIER_COL].nunique())
    with col3:
        st.metric("Questions", len(SCALE_QUESTIONS) + len(CATEGORY_QUESTIONS))

# Raw data (optional)
if st.checkbox("🔍 Voir les données brutes (anonymisées)"):
    st.dataframe(
        all_data.drop(columns=[IDENTIFIER_COL], errors='ignore'),
        use_container_width=True,
        height=400
    )

# Footer
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em; margin-top: 2rem;">
    <p>💡 Astuce: Cette page s'adapte automatiquement à ton écran!</p>
    <p>📱 Fonctionne parfaitement sur mobile</p>
</div>
""", unsafe_allow_html=True)