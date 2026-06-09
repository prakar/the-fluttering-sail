"""
home.py — The Fluttering Sail
==============================
Orientation page for first-time visitors.
Rendered when session_state['onboarded'] == 'tour'.
Called from app.py render_home().

All content is intentionally separate from app logic.
Edit this file to update the home page without touching the framework.
"""

import streamlit as st


def render_splash() -> None:
    """
    Full-viewport splash screen — shown once on first visit.
    Two routing buttons: straight to framework, or orientation tour.
    No sidebar. No navigation chrome.
    """
    # Hide sidebar entirely on splash
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    .block-container { padding-top: 0 !important; max-width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

    # Faint eight-axis radar SVG — the brand shape, not a data chart
    radar_svg = """
    <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg"
         style="position:fixed;top:40%;left:50%;transform:translate(-50%,-50%);
                width:min(500px,80vw);height:min(500px,80vw);opacity:0.055;
                pointer-events:none;z-index:0">
      <g transform="translate(200,200)">
        <!-- Concentric rings -->
        <circle r="160" fill="none" stroke="#4a90d9" stroke-width="0.8"/>
        <circle r="120" fill="none" stroke="#4a90d9" stroke-width="0.6"/>
        <circle r="80"  fill="none" stroke="#4a90d9" stroke-width="0.5"/>
        <circle r="40"  fill="none" stroke="#4a90d9" stroke-width="0.4"/>
        <!-- Eight axes at 45-degree intervals -->
        <line x1="0" y1="-160" x2="0"    y2="160"  stroke="#4a90d9" stroke-width="0.7"/>
        <line x1="-160" y1="0" x2="160"  y2="0"    stroke="#4a90d9" stroke-width="0.7"/>
        <line x1="-113" y1="-113" x2="113" y2="113" stroke="#4a90d9" stroke-width="0.5"/>
        <line x1="113"  y1="-113" x2="-113" y2="113" stroke="#4a90d9" stroke-width="0.5"/>
        <!-- Sail shape — a plausible 8D vector, aesthetically balanced -->
        <polygon points="0,-95 67,-67 110,0 67,67 0,55 -80,80 -95,0 -67,-90"
                 fill="#4a90d9" fill-opacity="0.18" stroke="#4a90d9" stroke-width="1.2"/>
      </g>
    </svg>
    """
    st.markdown(radar_svg, unsafe_allow_html=True)

    # Splash content — compact layout, everything above fold
    st.markdown("""
    <div style="
        position:relative;z-index:1;
        padding:48px 24px 32px;text-align:center;">

      <!-- Eyebrow -->
      <div style="
          font-size:11px;font-weight:700;letter-spacing:0.22em;
          text-transform:uppercase;color:#4a90d9;margin-bottom:16px">
        Computational Ethics Framework
      </div>

      <!-- Name -->
      <div style="
          font-size:clamp(32px,5vw,58px);font-weight:800;
          letter-spacing:-0.02em;color:#e8f0f8;line-height:1.1;
          margin-bottom:10px">
        The Fluttering Sail
      </div>

      <!-- Subtitle -->
      <div style="
          font-size:clamp(13px,1.8vw,17px);color:#7ab3e0;
          font-style:italic;margin-bottom:20px;max-width:600px;
          margin-left:auto;margin-right:auto">
        An 8-Dimensional Quantised Ethics Framework bridging<br>
        Western Materialist and Indic Essentialist philosophical traditions
      </div>

      <!-- One-sentence hook -->
      <div style="
          font-size:clamp(14px,1.6vw,16px);color:#aac;line-height:1.7;
          max-width:480px;margin:0 auto 36px auto">
        Paste any text — a speech, a mission statement, a policy document —
        and see its ethical fingerprint mapped across eight philosophical traditions in real time.
      </div>

    </div>
    """, unsafe_allow_html=True)

    # Routing buttons — Streamlit native (no HTML buttons)
    col_l, col_a, col_b, col_r = st.columns([2, 3, 3, 2])
    with col_a:
        if st.button("⛵  I know what this is — take me straight in",
                     type="primary", key="splash_direct", use_container_width=True):
            st.session_state['onboarded'] = 'direct'
            st.rerun()
    with col_b:
        if st.button("📖  Show me around first",
                     type="secondary", key="splash_tour", use_container_width=True):
            st.session_state['onboarded'] = 'tour'
            st.rerun()

    # Footer line
    st.markdown("""
    <div style="text-align:center;margin-top:48px;font-size:11px;color:#555">
      <a href="https://the-fluttering-sail.onrender.com" style="color:#4a90d9;text-decoration:none">
        the-fluttering-sail.onrender.com
      </a>
      &nbsp;·&nbsp;
      <a href="https://github.com/prakar/the-fluttering-sail"
         style="color:#4a90d9;text-decoration:none">
        github.com/prakar/the-fluttering-sail
      </a>
      &nbsp;·&nbsp;
      <span style="color:#555">Karmarkar, P.V. (2026) · Ethics and Information Technology (Springer)</span>
    </div>
    """, unsafe_allow_html=True)


def render_home() -> None:
    """
    Orientation page — for users who chose 'Show me around first'.
    Two-row layout: hero strip, then asymmetric three-column content zone.
    Back to splash link in sidebar.
    """
    st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # Unobtrusive back link in sidebar
    with st.sidebar:
        st.markdown("&nbsp;")
        if st.button("← Back to intro", key="back_to_splash"):
            del st.session_state['onboarded']
            st.rerun()
        st.markdown("---")
        if st.button("⛵  Go straight to analysis", type="primary",
                     key="home_to_direct"):
            st.session_state['onboarded'] = 'direct'
            st.session_state['_page_override'] = 'Main Analysis'
            st.rerun()

    # ── HERO STRIP ────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#0d1b2e 0%,#0e0e1a 60%,#1a0e2e 100%);
        border-radius:12px;padding:40px 48px;margin-bottom:32px;
        border:1px solid #1e2a3a">
      <div style="font-size:11px;font-weight:700;letter-spacing:0.2em;
           text-transform:uppercase;color:#4a90d9;margin-bottom:12px">
        The Fluttering Sail
      </div>
      <div style="font-size:26px;font-weight:700;color:#e8f0f8;
           line-height:1.3;margin-bottom:16px;max-width:700px">
        Ethics is not a verdict. It's a direction.
      </div>
      <div style="font-size:15px;color:#8899bb;line-height:1.8;max-width:680px">
        This framework maps any text to a position in an 8-dimensional philosophical
        space — four axes from Western analytic ethics, four from Indic philosophical
        traditions. The result is not a score. It's a <em>topological portrait</em>:
        what a text aligns with, what it opposes, and how close it is to five named
        ethical signatures.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── THREE COLUMNS ─────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([4, 3, 3], gap="large")

    # ── COLUMN 1: What this is and why ────────────────────────────────────
    with col1:
        st.markdown("""
        <div style="font-size:11px;font-weight:700;letter-spacing:0.15em;
             text-transform:uppercase;color:#4a90d9;margin-bottom:12px">
          What this is
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
Most ethical frameworks are monolithic — they evaluate from a single tradition and
cannot hold two civilisational perspectives simultaneously. A text can be maximally
fair by Rawlsian standards and ontologically incoherent by Dharmic ones, with no tool
to show both at once.

This framework treats ethical evaluation as a **geometric problem**: a moral position
is a vector in ℝ⁸. The eight dimensions span both traditions as co-equal axes — not
one tradition glossing the other.

**The eight dimensions:**
        """)

        dims = [
            ("u", "Utility",     "#e74c3c", "Does this text maximise real-world welfare?"),
            ("f", "Fairness",    "#e67e22", "Does it treat people with equal procedural dignity?"),
            ("p", "Power",       "#c0392b", "Does it think strategically about force and leverage?"),
            ("m", "Mimetic",     "#922b21", "Does it engage with rivalry and social conflict?"),
            ("t", "Telos",       "#2980b9", "Does it have a sense of purpose and direction?"),
            ("s", "Structure",   "#1a5276", "Does it operate from duty and principled constraint?"),
            ("d", "Dharma",      "#6c3483", "Does it align with cosmic or natural order?"),
            ("c", "Non-Dual",    "#4a235a", "Does it see unity rather than separation?"),
        ]
        for code, name, colour, desc in dims:
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:10px;
                 margin-bottom:8px">
              <div style="background:{colour};color:#fff;font-size:11px;
                   font-weight:700;padding:2px 7px;border-radius:3px;
                   min-width:20px;text-align:center;margin-top:2px">{code}</div>
              <div>
                <span style="color:#e8f0f8;font-size:13px;font-weight:600">{name}</span>
                <span style="color:#778;font-size:12px"> — {desc}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:20px;padding:14px 16px;background:#0d1b2e;
             border-radius:8px;border-left:3px solid #c8a96e">
          <div style="font-size:12px;color:#c8a96e;font-weight:600;
               margin-bottom:4px">On the Sanskrit lexicon</div>
          <div style="font-size:13px;color:#8899bb;line-height:1.6">
            63 Sanskrit philosophical non-translatables — dharma, moksha, viveka,
            ahankara and more — are positioned as vectors in this same space.
            Not translated. <em>Quantised.</em> Explore them in the
            Sanskrit Non-Translatables page.
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── COLUMN 2: User manual ──────────────────────────────────────────────
    with col2:
        st.markdown("""
        <div style="font-size:11px;font-weight:700;letter-spacing:0.15em;
             text-transform:uppercase;color:#4a90d9;margin-bottom:12px">
          How to use it
        </div>
        """, unsafe_allow_html=True)

        steps = [
            ("📄", "Choose a text",
             "Select one of the ten Canonical Texts — spanning Aristotle, the Indian Constitution, "
             "Newton, Marx, and more — or paste your own passage in Custom Text."),
            ("🎯", "Read the dual radar",
             "Two sail-shaped plots appear: the Materialist Lens (left) and the Dharmic-Essentialist "
             "Lens (right). The solid shape shows what the text aligns with. The dotted shape shows "
             "what it actively opposes."),
            ("🌪️", "Synthesize the lenses",
             "Click Synthesize to overlay both radars into one view and generate a philosophical "
             "narration — a single dense paragraph describing the text's ethical fingerprint."),
            ("🔬", "Read the proximity meters",
             "Five VU-style bars show how close the text is to each named ethical condition — "
             "Baconian Collapse, Mimetic Shear, Ascetic Drift, Purushartha Equilibrium, and "
             "Nyaya Meta-Condition. Click ? next to any bar to understand what it means."),
            ("📊", "Check lexicon coverage",
             "The coverage report below the analysis shows what percentage of your text's "
             "vocabulary the framework recognises — and lists the unrecognised words, with "
             "instructions for adding them."),
            ("🔧", "Extend it",
             "This framework is designed to be forked. The vocabulary, thresholds, dimensions, "
             "and diagnostic conditions are all in editable JSON files. No philosophy PhD required."),
        ]

        for icon, title, desc in steps:
            st.markdown(f"""
            <div style="display:flex;gap:12px;margin-bottom:18px;
                 align-items:flex-start">
              <div style="font-size:20px;min-width:28px">{icon}</div>
              <div>
                <div style="color:#e8f0f8;font-size:13px;font-weight:600;
                     margin-bottom:3px">{title}</div>
                <div style="color:#778;font-size:12px;line-height:1.6">{desc}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── COLUMN 3: Who this is for ──────────────────────────────────────────
    with col3:
        st.markdown("""
        <div style="font-size:11px;font-weight:700;letter-spacing:0.15em;
             text-transform:uppercase;color:#4a90d9;margin-bottom:12px">
          Who this is for
        </div>
        """, unsafe_allow_html=True)

        audiences = [
            ("🎓", "Educators and policy writers",
             "Test whether a curriculum, policy document, or public communication "
             "is as balanced as it claims to be."),
            ("✍️", "Marketers and content creators",
             "Check whether your content's philosophical posture matches your "
             "brand's stated values — before you publish."),
            ("⚡", "Strategists and campaign writers",
             "Understand the ethical signature of persuasive content. Know "
             "whether you're writing for mobilisation, balance, or transcendence "
             "— and whether that's intentional."),
            ("🕉️", "Sanskrit and Indic philosophy scholars",
             "The first computational lexicon of Sanskrit non-translatables "
             "as philosophical vectors. Explore dharma, moksha, viveka, and "
             "60 more terms in the dedicated Sanskrit view."),
            ("🔬", "Ethics and AI researchers",
             "A forkable, open-source framework for cross-civilisational "
             "computational ethics. Extend the dimensions, add traditions, "
             "publish variant lexicons as citable forks."),
            ("🌐", "Anyone",
             "Paste anything. A tweet, a manifesto, a company mission statement. "
             "No prior knowledge required — the ? buttons explain everything."),
        ]

        for icon, title, desc in audiences:
            st.markdown(f"""
            <div style="padding:12px 14px;background:#0d1420;border-radius:8px;
                 margin-bottom:10px;border:1px solid #1a2535">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                <span style="font-size:16px">{icon}</span>
                <span style="color:#e8f0f8;font-size:13px;font-weight:600">{title}</span>
              </div>
              <div style="color:#778;font-size:12px;line-height:1.6;
                   padding-left:24px">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── CTA ───────────────────────────────────────────────────────────────
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    _, cta_col, _ = st.columns([3, 4, 3])
    with cta_col:
        if st.button("⛵  Start analysing — open the framework",
                     type="primary", key="home_cta",
                     use_container_width=True):
            st.session_state['onboarded'] = 'direct'
            st.session_state['_page_override'] = 'Main Analysis'
            st.rerun()

    # Paper citation
    st.markdown("""
    <div style="text-align:center;margin-top:24px;font-size:11px;color:#444;
         padding-bottom:40px">
      Karmarkar, P.V. (2026). An 8-Dimensional Quantised Computational Ethics Framework
      Bridging Western Materialist and Indic Essentialist Philosophical Traditions.
      <em>Ethics and Information Technology</em> (Springer, under review).
    </div>
    """, unsafe_allow_html=True)