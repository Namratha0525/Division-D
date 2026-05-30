import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.constants import COLOR_PALETTE

class ChartGenerator:
    def __init__(self):
        self.colors = COLOR_PALETTE

    def plot_waste_composition_donut(self, df: pd.DataFrame) -> go.Figure:
        """Generates a donut chart displaying plastic polymer compositions."""
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No audit records loaded.", showarrow=False, font=dict(size=16))
            return fig
            
        summary = df.groupby("polymer_desc")["weight_kg"].sum().reset_index()
        
        fig = px.pie(
            summary, 
            values="weight_kg", 
            names="polymer_desc", 
            hole=0.4,
            color_discrete_sequence=[self.colors["primary"], self.colors["secondary"], self.colors["highlight"], "#8FBC8F", "#E0EEE0", "#BCD2EE", "#B0C4DE"]
        )
        
        fig.update_layout(
            title_text="Plastic Waste Breakdown by Polymer Type",
            title_x=0.1,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=40, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        return fig

    def plot_disposal_bar(self, df: pd.DataFrame) -> go.Figure:
        """Generates a horizontal bar chart mapping disposal pathway distributions."""
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No audit records loaded.", showarrow=False, font=dict(size=16))
            return fig
            
        summary = df.groupby("disposal_desc")["weight_kg"].sum().reset_index().sort_values(by="weight_kg")
        
        # Color mapping depending on green vs red pathways
        colors = []
        for pathway in summary["disposal_desc"]:
            if "Recycling" in pathway or "Cement" in pathway:
                colors.append(self.colors["alert_green"])
            elif "Burning" in pathway:
                colors.append(self.colors["alert_red"])
            else:
                colors.append(self.colors["alert_orange"])
                
        fig = go.Figure(go.Bar(
            x=summary["weight_kg"],
            y=summary["disposal_desc"],
            orientation='h',
            marker_color=colors
        ))
        
        fig.update_layout(
            title_text="Disposal Channels Distribution (Kg)",
            title_x=0.1,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=40, b=10, l=10, r=10),
            xaxis=dict(gridcolor='#EAEAEA', title="Weight (kg)"),
            yaxis=dict(title="")
        )
        return fig

    def plot_monthly_trends(self, df: pd.DataFrame) -> go.Figure:
        """Plots monthly timeline trends for audit volumes."""
        if df.empty:
            return go.Figure()
            
        # Group by month string representation
        df_copy = df.copy()
        df_copy["month_year"] = df_copy["date"].dt.strftime("%b %Y")
        summary = df_copy.groupby("month_year")["weight_kg"].sum().reset_index()
        
        fig = px.line(
            summary, 
            x="month_year", 
            y="weight_kg", 
            markers=True,
            line_shape="spline",
            color_discrete_sequence=[self.colors["primary"]]
        )
        
        fig.update_layout(
            title_text="Plastic Audit Volume Timeline",
            title_x=0.1,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=40, b=10, l=10, r=10),
            xaxis=dict(title="Month", gridcolor='#EAEAEA'),
            yaxis=dict(title="Weight (kg)", gridcolor='#EAEAEA')
        )
        return fig

    def plot_sustainability_gauge(self, score: float, color: str) -> go.Figure:
        """Renders an interactive speedometer gauge rating the score."""
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Sustainability Index", 'font': {'size': 18, 'color': self.colors["primary"]}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#FFF5F5'}, # Red tint
                    {'range': [50, 70], 'color': '#FFF8F2'}, # Amber tint
                    {'range': [70, 85], 'color': '#F4FBF4'}, # Sage tint
                    {'range': [85, 100], 'color': '#EDFAED'}  # Rich green tint
                ],
                'threshold': {
                    'line': {'color': "green", 'width': 4},
                    'thickness': 0.75,
                    'value': 85
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=50, b=10, l=20, r=20),
            height=260
        )
        return fig

    def plot_roadmap_flowchart(self) -> go.Figure:
        """
        Generates an executive-level horizontal milestone flowchart for the 12-month roadmap.
        """
        fig = go.Figure()
        
        # 1. Add Card Milestone Annotations
        phases = [
            {
                "x": 1.0,
                "title": "Month 1-3",
                "subtitle": "Policy & Setup",
                "details": "• Policy Setup<br/>• Single-Use Plastic Ban<br/>• Vendor Registration",
                "color": "#1E4620" # Dark Green
            },
            {
                "x": 2.5,
                "title": "Month 4-6",
                "subtitle": "Segregation Infra",
                "details": "• Separate Bins Setup<br/>• Staff Training<br/>• Collection Logging",
                "color": "#5C8D89" # Teal
            },
            {
                "x": 4.0,
                "title": "Month 7-9",
                "subtitle": "Partnerships",
                "details": "• Recycler MoUs<br/>• Waste Tracking<br/>• EPR Target Audit",
                "color": "#8FBC8F" # Light Green
            },
            {
                "x": 5.5,
                "title": "Month 10-12",
                "subtitle": "Certification",
                "details": "• Secondary Audit<br/>• Green Campus Cert<br/>• 100% Target Met",
                "color": "#D9822B" # Amber
            }
        ]
        
        for phase in phases:
            text = (
                f"<span style='font-size:14px; font-weight:bold; color:white;'>{phase['title']}</span><br/>"
                f"<span style='font-size:12px; font-weight:bold; color:white;'>{phase['subtitle']}</span><br/><br/>"
                f"<span style='font-size:10px; color:#F5F5F5; line-height:1.4;'>{phase['details']}</span>"
            )
            
            fig.add_annotation(
                x=phase["x"],
                y=1.0,
                text=text,
                showarrow=False,
                align="left",
                font=dict(family="Arial", size=11, color="white"),
                bgcolor=phase["color"],
                bordercolor=phase["color"],
                borderwidth=2,
                borderpad=12,
                width=160,
                height=110
            )

        # 2. Add Connective Arrows between Card steps
        arrows = [1.75, 3.25, 4.75]
        for arrow_x in arrows:
            fig.add_annotation(
                x=arrow_x,
                y=1.0,
                text="➔",
                showarrow=False,
                font=dict(size=24, color="#5C8D89")
            )
            
        fig.update_layout(
            xaxis=dict(range=[0.2, 6.3], showgrid=False, zeroline=False, visible=False),
            yaxis=dict(range=[0.4, 1.6], showgrid=False, zeroline=False, visible=False),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=10, b=10, l=10, r=10),
            height=200,
            width=850
        )
        
        return fig

