"""
Tax Prediction Model Training Script
Trains an XGBoost model for predicting tax liability based on income and deductions.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import json
import argparse
import os
from datetime import datetime

def calculate_tax_from_slabs(taxable_income):
    """Calculate tax using Indian progressive tax slabs"""
    slabs = [
        (250000, 0.0),    # 0% up to 2.5L
        (500000, 0.05),   # 5% from 2.5L to 5L
        (1000000, 0.20),  # 20% from 5L to 10L
        (float('inf'), 0.30)  # 30% above 10L
    ]
    
    tax = 0
    remaining_income = taxable_income
    prev_limit = 0
    
    for limit, rate in slabs:
        if remaining_income <= 0:
            break
        
        taxable_in_slab = min(remaining_income, limit - prev_limit)
        tax += taxable_in_slab * rate
        remaining_income -= taxable_in_slab
        prev_limit = limit
    
    return tax

def create_sample_tax_data(output_path="../data/tax_dataset.csv", n_samples=5000):
    """Create sample tax data for training"""
    # Normalize path
    output_path = os.path.normpath(output_path)
    
    np.random.seed(42)
    
    data = []
    for i in range(n_samples):
        # Generate income sources
        salary_income = np.random.lognormal(11, 0.8)  # ~30k-200k
        business_income = np.random.lognormal(9, 1.2) if np.random.random() < 0.3 else 0
        capital_gains = np.random.lognormal(8, 1.5) if np.random.random() < 0.2 else 0
        
        total_income = salary_income + business_income + capital_gains
        
        # Generate deductions
        standard_deduction = 50000
        hra_exemption = min(salary_income * 0.4, 100000) if salary_income > 0 else 0
        section_80c = np.random.uniform(0, 150000) if np.random.random() < 0.7 else 0
        section_80d = np.random.uniform(0, 25000) if np.random.random() < 0.5 else 0
        
        total_deductions = standard_deduction + hra_exemption + section_80c + section_80d
        taxable_income = max(0, total_income - total_deductions)
        
        # Calculate actual tax
        tax = calculate_tax_from_slabs(taxable_income)
        tax = max(0, tax + np.random.normal(0, tax * 0.05))  # Add 5% noise
        
        data.append({
            'total_income': round(total_income, 2),
            'salary_income': round(salary_income, 2),
            'business_income': round(business_income, 2),
            'capital_gains': round(capital_gains, 2),
            'standard_deduction': round(standard_deduction, 2),
            'hra_exemption': round(hra_exemption, 2),
            'section_80c': round(section_80c, 2),
            'section_80d': round(section_80d, 2),
            'total_deductions': round(total_deductions, 2),
            'taxable_income': round(taxable_income, 2),
            'fiscal_year': np.random.choice([2022, 2023, 2024]),
            'true_tax': round(tax, 2)
        })
    
    df = pd.DataFrame(data)
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Sample tax data created: {output_path}")
    except Exception as e:
        print(f"Error saving data: {e}")
        raise
    return df

def prepare_features(df):
    """Prepare features for tax prediction"""
    feature_columns = [
        'total_income', 'salary_income', 'business_income', 'capital_gains',
        'total_deductions', 'taxable_income', 'fiscal_year'
    ]
    
    # Create additional features
    df['income_diversity'] = (
        (df['salary_income'] > 0).astype(int) +
        (df['business_income'] > 0).astype(int) +
        (df['capital_gains'] > 0).astype(int)
    )
    
    df['deduction_ratio'] = df['total_deductions'] / (df['total_income'] + 1)
    df['log_total_income'] = np.log1p(df['total_income'])
    df['log_taxable_income'] = np.log1p(df['taxable_income'])
    
    feature_columns.extend(['income_diversity', 'deduction_ratio', 'log_total_income', 'log_taxable_income'])
    
    X = df[feature_columns]
    y = df['true_tax']
    
    return X, y, feature_columns

def train_model(X, y):
    """Train XGBoost model for tax prediction"""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    model = xgb.XGBRegressor(
        n_estimators=300,
        learning_rate=0.1,
        max_depth=6,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred_test = model.predict(X_test)
    
    print(f"Test R²: {r2_score(y_test, y_pred_test):.4f}")
    print(f"Test MAE: ₹{mean_absolute_error(y_test, y_pred_test):.2f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 5 Feature Importances:")
    print(feature_importance.head())
    
    return model

def save_model(model, feature_names, output_dir="./"):
    """Save trained model and metadata"""
    # Normalize directory path
    output_dir = os.path.normpath(output_dir)
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        model_path = os.path.join(output_dir, "tax_model_v1.joblib")
        joblib.dump(model, model_path)
        
        metadata = {
            "model_type": "XGBRegressor",
            "feature_names": feature_names,
            "trained_at": datetime.now().isoformat(),
            "hyperparameters": {
                "n_estimators": 300,
                "learning_rate": 0.1,
                "max_depth": 6
            }
        }
        
        metadata_path = os.path.join(output_dir, "tax_model_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Model saved: {model_path}")
    except Exception as e:
        print(f"Error saving model: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Train tax prediction model')
    parser.add_argument('--data_path', default='../data/tax_dataset.csv')
    parser.add_argument('--output_dir', default='./')
    parser.add_argument('--create_sample', action='store_true')
    parser.add_argument('--n_samples', type=int, default=5000)
    
    args = parser.parse_args()
    
    try:
        if args.create_sample or not os.path.exists(args.data_path):
            create_sample_tax_data(args.data_path, args.n_samples)
        
        df = pd.read_csv(args.data_path)
        print(f"Loaded {len(df)} tax records")
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    X, y, feature_names = prepare_features(df)
    model = train_model(X, y)
    save_model(model, feature_names, args.output_dir)
    
    print("Training completed successfully!")

if __name__ == "__main__":
    main()