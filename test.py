import streamlit as st
from streamlit_plotly_events import plotly_events
import plotly.graph_objects as go

# Sample data for the bar graph
data = {'Categories': ['A', 'B', 'C', 'D'], 'Values': [10, 20, 15, 30]}
fig = go.Figure(data=[go.Bar(x=data['Categories'], y=data['Values'])])

# Display the chart and capture click event
selected_points = plotly_events(fig)

# Use the selected bar info elsewhere
if selected_points:
    selected_bar = selected_points[0]  # Get info about the clicked bar
    st.write("Clicked bar information:", selected_bar)
    st.write("Category:", data['Categories'][selected_bar['pointIndex']])
    st.write("Value:", data['Values'][selected_bar['pointIndex']])
