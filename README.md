# YouTube Data Harvesting

This Python script enables you to extract, transform, and load data from YouTube using the YouTube API. The extracted data is then stored in a PostgreSQL database.

## Prerequisites

Before running the script, make sure you have the following installed:

- Python
- Google API Python Client
- Streamlit
- PostgreSQL (psycopg2)
- Pandas

Additionally, you need to obtain a YouTube API key and provide it in the script.

## Getting Started

1. **Install the required dependencies:**

    ```bash
    pip install -r Requirements.txt
    ```

2. **Set up PostgreSQL:**
    - Make sure you have PostgreSQL installed and running on your local machine.
    - Create a database named "youtube" in PostgreSQL.
    - Create tables named "CHANNEL," "PLAYLIST," "VIDEOS," and "COMMENT" in the "youtube" database.

3. **Replace the placeholder values in the script:**
    - Replace the placeholder values for the YouTube API key (`Api_Id`) and other database connection details.

4. **Run the script:**

    ```bash
    streamlit run your_script_name.py
    ```

## Usage

- Enter the YouTube channel ID in the provided input box.
- Click the "Collect and Store Data" button to fetch data from the YouTube API and store it in PostgreSQL.
- Select the desired table to view from the dropdown.
- Execute queries to retrieve specific information from the database.

## Note

- Make sure to handle API keys and database connection details securely.
- This script assumes a local installation of PostgreSQL. Adjust connection details accordingly for a remote database.

## Disclaimer

This script is provided as-is and may require modifications based on your specific use case or changes in the YouTube API.
