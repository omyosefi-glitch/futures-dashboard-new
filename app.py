import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from scipy.stats import norm
import os
from datetime import datetime

st.set_page_config(page_title="Ultimate Futures Dashboard", layout="wide")

# ================================
# حالت دارک/روشن
# ================================
if 'theme' not in st.session_state:
    st.session_state.theme = "Dark"

col_title, col_theme = st.columns([4, 1])
with col_title:
    st.title("📈 ULTIMATE FUTURES TRADING DASHBOARD")
with col_theme:
    theme = st.selectbox("🎨 Theme", ["Dark", "Light"], index=0 if st.session_state.theme == "Dark" else 1)
    st.session_state.theme = theme

bg_color = "#0e1117" if theme == "Dark" else "#ffffff"
text_color = "white" if theme == "Dark" else "black"

# ================================
# بارگذاری داده
# ================================
uploaded_file = st.file_uploader("📂 آپلود فایل Excel", type=["xlsx"])
default_path = "closeout_complete.xlsx"

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("✅ فایل جدید بارگیری شد.")
elif os.path.exists(default_path):
    df = pd.read_excel(default_path)
    st.info("📁 فایل پیش‌فرض بارگیری شد.")
else:
    st.warning("⚠️ لطفاً فایل Excel را آپلود کنید.")
    st.stop()

df['Date'] = pd.to_datetime(df['Date'])
df['Month_Name'] = df['Date'].dt.strftime('%b')
df['Year'] = df['Date'].dt.year

# ================================
# تب‌های اصلی
# ================================
tabs = st.tabs([
    "🏠 Home", 
    "🔄 Compare Periods", 
    "📊 Analysis", 
    "📈 Statistics", 
    "📥 Export Report"
])

# ==================================================
# 🏠 تب Home
# ==================================================
with tabs[0]:
    st.header("📊 خلاصه عملکرد کلی")
    
    total_profit = df[df['P&L (USD)'] > 0]['P&L (USD)'].sum()
    total_loss = df[df['P&L (USD)'] < 0]['P&L (USD)'].sum()
    net = df['P&L (USD)'].sum()
    win_rate = len(df[df['P&L (USD)'] > 0]) / len(df) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Trades", len(df))
    col2.metric("Net Profit", f"${net:,.0f}")
    col3.metric("Win Rate", f"{win_rate:.1f}%")
    col4.metric("Best Commodity", df.groupby('Commodity')['P&L (USD)'].sum().idxmax()[:20])
    
    cumulative = df.sort_values('Date')
    cumulative['Cumulative'] = cumulative['P&L (USD)'].cumsum()
    fig = px.line(cumulative, x='Date', y='Cumulative', title='Cumulative P&L', markers=True, height=400)
    fig.update_traces(line=dict(color='#00FF88', width=3))
    fig.update_layout(plot_bgcolor=bg_color, paper_bgcolor=bg_color, font=dict(color=text_color))
    st.plotly_chart(fig, use_container_width=True)

