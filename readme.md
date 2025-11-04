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

### Mod6_PCA_Clustering
This notebook does a deeper dive into the classes around PCA and Clustering in Modules 6 providing you practical applications to handle, such as:
1. Initial and ongoing analysis of your datasets using summary_stats function
2. Preliminary data cleaning and preparatory techniques - including missing data, detecting and removing outliers, dropping columns that are too unique or not unique
3. Feature Engineering: how to create new features from existing features e.g. dt_customer
4. Scaling: why it matters for numerical data and simple tools you can use
5. PCA: key assumptions, alternatives
6. PCA Analysis: how to interpret PCA using scree plots et. al + how to use it in your (future) model
7. Unsupervised learning features: how to add PC and Cluster features into your existing dataset
8. Next steps: what other steps remain before we're ready to select and run a model

### Mod8_Feat_Engineering
This notebook deep-dives into feature engineering in the context of both traditional machine learning and large language models (LLMs). You will explore practical techniques to transform raw data into model-ready formats, understand how these transformations differ across ML paradigms, and build intuition for the encoding foundations that power modern LLMs.

Specifically, this notebook covers:
1. Traditional ML Feature Encoding
- Apply one-hot and ordinal encoding to structured categorical data
- Understand how these approaches create explicit features for downstream models
2. Text Feature Engineering for LLMs
- Learn how LLMs defer feature identification to the model itself, discovering latent features during training
- Compare traditional feature engineering workflows with LLM pipelines
3. Chunking & Tokenisation Concepts
- Explore chunking as a preparation step for large text corpora
- Understand the difference between text splitting, tokenisation, and encoding
4. BPE Tokenizer Training
- Build and train a Byte Pair Encoding (BPE) tokenizer on a text corpus
- Observe how tokenisers extract frequent subword patterns (feature extraction)
- Map these patterns to stable numeric IDs suitable for model training (feature engineering)
5. Practical Tokenisation Demo
- Inspect vocabulary and learned subword units
- Tokenise real text samples and compare results to traditional encoders
6. Conceptual Bridges & Diagrams
- Use flow diagrams to illustrate the end-to-end LLM ingestion pipeline
- Reinforce how tokenisation transforms text into embedding-ready numerical form

By the end of this module, you’ll not only know how to encode features in both traditional and LLM settings — you’ll also understand why encoding matters, what information is preserved or lost through different methods, and how tokenisation forms the foundation of modern language model capability.


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