import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import seaborn as sns
from terminal_style import sprint, style

df_characters = pd.read_csv("data_extraction/df_final_onepiece.csv")

# ===== FEATURE ENGINEERING =====

# Process affiliations and occupations
df_characters['affiliations'] = df_characters['affiliations'].fillna('').str.split(';')
df_characters['affiliations'] = df_characters['affiliations'].apply(lambda x: [aff.strip() for aff in x if aff.strip() and aff.strip() != "clanofd."])
df_characters['occupations'] = df_characters['occupations'].fillna('').str.split(';')

# Categorical features
affiliations_dummies = pd.get_dummies(df_characters['affiliations'].explode()).groupby(level=0).sum()
affiliations_dummies = affiliations_dummies.drop(columns=['gold.roger', 'portgasd.ace'], errors='ignore')
#TODO check why there are names in affiliations

occupations_dummies = pd.get_dummies(df_characters['occupations'].explode()).groupby(level=0).sum()

other_dummies = pd.get_dummies(df_characters[['devilfruit.type', 'status', 'origin']].fillna('NO DATA'))


# Numerical features
numerical_cols = ['bounty', 'haki.observation', 'haki.armament', 'haki.conqueror']
df_num = df_characters[numerical_cols].fillna(0)

# Combining all features
features_list = [df_num, other_dummies, affiliations_dummies, occupations_dummies]
X = pd.concat(features_list, axis=1)
y = df_characters['has_D'].fillna(0).astype(int)

# Store feature names for later use
feature_names = X.columns.tolist()

# Train model TODO Check where is the pb, too good accuracy
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
model.fit(X_train, y_train)

# ===== MODEL EVALUATION =====

# Print model performance
sprint("\nModel Performance:", color="purple", bold=True)
print("Train accuracy:", style(model.score(X_train, y_train), bold=True))
print("Test accuracy:", style(model.score(X_test, y_test), bold=True, color="green"))

# Plot feature importances
feature_importance = pd.DataFrame({
    'feature': feature_names,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

plt.figure(figsize=(12, 6))
sns.barplot(data=feature_importance.head(10), x='importance', y='feature')
plt.title('Top 10 most important features for predicting Will of D.')
plt.xlabel('Feature importance')
plt.tight_layout()
plt.show()

# Print top 10 most important features
sprint("\nTop 10 most important features:", color="purple", bold=True)
for idx, row in feature_importance.head(10).iterrows():
    print(f"{row['feature']}: {row['importance']}")

# ===== PREDICTION FUNCTION =====
