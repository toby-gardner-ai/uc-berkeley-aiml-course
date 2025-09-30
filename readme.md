# UC Berkeley Extension - Professional Certificate in AI & Machine Learning

The following notebooks cover various topics across AI & Machine Learning as part of the program - with helpful functions that can be repurposed and used in future projects. 

## Notebooks

### Mod4_Data_Analytics
This notebook does a deeper dive into the classes around data analytics in Modules 3 and 4 providing you practical applications to handle, such as:
1. Initial and ongoing analysis of your datasets using summary_stats function
2. Preliminary data cleaning and preparatory techinuqes using data_cleanse and convert_dtypes functions
3. Missing data: understand the various ways data can appear missing, beyond 'NaN'
4. MCAR v MNAR: understand the difference between missing data completely at random (MCAR) v. not at random (MNAR) and why it matters
5. Detecting outliers through box plot visualisation and how to handle them using a remove_outliers_by_zscore function
6. Missing v. Incorrect Data: understanding when and why incorrect data can be worse than missing data and how to analyse them both

## Getting Started (Using the Repo)

1. **Clone the repo**
   ```bash
   git clone https://github.com/toby-gardner-ai/uc-berkeley-aiml-course
   cd uc-berkeley-aiml-course
   ```

2. **(Optional) Create a virtual environment**
    ```bash 
    python3 -m venv .venv
    source .venv/bin/activate   # On Mac/Linux
    .venv\Scripts\activate      # On Windows
    ```

3. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Launch Jupyter Notebook**

    ```bash
    jupyter notebook
    ```


This opens a web page in the browser where you can then navigate into your notebooks/ folder and click on a notebook e.g. Mod4_Data_Analytics.ipynb.

## Getting Started (Using Colab - notebook specific)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR-USERNAME/uc-berkeley-aiml-course/blob/main/notebooks/Mod4_Data_Analytics.ipynb)

You will need to move the datasets over.