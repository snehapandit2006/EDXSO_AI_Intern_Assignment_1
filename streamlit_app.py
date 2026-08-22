import json
import streamlit as st
import pandas as pd
from pathlib import Path

from app.config import (
    CAMPAIGN_TITLE, TARGET_NICHE, TARGET_PLATFORM, MIN_FOLLOWERS, MAX_FOLLOWERS,
    QUALIFIED_THRESHOLD, REVIEW_THRESHOLD, RAW_DATA_DIR, PROCESSED_DATA_DIR, EXPORTS_DATA_DIR, SEND_MODE
)
from app.database.models import init_db, SessionLocal, Campaign, Creator, FilterResult, Message, OutreachLog
from app.database.repository import (
    get_or_create_campaign, upsert_creator, save_filter_result, save_message, save_outreach_log, get_all_creators
)
from app.discovery import run_discovery
from app.enrichment import run_enrichment
from app.filtering import run_filtering
from app.personalization import run_personalization
from app.outreach.tracker import process_outreach_for_qualified
from app.outreach.sender import prepare_dm_workflow

# Page Configuration
st.set_page_config(
    page_title="EDXSO | AI Influencer Outreach System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Glassmorphism UI)
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #6366F1, #8B5CF6, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #9CA3AF;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: rgba(31, 41, 55, 0.7);
        border: 1px solid rgba(75, 85, 99, 0.4);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        backdrop-filter: blur(8px);
    }
    .metric-val {
        font-size: 2.0rem;
        font-weight: 700;
        color: #F3F4F6;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-qualified {
        background-color: #059669;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-review {
        background-color: #D97706;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-rejected {
        background-color: #DC2626;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


def load_db_session():
    init_db()
    return SessionLocal()


def format_followers(val) -> str:
    """Safely format follower counts handling int, float, string 'Not Found', or None."""
    if isinstance(val, int):
        return f"{val:,}"
    elif isinstance(val, float):
        return f"{int(val):,}"
    elif val is not None and str(val).isdigit():
        return f"{int(val):,}"
    return str(val or "Not Found")


def format_engagement(val) -> str:
    """Safely format engagement rate handling numeric floats, strings, or None."""
    if isinstance(val, (int, float)):
        return f"{val:.2f}%"
    elif val is not None and val not in ["Not Found", "None", ""]:
        try:
            return f"{float(val):.2f}%"
        except (ValueError, TypeError):
            pass
    return str(val or "Not Found")


def main():
    st.markdown('<div class="main-header">EDXSO AI Micro-Influencer Discovery & Outreach Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Production-Ready Autonomous Outreach Engine for Tech & AI Creator Campaigns</div>', unsafe_allow_html=True)

    db = load_db_session()
    campaign = get_or_create_campaign(db)

    # Sidebar Navigation & Controls
    with st.sidebar:
        st.header("⚙️ Control Center")
        st.info(f"**Active Campaign:**\n{campaign.title}")
        st.write(f"**Target Platform:** {campaign.platform}")
        min_f_str = format_followers(campaign.min_followers)
        max_f_str = format_followers(campaign.max_followers)
        st.write(f"**Follower Range:** {min_f_str} – {max_f_str}")

        st.divider()
        st.subheader("⚡ Automated Actions")
        if st.button("▶️ Run Full Pipeline", type="primary", use_container_width=True):
            with st.spinner("Running full E2E pipeline (Discovery -> Outreach)..."):
                raw = run_discovery()
                enriched = run_enrichment(raw)
                for c in enriched:
                    c_obj = upsert_creator(db, campaign.id, c)
                    c["db_creator_id"] = c_obj.id

                filtering_res = run_filtering(enriched)
                for cat in ["QUALIFIED", "REVIEW", "REJECTED"]:
                    for item in filtering_res[cat]:
                        save_filter_result(db, campaign.id, item["db_creator_id"], item)

                qualified = filtering_res["QUALIFIED"]
                personalized = run_personalization(qualified, campaign_title=campaign.title)
                for item in personalized:
                    m_obj = save_message(db, campaign.id, item["db_creator_id"], item["message"])
                    item["db_message_id"] = m_obj.id

                process_outreach_for_qualified(db, campaign.id, personalized, send_mode=SEND_MODE)
                st.success("Pipeline executed successfully!")
                st.rerun()

        if st.button("🔄 Reset / Clear DB Data", use_container_width=True):
            db.query(OutreachLog).delete()
            db.query(Message).delete()
            db.query(FilterResult).delete()
            db.query(Creator).delete()
            db.commit()
            st.success("Database cleared!")
            st.rerun()

    # Create Main Tabs
    tabs = st.tabs([
        "🎯 Campaign Setup",
        "🔍 Creator Discovery",
        "📊 Filtering & Classification",
        "👤 Enriched Profiles",
        "🤖 AI Personalization",
        "✉️ Outreach Sending Layer",
        "📈 Tracker & Matrix"
    ])

    # Tab 1: Campaign Setup
    with tabs[0]:
        st.subheader("🎯 Active Campaign Configuration")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.text_input("Campaign Title", value=campaign.title, disabled=True)
            st.text_input("Target Niche", value=campaign.target_niche, disabled=True)
        with c2:
            st.text_input("Platform", value=campaign.platform, disabled=True)
            st.text_input("Collaboration Type", value=campaign.collaboration_type, disabled=True)
        with c3:
            st.number_input("Min Followers", value=campaign.min_followers, disabled=True)
            st.number_input("Max Followers", value=campaign.max_followers, disabled=True)

        st.divider()
        st.subheader("📊 System Summary Metrics")
        creators_in_db = db.query(Creator).filter_by(campaign_id=campaign.id).all()
        q_count = db.query(FilterResult).filter_by(campaign_id=campaign.id, classification="QUALIFIED").count()
        r_count = db.query(FilterResult).filter_by(campaign_id=campaign.id, classification="REVIEW").count()
        rej_count = db.query(FilterResult).filter_by(campaign_id=campaign.id, classification="REJECTED").count()
        sent_count = db.query(OutreachLog).filter_by(campaign_id=campaign.id, sent=True).count()

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Discovered Creators", len(creators_in_db))
        m2.metric("QUALIFIED", q_count)
        m3.metric("REVIEW", r_count)
        m4.metric("REJECTED", rej_count)
        m5.metric("Outreach Sent", sent_count)

    # Tab 2: Creator Discovery
    with tabs[1]:
        st.subheader("🔍 Live Multi-Source Discovery Engine & Provenance Pipeline")
        st.markdown("**Live Discovery Sources:** Source A (GitHub Public Directories) → Source B (Dev.to Spotlight Index) → Source C (Tech Hashtag Feed) → Source D (Open Tech Creator Index)")
        st.caption("Target: 100 raw records | Minimum Acceptance Gate: 50 valid unique records")

        if st.button("🔍 Run Discovery Adapter Chain"):
            with st.spinner("Fetching creators across live API adapters..."):
                raw_list = run_discovery()
                enriched_list = run_enrichment(raw_list)
                for c in enriched_list:
                    upsert_creator(db, campaign.id, c)
                st.success(f"Discovered and persisted {len(raw_list)} creators!")
                st.rerun()

        raw_path = RAW_DATA_DIR / "discovered_creators_raw.json"
        if raw_path.exists():
            with open(raw_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            st.write(f"**Discovered Raw Records ({len(raw_data)}):**")
            df_raw = pd.DataFrame(raw_data)
            if "engagement_rate" in df_raw.columns:
                df_raw["engagement_rate"] = df_raw["engagement_rate"].apply(format_engagement)
            if "followers" in df_raw.columns:
                df_raw["followers"] = df_raw["followers"].apply(format_followers)
            display_cols = [c for c in ["name", "username", "followers", "engagement_rate", "source", "source_url", "extraction_method", "discovered_at"] if c in df_raw.columns]
            st.dataframe(df_raw[display_cols], use_container_width=True)

    # Tab 3: Filtering & Classification
    with tabs[2]:
        st.subheader("📊 Deterministic Qualification & Soft Scoring Engine")
        st.markdown("**Strict Gates:** Platform = Tech Creator | 5k–100k Followers | Mandatory Email | Mandatory Engagement")

        if st.button("⚡ Run Filtering & Explainability Classifier"):
            creators = get_all_creators(db, campaign.id)
            creator_dicts = [
                {
                    "db_creator_id": c.id,
                    "name": c.name,
                    "username": c.username,
                    "platform": c.platform,
                    "followers": c.followers,
                    "engagement_rate": c.engagement_rate,
                    "contact_email": c.contact_email,
                    "category": c.category,
                    "sub_niche": c.sub_niche,
                    "bio": c.bio,
                    "content_themes": c.get_content_themes(),
                    "recent_content": c.get_recent_content(),
                    "creator_geography": c.creator_geography,
                    "audience_age": c.audience_age,
                    "audience_gender": c.audience_gender,
                    "audience_geography": c.audience_geography
                }
                for c in creators
            ]
            filter_res = run_filtering(creator_dicts)
            for cat in ["QUALIFIED", "REVIEW", "REJECTED"]:
                for item in filter_res[cat]:
                    save_filter_result(db, campaign.id, item["db_creator_id"], item)
            st.success("Filtering complete!")
            st.rerun()

        filter_records = db.query(FilterResult, Creator).join(Creator, FilterResult.creator_id == Creator.id).filter(FilterResult.campaign_id == campaign.id).all()
        if filter_records:
            data = []
            for fr, c in filter_records:
                data.append({
                    "Name": c.name,
                    "Username": f"@{c.username}",
                    "Followers": format_followers(c.followers),
                    "Email": c.contact_email,
                    "Eng %": format_engagement(c.engagement_rate),
                    "Total Score": fr.total_score,
                    "Classification": fr.classification,
                    "Justification / Filter Reason": fr.filter_reason
                })
            df_filter = pd.DataFrame(data)
            st.dataframe(df_filter, use_container_width=True)

    # Tab 4: Enriched Profiles
    with tabs[3]:
        st.subheader("👤 Enriched Creator Profile Directory")
        creators = get_all_creators(db, campaign.id)
        if creators:
            search_query = st.text_input("🔍 Search creators by name, username, or sub-niche:", "")
            filtered_c = [c for c in creators if search_query.lower() in c.name.lower() or search_query.lower() in c.username.lower() or search_query.lower() in c.sub_niche.lower()]

            cols = st.columns(2)
            for idx, c in enumerate(filtered_c):
                f_str = format_followers(c.followers)
                eng_str = format_engagement(c.engagement_rate)
                with cols[idx % 2]:
                    with st.expander(f"📌 {c.name} (@{c.username}) — {f_str} Followers"):
                        st.write(f"**Bio:** {c.bio}")
                        st.write(f"**Sub-Niche:** {c.sub_niche}")
                        st.write(f"**Engagement Rate:** {eng_str}")
                        st.write(f"**Contact Email:** `{c.contact_email}`")
                        st.write(f"**Website:** {c.website}")
                        st.write(f"**Creator Geography:** {c.creator_geography}")
                        st.write(f"**Audience Geography:** {c.audience_geography}")
                        st.divider()
                        st.markdown("**🔍 Data Provenance Tracking:**")
                        st.write(f"- **Primary Source:** {c.source}")
                        st.write(f"- **Source API Endpoint:** `{c.source_url}`")

    # Tab 5: AI Personalization
    with tabs[4]:
        st.subheader("🤖 Gemini LLM Personalized Pitches & Quality Control")
        st.caption("Constraints: Email (60–90 words) | IG DM (15–30 words) | Profile Signal Citation")

        messages = db.query(Message, Creator).join(Creator, Message.creator_id == Creator.id).filter(Message.campaign_id == campaign.id).all()
        if messages:
            for msg, c in messages:
                with st.expander(f"✉️ Pitch for {c.name} (@{c.username}) — Status: {msg.validation_status}"):
                    st.write(f"**Email Subject:** {msg.email_subject}")
                    st.code(msg.email_body, language="text")
                    st.caption(f"Email Word Count: **{msg.email_word_count} words** (Target: 60-90 words)")

                    st.write("**Instagram DM:**")
                    st.code(msg.dm_body, language="text")
                    st.caption(f"DM Word Count: **{msg.dm_word_count} words** (Target: 15-30 words)")

                    st.json(msg.personalization_signals)
        else:
            st.warning("⚠️ No creators currently qualify for AI personalization.")
            st.info("💡 **Reason:** Creators are only personalized after satisfying all mandatory qualification gates (5,000–100,000 verified followers, mandatory public contact email, and source-backed engagement data). Non-qualifying creators are transparently routed to **REVIEW** rather than using synthetic data.")

    # Tab 6: Outreach Sending Layer
    with tabs[5]:
        st.subheader("✉️ Outreach Sending Simulation & Manual DM Workflow")
        st.write(f"**Current Send Mode:** `{SEND_MODE.upper()}`")

        outreach_logs = db.query(OutreachLog, Creator).join(Creator, OutreachLog.creator_id == Creator.id).filter(OutreachLog.campaign_id == campaign.id).all()
        if outreach_logs:
            data = []
            for log, c in outreach_logs:
                data.append({
                    "Creator": c.name,
                    "Username": f"@{c.username}",
                    "Email": log.email,
                    "Status": log.status,
                    "Sent": "YES" if log.sent else "NO",
                    "Sent At": log.sent_at.strftime("%Y-%m-%d %H:%M:%S") if log.sent_at else "-",
                    "Notes": log.error or "Successfully logged"
                })
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.warning("⚠️ No approved creators are currently available for outreach.")
            o_col1, o_col2, o_col3, o_col4 = st.columns(4)
            o_col1.metric("Qualified Creators", q_count)
            o_col2.metric("Personalized Pitches", len(db.query(Message).filter_by(campaign_id=campaign.id).all()))
            o_col3.metric("Approved for Sending", 0)
            o_col4.metric("Outreach Records Sent", 0)
            st.info("💡 **Workflow Status:** Outreach simulation and tracking run automatically when creators satisfy qualification and human review gates. Zero outreach records are generated when 0 creators qualify.")

        st.divider()
        st.subheader("📲 Instagram DM Manual Workflow Cards")
        qualified_msgs = db.query(Message, Creator).join(Creator, Message.creator_id == Creator.id).filter(Message.campaign_id == campaign.id).all()
        if qualified_msgs:
            c1, c2 = st.columns(2)
            for idx, (msg, c) in enumerate(qualified_msgs[:6]):
                dm_info = prepare_dm_workflow(msg.dm_body, c.username)
                with c1 if idx % 2 == 0 else c2:
                    st.info(f"**Target:** @{c.username}\n\n**DM Copy:**\n{dm_info['dm_body']}")
                    st.caption(f"[Open Instagram Profile]({dm_info['profile_url']})")
        else:
            st.caption("No qualified creators available for DM workflow cards.")

    # Tab 7: Outreach Tracker & Traceability Matrix
    with tabs[6]:
        st.subheader("📈 Outreach Tracker & Requirement Traceability Matrix")

        st.markdown("### 📋 Requirement Traceability Matrix")
        matrix_data = [
            {"EDXSO Requirement": "Discover Real Influencers (≥50 Target)", "Implementation Component": "app/discovery/", "Evidence Location": "data/raw/discovered_creators_raw.json"},
            {"EDXSO Requirement": "Micro-Influencer 5K–100K Bound", "Implementation Component": "app/filtering/rules.py", "Evidence Location": "tests/test_filtering.py & UI"},
            {"EDXSO Requirement": "Mandatory Email & Engagement Gates", "Implementation Component": "app/filtering/rules.py", "Evidence Location": "app/filtering/classifier.py (Routes to REVIEW)"},
            {"EDXSO Requirement": "Audience Demographics & Reweighting", "Implementation Component": "app/enrichment/demographics.py", "Evidence Location": "app/filtering/scoring.py"},
            {"EDXSO Requirement": "Explainable Pass/Fail Justification", "Implementation Component": "app/filtering/classifier.py", "Evidence Location": "DB filter_results.filter_reason"},
            {"EDXSO Requirement": "Email (60-90 words) & DM (15-30 words)", "Implementation Component": "app/personalization/validators.py", "Evidence Location": "tests/test_personalization.py"},
            {"EDXSO Requirement": "Sending Layer & Duplicate Prevention", "Implementation Component": "app/outreach/tracker.py", "Evidence Location": "UNIQUE(campaign_id, creator_id) DB Constraint"},
            {"EDXSO Requirement": "Full Dataset Retention (Raw & Processed)", "Implementation Component": "app/enrichment/__init__.py", "Evidence Location": "data/raw/ & data/processed/"},
            {"EDXSO Requirement": "Streamlit UI & CLI Automation Runner", "Implementation Component": "streamlit_app.py & scripts/", "Evidence Location": "scripts/run_pipeline.py"}
        ]
        st.table(pd.DataFrame(matrix_data))

    db.close()


if __name__ == "__main__":
    main()
