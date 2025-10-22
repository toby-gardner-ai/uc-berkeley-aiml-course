from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def pca_recommendation_viz(df, scale_data=True, top_n_pc=3):
    
    # Scale data
    if scale_data:
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df)
    else:
        scaled_data = df.values

    # Fit PCA
    pca = PCA()
    pca.fit(scaled_data)
    explained_var = pca.explained_variance_ratio_
    cum_var = np.cumsum(explained_var)

    # Set thresholds
    n_components_95 = np.argmax(cum_var >= 0.95) + 1
    n_components_80 = np.argmax(cum_var >= 0.80) + 1

    # Load Features
    loadings = pd.DataFrame(
        pca.components_[:top_n_pc, :],
        columns=df.columns,
        index=[f'PC{i+1}' for i in range(top_n_pc)]
    )

    # Set up Visuals
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 1. Scree plot
    axes[0].plot(range(1, len(explained_var) + 1), explained_var * 100, 'o-', label='Individual')
    axes[0].plot(range(1, len(cum_var) + 1), cum_var * 100, 's--', label='Cumulative')
    axes[0].axhline(5, color='r', linestyle='--', alpha=0.5, label='5% cutoff')
    axes[0].set_title('Scree Plot (Variance Explained)')
    axes[0].set_xlabel('Principal Component')
    axes[0].set_ylabel('Variance Explained (%)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 2. PC vs Feature Heatmap
    im = axes[1].imshow(loadings, cmap='coolwarm', aspect='auto')
    axes[1].set_xticks(range(len(df.columns)))
    axes[1].set_xticklabels(df.columns, rotation=90)
    axes[1].set_yticks(range(top_n_pc))
    axes[1].set_yticklabels(loadings.index)
    axes[1].set_title(f'Top {top_n_pc} PCs vs Features')
    fig.colorbar(im, ax=axes[1], fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.show()

    # Generate recommendations
    total_var = cum_var[-1]
    strong_pcs = np.sum(explained_var > 0.05)

    if strong_pcs == 0:
        recommendation = "Keep existing features (PCA offers little dimensionality reduction)."
    elif n_components_95 <= len(df.columns) * 0.5:
        recommendation = "Use PCA features (significant dimensionality reduction with >95% variance retained)."
    elif n_components_80 <= len(df.columns) * 0.8:
        recommendation = f"Add <={n_components_80} PCs as new features only."
    else:
        recommendation = "Keep existing features (original features carry distributed information)."

    # Summary table
    recommendation_df = pd.DataFrame({
        'Metric': ['Total Variance Explained', 
                   'PCs for 80% Variance', 
                   'PCs for 95% Variance',
                   'Strong PCs (>5% var each)',
                   'Recommendation'],
        'Value': [f"{total_var*100:.1f}%", 
                  n_components_80, 
                  n_components_95,
                  strong_pcs, 
                  recommendation]
    })

    
    return recommendation_df