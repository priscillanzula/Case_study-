import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output

# Load and clean the dataset
file_path = "Case_study.csv"  # Replace with your file path
df = pd.read_csv(file_path)

# Rename the columns to preferred right case
df.columns = [
    'Date', 
    'Anonymized category', 
    'Anonymized product', 
    'Anonymized business', 
    'Anonymized location', 
    'Quantity', 
    'UnitPrice'
]

# Data Cleaning
df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='%B %d, %Y, %I:%M %p')
df['UnitPrice'] = df['UnitPrice'].str.replace(',', '').astype(float)
df['Total value'] = df['Quantity'] * df['UnitPrice']

# Create Month-Year column
df['Month-Year'] = df['Date'].dt.strftime('%B %Y')
df['Date'] = df['Date'].dt.strftime('%Y-%m-%Y')

# Aggregate Data for Insights
category_summary = df.groupby('Anonymized category').agg(
    Total_Quantity=('Quantity', 'sum'),
    Total_value=('Total value', 'sum')
).reset_index()

top_products = df.groupby('Anonymized product').agg(
    Total_Quantity=('Quantity', 'sum'),
    Total_value=('Total value', 'sum')
).reset_index().nlargest(5, 'Total_value')

top_businesses = df.groupby('Anonymized business').agg(
    Total_Quantity=('Quantity', 'sum'),
    Total_value=('Total value', 'sum')
).reset_index().nlargest(5, 'Total_value')

sales_trends = df.groupby('Month-Year').agg(
    Total_Quantity=('Quantity', 'sum'),
    Total_value=('Total value', 'sum')
).reset_index()

# Create Customer Segmentation
# First, aggregate data by customer (i.e., by 'Anonymized location' or another relevant column)
customer_summary = df.groupby('Anonymized location').agg(
    Total_Quantity=('Quantity', 'sum'),
    Total_value=('Total value', 'sum')
).reset_index()

# Define thresholds for segmentation (for simplicity, we'll use 3 segments)
high_value_threshold = customer_summary['Total_value'].quantile(0.75)
low_value_threshold = customer_summary['Total_value'].quantile(0.25)

# Apply segmentation logic
customer_summary['Segmentation'] = customer_summary['Total_value'].apply(
    lambda x: 'High-Value Customers' if x >= high_value_threshold
    else ('Low-Value Customers' if x <= low_value_threshold else 'Medium-Value Customers')
)

# Create Segmentation Summary
segmentation_summary = customer_summary.groupby('Segmentation').agg(
    Total_Customers=('Total_value', 'count'),
    Total_Sales=('Total_value', 'sum')
).reset_index()

# Create Dash App
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div(
    style={'max-width': '1200px', 'margin': '0 auto', 'padding': '20px', 'overflow-x': 'auto'},  # Centered and responsive layout
    children=[
        # Header of the dashboard
        html.H1("Sales Dashboard", style={'textAlign': 'center'}),
        
        # Filter Section: Dropdowns for Category and Date Range
        html.Div(
            style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '30px'},
            children=[
                # Dropdown for Category
                dcc.Dropdown(
                    id='category-dropdown',
                    options=[{'label': cat, 'value': cat} for cat in df['Anonymized category'].unique()],
                    value=df['Anonymized category'].unique()[0],
                    style={'width': '48%'}
                ),
                # Date Range Picker
                dcc.DatePickerRange(
                    id='date-picker-range',
                    start_date=df['Date'].min(),
                    end_date=df['Date'].max(),
                    display_format='YYYY-MM-DD',
                    style={'width': '48%'}
                )
            ]
        ),
        
        # Total Quantity and Value by Category (Graph)
        html.Div(
            children=[
                html.H2("Total Quantity and Value by Category"),
                dcc.Graph(
                    id='category-bar',
                    figure=px.bar(category_summary, x='Anonymized category', y=['Total_Quantity', 'Total_value'],
                                  barmode='group', title="Total Quantity and Value by Category"),
                    style={'height': '350px'}  # Restrict height
                )
            ],
            style={'margin-bottom': '30px'}
        ),
        
        # Top Performing Products (Graph)
        html.Div(
            children=[
                html.H2("Top Performing Products (by Value)"),
                dcc.Graph(
                    id='top-products',
                    figure=px.bar(top_products, x='Anonymized product', y='Total_value', 
                                  title="Top 5 Products by Value"),
                    style={'height': '350px'}  # Restrict height
                )
            ],
            style={'margin-bottom': '30px'}
        ),
        
        # Top Performing Businesses (Graph)
        html.Div(
            children=[
                html.H2("Top Performing Businesses (by Value)"),
                dcc.Graph(
                    id='top-businesses',
                    figure=px.bar(top_businesses, x='Anonymized business', y='Total_value', 
                                  title="Top 5 Businesses by Value"),
                    style={'height': '350px'}  # Restrict height
                )
            ],
            style={'margin-bottom': '30px'}
        ),
        
        # Time Series of Sales Trends (Graph)
        html.Div(
            children=[
                html.H2("Sales Trends Over Time"),
                dcc.Graph(
                    id='sales-trends',
                    figure=px.line(sales_trends, x='Month-Year', y=['Total_Quantity', 'Total_value'],
                                   title="Sales Trends Over Time"),
                    style={'height': '350px'}  # Restrict height
                )
            ],
            style={'margin-bottom': '30px'}
        ),
        
        # Customer Segmentation Summary (Graph)
        html.Div(
            children=[
                html.H2("Customer Segmentation Summary"),
                dcc.Graph(
                    id='customer-segmentation',
                    figure=px.pie(segmentation_summary, names='Segmentation', values='Total_Sales', 
                                  title="Customer Segmentation by Total Sales"),
                    style={'height': '350px'}
                )
            ],
            style={'margin-bottom': '30px'}
        ),
        
        # Customer Segmentation Details (Cards)
        html.Div(
            children=[
                html.Div([html.H3(f"{seg} Segmentation", style={'fontWeight': 'bold'}) for seg in segmentation_summary['Segmentation']])
            ],
            style={'display': 'flex', 'justifyContent': 'space-between'}
        )
    ]
)