# ==================================================
# 🔄 تب مقایسه دو بازه زمانی (پیشرفته با ۴ گراف)
# ==================================================
with tabs[1]:
    st.header("🔄 مقایسه دو بازه زمانی")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📅 دوره اول")
        start1 = st.date_input("از تاریخ (دوره 1)", df['Date'].min(), key="start1")
        end1 = st.date_input("تا تاریخ (دوره 1)", df['Date'].max(), key="end1")
    with col2:
        st.subheader("📅 دوره دوم")
        start2 = st.date_input("از تاریخ (دوره 2)", df['Date'].min(), key="start2")
        end2 = st.date_input("تا تاریخ (دوره 2)", df['Date'].max(), key="end2")
    
    period1 = df[(df['Date'] >= pd.to_datetime(start1)) & (df['Date'] <= pd.to_datetime(end1))]
    period2 = df[(df['Date'] >= pd.to_datetime(start2)) & (df['Date'] <= pd.to_datetime(end2))]
    
    # کارت‌های مقایسه
    st.subheader("📊 مقایسه عددی")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("تعداد معاملات دوره 1", len(period1))
        st.metric("تعداد معاملات دوره 2", len(period2))
        diff_trades = len(period2) - len(period1)
        st.metric("تغییر", f"{diff_trades:+d}", delta_color="normal")
    with col2:
        st.metric("سود خالص دوره 1", f"${period1['P&L (USD)'].sum():,.0f}")
        st.metric("سود خالص دوره 2", f"${period2['P&L (USD)'].sum():,.0f}")
        diff_net = period2['P&L (USD)'].sum() - period1['P&L (USD)'].sum()
        st.metric("تغییر", f"${diff_net:+,.0f}", delta_color="normal")
    with col3:
        wr1 = len(period1[period1['P&L (USD)'] > 0]) / len(period1) * 100 if len(period1) > 0 else 0
        wr2 = len(period2[period2['P&L (USD)'] > 0]) / len(period2) * 100 if len(period2) > 0 else 0
        st.metric("نرخ برد دوره 1", f"{wr1:.1f}%")
        st.metric("نرخ برد دوره 2", f"{wr2:.1f}%")
        diff_wr = wr2 - wr1
        st.metric("تغییر", f"{diff_wr:+.1f}%", delta_color="normal")
    with col4:
        best1 = period1.groupby('Commodity')['P&L (USD)'].sum().idxmax() if len(period1) > 0 else "-"
        best2 = period2.groupby('Commodity')['P&L (USD)'].sum().idxmax() if len(period2) > 0 else "-"
        st.metric("بهترین کالا دوره 1", best1[:15])
        st.metric("بهترین کالا دوره 2", best2[:15])
    
    # گراف 1: مقایسه سود تجمعی
    st.subheader("📈 مقایسه روند سود تجمعی")
    fig = go.Figure()
    cum1 = period1.sort_values('Date')
    cum1['Cumulative'] = cum1['P&L (USD)'].cumsum()
    cum2 = period2.sort_values('Date')
    cum2['Cumulative'] = cum2['P&L (USD)'].cumsum()
    fig.add_trace(go.Scatter(x=cum1['Date'], y=cum1['Cumulative'], mode='lines', name='Period 1', line=dict(color='#00FF88', width=3)))
    fig.add_trace(go.Scatter(x=cum2['Date'], y=cum2['Cumulative'], mode='lines', name='Period 2', line=dict(color='#FF5555', width=3)))
    fig.update_layout(title='مقایسه روند سود تجمعی', xaxis_title='Date', yaxis_title='Cumulative P&L', height=450,
                      plot_bgcolor=bg_color, paper_bgcolor=bg_color, font=dict(color=text_color))
    st.plotly_chart(fig, use_container_width=True)
    
    # گراف 2: مقایسه سود ماهانه (کنار هم)
    st.subheader("📊 مقایسه سود ماهانه")
    monthly1 = period1.groupby('Month_Name')['P&L (USD)'].sum().reset_index()
    monthly1['Period'] = 'Period 1'
    monthly2 = period2.groupby('Month_Name')['P&L (USD)'].sum().reset_index()
    monthly2['Period'] = 'Period 2'
    monthly_combined = pd.concat([monthly1, monthly2])
    fig = px.bar(monthly_combined, x='Month_Name', y='P&L (USD)', color='Period', barmode='group',
                 title='مقایسه سود ماهانه', color_discrete_map={'Period 1': '#00FF88', 'Period 2': '#FF5555'}, height=450)
    fig.update_layout(plot_bgcolor=bg_color, paper_bgcolor=bg_color, font=dict(color=text_color))
    st.plotly_chart(fig, use_container_width=True)
    
    # گراف 3: مقایسه سهم کالاها (نمودارهای کنار هم)
    st.subheader("🥧 مقایسه سهم ۵ کالای برتر")
    col1, col2 = st.columns(2)
    with col1:
        top5_1 = period1.groupby('Commodity')['P&L (USD)'].sum().nlargest(5).reset_index()
        fig1 = px.pie(top5_1, names='Commodity', values='P&L (USD)', title='دوره 1', hole=0.3, height=400)
        fig1.update_layout(plot_bgcolor=bg_color, paper_bgcolor=bg_color, font=dict(color=text_color))
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        top5_2 = period2.groupby('Commodity')['P&L (USD)'].sum().nlargest(5).reset_index()
        fig2 = px.pie(top5_2, names='Commodity', values='P&L (USD)', title='دوره 2', hole=0.3, height=400)
        fig2.update_layout(plot_bgcolor=bg_color, paper_bgcolor=bg_color, font=dict(color=text_color))
        st.plotly_chart(fig2, use_container_width=True)
    
    # گراف 4: مقایسه توزیع سود (هیستوگرام کنار هم)
    st.subheader("📉 مقایسه توزیع سود")
    fig = make_subplots(rows=1, cols=2, subplot_titles=('دوره 1', 'دوره 2'))
    fig.add_trace(go.Histogram(x=period1['P&L (USD)'], nbinsx=20, name='Period 1', marker_color='#00FF88'), row=1, col=1)
    fig.add_trace(go.Histogram(x=period2['P&L (USD)'], nbinsx=20, name='Period 2', marker_color='#FF5555'), row=1, col=2)
    fig.update_layout(title='مقایسه توزیع سود و زیان', height=450, showlegend=False,
                      plot_bgcolor=bg_color, paper_bgcolor=bg_color, font=dict(color=text_color))
    st.plotly_chart(fig, use_container_width=True)

