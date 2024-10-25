# GROMACS External Pulse Excited Transition State Kinetic Energy Visualization and Analysis App

This project is a **Streamlit** application for visualizing and analyzing GROMACS simulation data involving external pulse excitation and kinetic energy transitions. The app provides advanced visual tools to understand transition states, kinetic energy distributions, and other simulation parameters.

**Planned Features** include basic user authentication (using **SQLite**) for collaborative analysis and annotation.

## Features

- **Kinetic Energy Visualization**: Visualize kinetic energy distributions for residues and atoms across GROMACS simulation frames.
- **Heatmap Analysis**: Interactive heatmaps to explore energy variations, reorder residues, and compare different run categories.
- **Histogram Customization**: Select value ranges from histograms to control heatmap color coding, making specific energy transitions more visible.

## Planned Authentication Features

- **User Registration**: New users can register to save analysis and add comments.
- **User Login**: Registered users can log in to access saved sessions.
- **User Logout**: Logged-in users can log out to secure their session.

## Requirements

- **Python 3.7+**
- **Streamlit**
- **SQLite**
- **bcrypt**

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Freezing Dependencies

To create a `requirements.txt` file for freezing the dependencies:

1. Make sure your virtual environment is activated.
2. Install all required packages (`streamlit`, `bcrypt`, etc.) using `pip install`.
3. Run the following command to generate the `requirements.txt`:
   ```bash
   pip freeze > requirements.txt
   ```
   This will save the current versions of all installed packages in your virtual environment to `requirements.txt`.

## Running the App

1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```
2. Open the local address provided by Streamlit in your web browser to use the app.

## Running Tests

The unit tests for authentication are located in `test_auth_handler.py`.
To run the tests, use:

```bash
python -m unittest test_auth_handler.py
```

## Deployment

You can deploy the Streamlit app on platforms such as **Streamlit Cloud**, **Heroku**, or **AWS**. Currently, the app is not set up with active user authentication for deployment but can be easily extended once the hosted SQL database is set up.

## Future Work

- **Deploy Authentication Module**: Integrate authentication features when deploying to a cloud environment to allow users to save and share analysis.
- **User State Management**: Implement persistent storage to save user comments, selected parameters, and analysis states.
- **Performance Enhancements**: Optimize database connections and improve the efficiency of data handling for large GROMACS datasets.
- **Advanced Data Analysis Tools**: Add features for in-depth statistical analysis of kinetic energy transitions and automated detection of significant events.

## License

This project is licensed under the MIT License.

## Authors

- István Lőrincz

Feel free to reach out for any questions or collaboration!