# Callback for interactivity (filtering based on dropdown and date range)
@app.callback(
    [Output('category-bar', 'figure'),
     Output('top-products', 'figure'),
     Output('top-businesses', 'figure'),
     Output('sales-trends', 'figure'),
     Output('customer-segmentation', 'figure')],
    [Input('category-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_charts(selected_category, start_date, end_date):
    # Filter data based on selected category and date range
    filtered_df = df[(df['Anonymized category'] == selected_category) & 
                     (df['Date'] >= start_date) & 
                     (df['Date'] <= end_date)]

    # Update the charts with filtered data
    category_summary_filtered = filtered_df.groupby('Anonymized category').agg(
        Total_Quantity=('Quantity', 'sum'),
        Total_value=('Total value', 'sum')
    ).reset_index()

    top_products_filtered = filtered_df.groupby('Anonymized product').agg(
        Total_Quantity=('Quantity', 'sum'),
        Total_value=('Total value', 'sum')
    ).reset_index().nlargest(5, 'Total_value')

    top_businesses_filtered = filtered_df.groupby('Anonymized business').agg(
        Total_Quantity=('Quantity', 'sum'),
        Total_value=('Total value', 'sum')
    ).reset_index().nlargest(5, 'Total_value')

    sales_trends_filtered = filtered_df.groupby('Month-Year').agg(
        Total_Quantity=('Quantity', 'sum'),
        Total_value=('Total value', 'sum')
    ).reset_index()

    segmentation_summary_filtered = filtered_df.groupby('Anonymized location').agg(
        Total_Quantity=('Quantity', 'sum'),
        Total_value=('Total value', 'sum')
    ).reset_index()

    # Segmentation
    high_value_threshold = segmentation_summary_filtered['Total_value'].quantile(0.75)
    low_value_threshold = segmentation_summary_filtered['Total_value'].quantile(0.25)

    segmentation_summary_filtered['Segmentation'] = segmentation_summary_filtered['Total_value'].apply(
        lambda x: 'High-Value Customers' if x >= high_value_threshold
        else ('Low-Value Customers' if x <= low_value_threshold else 'Medium-Value Customers')
    )

    segmentation_summary_filtered = segmentation_summary_filtered.groupby('Segmentation').agg(
        Total_Customers=('Total_value', 'count'),
        Total_Sales=('Total_value', 'sum')
    ).reset_index()

    # Create the updated figures
    category_fig = px.bar(category_summary_filtered, x='Anonymized category', y=['Total_Quantity', 'Total_value'],
                          barmode='group', title="Total Quantity and Value by Category")
    top_products_fig = px.bar(top_products_filtered, x='Anonymized product', y='Total_value',
                              title="Top 5 Products by Value")
    top_businesses_fig = px.bar(top_businesses_filtered, x='Anonymized business', y='Total_value',
                                title="Top 5 Businesses by Value")
    sales_trends_fig = px.line(sales_trends_filtered, x='Month-Year', y=['Total_Quantity', 'Total_value'],
                               title="Sales Trends Over Time")
    customer_segmentation_fig = px.pie(segmentation_summary_filtered, names='Segmentation', values='Total_Sales',
                                       title="Customer Segmentation by Total Sales")

    return category_fig, top_products_fig, top_businesses_fig, sales_trends_fig, customer_segmentation_fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)