# ==================================================
# 📊 تب Analysis (با فیلتر)
# ==================================================
with tabs[2]:
    st.header("🔍 فیلترهای تخصصی و تحلیل")
    
    with st.sidebar:
        st.subheader("🎯 فیلترها")
        start_date = st.date_input("از تاریخ", df['Date'].min())
        end_date = st.date_input("تا تاریخ", df['Date'].max())
        type_filter = st.multiselect("نوع معامله", df['Type'].unique(), default=df['Type'].unique())
        commodity_filter = st.multiselect("کالا", df['Commodity'].unique(), default=df['Commodity'].unique())
        min_pnl = st.number_input("حداقل سود", value=int(df['P&L (USD)'].min()))
        max_pnl = st.number_input("حداکثر سود", value=int(df['P&L (USD)'].max()))
    
    filtered = df[
        (df['Date'] >= pd.to_datetime(start_date)) &
        (df['Date'] <= pd.to_datetime(end_date)) &
        (df['Type'].isin(type_filter)) &
        (df['Commodity'].isin(commodity_filter)) &
        (df['P&L (USD)'] >= min_pnl) &
        (df['P&L (USD)'] <= max_pnl)
    ]
    
    if filtered.empty:
        st.warning("⚠️ با فیلترهای انتخابی داده‌ای وجود ندارد.")
    else:
        st.success(f"نمایش {len(filtered)} معامله")
        
        col1, col2 = st.columns(2)
        with col1:
            cum = filtered.sort_values('Date')
            cum['Cumulative'] = cum['P&L (USD)'].cumsum()
            fig = px.line(cum, x='Date', y='Cumulative', title='Cumulative P&L', markers=True, height=350)
            fig.update_traces(line=dict(color='#00FF88', width=3))
            st.plotly_chart(fig, use_container_width=True)
            
            top5 = filtered.groupby('Commodity')['P&L (USD)'].sum().nlargest(5).reset_index()
            fig = px.pie(top5, names='Commodity', values='P&L (USD)', title='Top 5 Commodities', hole=0.3, height=350)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            monthly = filtered.groupby('Month_Name')['P&L (USD)'].sum().reset_index()
            fig = px.bar(monthly, x='Month_Name', y='P&L (USD)', title='Monthly P&L', color='P&L (USD)', height=350)
            st.plotly_chart(fig, use_container_width=True)
            
            best = filtered.groupby('Commodity')['P&L (USD)'].sum().nlargest(5).reset_index()
            fig = px.bar(best, x='P&L (USD)', y='Commodity', title='Best Performing', orientation='h', height=350)
            st.plotly_chart(fig, use_container_width=True)

# ==================================================
# 📈 تب Statistics
# ==================================================
with tabs[3]:
    st.header("📊 آمار پیشرفته")
    
    total_profit = df[df['P&L (USD)'] > 0]['P&L (USD)'].sum()
    total_loss = df[df['P&L (USD)'] < 0]['P&L (USD)'].sum()
    avg_win = df[df['P&L (USD)'] > 0]['P&L (USD)'].mean()
    avg_loss = df[df['P&L (USD)'] < 0]['P&L (USD)'].mean()
    profit_factor = abs(total_profit / total_loss) if total_loss != 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trades", len(df))
        st.metric("Winning Trades", f"{len(df[df['P&L (USD)'] > 0])} ({win_rate:.1f}%)")
        st.metric("Losing Trades", f"{len(df[df['P&L (USD)'] < 0])} ({100 - win_rate:.1f}%)")
    with col2:
        st.metric("Total Profit", f"${total_profit:,.0f}")
        st.metric("Total Loss", f"${total_loss:,.0f}")
        st.metric("NET PROFIT", f"${df['P&L (USD)'].sum():,.0f}")
    with col3:
        st.metric("Avg Win", f"${avg_win:,.0f}")
        st.metric("Avg Loss", f"${avg_loss:,.0f}")
        st.metric("Profit Factor", f"{profit_factor:.2f}")
    
    st.subheader("📉 توزیع سود با منحنی نرمال")
    data = df['P&L (USD)'].dropna()
    mean = data.mean()
    std = data.std()
    fig = px.histogram(data, x='P&L (USD)', nbins=30, title='', color_discrete_sequence=['#00FF88'],
                       histnorm='probability density', height=500)
    x_vals = np.linspace(data.min(), data.max(), 100)
    y_vals = norm.pdf(x_vals, mean, std)
    fig.add_scatter(x=x_vals, y=y_vals, mode='lines', name='Normal Curve', line=dict(color='#FF5555', width=3))
    fig.add_vline(x=mean, line_dash="dash", line_color="blue", annotation_text=f"Mean: ${mean:,.0f}")
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break-even")
    fig.update_layout(xaxis_title='P&L (USD)', yaxis_title='Density', height=500,
                      plot_bgcolor=bg_color, paper_bgcolor=bg_color, font=dict(color=text_color))
    st.plotly_chart(fig, use_container_width=True)

# ==================================================
# 📥 تب Export Report
# ==================================================
with tabs[4]:
    st.header("📥 خروجی حرفه‌ای")
    
    csv = df.to_csv(index=False)
    st.download_button("📊 دانلود CSV (همه داده‌ها)", data=csv, file_name="trades_export.csv", mime="text/csv")
    
    st.subheader("📋 خلاصه آماری")
    st.dataframe(df[['Date', 'Commodity', 'Type', 'P&L (USD)']].sort_values('Date', ascending=False), use_container_width=True)
    
    st.info("💡 برای خروجی PDF، می‌توانید از گواهی (Ctrl+P) استفاده کنید.")
