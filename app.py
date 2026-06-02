import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from tranche_master import SEEDS

st.set_page_config(page_title="The Fluttering Sail Engine", layout="wide")

st.title("⛵ The Fluttering Sail: 8D Epistemic Parser")
st.markdown("---")

# Left Sidebar controls
st.sidebar.header("Engine Configuration")
text_input_method = st.sidebar.radio("Input Source", ["Custom Text Entry", "Preloaded Core Corpora Sample"])

# Sample corporate text vs philosophical baseline text
SAMPLES = {
    "Corporate Resource Yield Strategy": "We must execute a strategy to leverage systemic throughput and optimize asset scale. Exploiting these process efficiencies will yield immediate margin improvements.",
    "Civic and Universal Integration Manifesto": "Our alignment with natural rhythm and duty preserves communal wholeness. True justice requires fraternity and a shared sacrifice to secure liberty for every single citizen."
}

if text_input_method == "Custom Text Entry":
    user_text = st.sidebar.text_area("Paste Corpus Segment here:", value=SAMPLES["Corporate Resource Yield Strategy"])
else:
    selected_sample = st.sidebar.selectbox("Choose a preloaded document:", list(SAMPLES.keys()))
    user_text = SAMPLES[selected_sample]

# Core Text Analysis
def evaluate_text(text):
    clean_text = re.sub(r'[^\w\s]', '', text.lower())
    tokens = clean_text.split()
    
    cumulative_vector = np.zeros(8)
    matched_tokens = []
    
    for token in tokens:
        if token in SEEDS:
            matched_tokens.append(token)
            cumulative_vector += np.array(SEEDS[token])
            
    if len(matched_tokens) == 0:
        return None, []
        
    avg_vector = cumulative_vector / len(matched_tokens)
    return avg_vector, matched_tokens

# Run Analysis Pipeline
avg_vec, matches = evaluate_text(user_text)

# Layout Setup
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Corpus Under Evaluation")
    st.info(f'"{user_text}"')
    
    if matches:
        st.success(f"**Detected Anchor Tokens:** {', '.join(set(matches))}")
        
        # Display 8D Vector metrics table
        dimensions = ["Utility (U)", "Fairness (F)", "Power (P)", "Mimetic (M)", "Telos (T)", "Structure (S)", "Dharma (D)", "Consciousness (C)"]
        df_metrics = pd.DataFrame({"Dimension": dimensions, "Calculated Coordinate": avg_vec})
        st.dataframe(df_metrics, hide_index=True, use_container_width=True)
    else:
        st.warning("No anchor tokens discovered. The text occupies a completely Neutral Void.")

with col2:
    st.subheader("📊 The Vector Tension Canvas")
    
    if avg_vec is not None:
        # Dimensional Reduction Mapping Formulas (Section 3.3.1)
        m_axis = 0.5 * np.sqrt(avg_vec[0]**2 + avg_vec[1]**2 + avg_vec[2]**2 + avg_vec[3]**2)
        d_axis = 0.5 * np.sqrt(avg_vec[4]**2 + avg_vec[5]**2 + avg_vec[6]**2 + avg_vec[7]**2)
        
        shear_tension = abs(m_axis - d_axis)
        
        # Classification Engine
        if m_axis >= 0.55 and d_axis <= 0.25:
            zone = "Baconian Collapse (Extractive Extraction Grid)"
            color = "red"
        elif m_axis <= 0.25 and d_axis >= 0.55:
            zone = "Ascetic Drift (Divorced Pure Philosophy)"
            color = "blue"
        elif m_axis >= 0.40 and d_axis >= 0.40 and shear_tension <= 0.20:
            zone = "Equilibrium Zone (Harmonious Dynamic)"
            color = "green"
        else:
            zone = "Transition Gradient"
            color = "orange"
            
        st.metric(label="Current Metaphysical Zone", value=zone)
        st.metric(label="Shear Tension Metric ($T_{shear}$)", value=f"{shear_tension:.3f}")
        
        # Matplotlib Canvas Plot Construction
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(0, 1.0)
        ax.set_ylim(0, 1.0)
        ax.set_xlabel("Materialist Axis (M)")
        ax.set_ylabel("Dharmic Axis (D)")
        
        # Quadrant background coloring indicators
        ax.axhspan(0, 0.4, 0.6, 1.0, color='red', alpha=0.05, label="Baconian Collapse Zone")
        ax.axhspan(0.6, 1.0, 0, 0.4, color='blue', alpha=0.05, label="Ascetic Drift Zone")
        
        # Grid layout markers
        ax.axhline(0.5, color='gray', linestyle='--', alpha=0.3)
        ax.axvline(0.5, color='gray', linestyle='--', alpha=0.3)
        
        # Current vector location marker plotting
        ax.scatter(m_axis, d_axis, color=color, s=200, edgecolors='black', zorder=5, label="Analyzed Document Position")
        ax.text(m_axis + 0.03, d_axis + 0.03, "Document Target", fontsize=12, fontweight='bold')
        
        ax.grid(True, alpha=0.2)
        st.pyplot(fig)
