"""
Anomaly Detection Model Training Script
Trains an Isolation Forest model for detecting anomalous transactions.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import json
import argparse
import os
from datetime import datetime

def create_sample_data(output_path="../data/sample_transactions.csv", n_samples=1000):
    """Create sample transaction data"""
    # Validate and sanitize output path
    output_path = os.path.normpath(output_path)
    if '..' in output_path or output_path.startswith('/'):
        raise ValueError("Invalid output path")
    
    np.random.seed(42)
    
    merchants = ['Amazon', 'Walmart', 'Starbucks', 'Shell', 'Home Depot', 'Apple Store', 'Uber', 'Restaurant XYZ']
    categories = ['groceries', 'gas', 'restaurants', 'shopping', 'entertainment', 'travel', 'utilities']
    
    data = []
    for i in range(n_samples):
        merchant = np.random.choice(merchants)
        category = np.random.choice(categories)
        
        # Generate realistic amounts by category
        if category == 'groceries':
            amount = np.random.lognormal(4, 0.5)
        elif category == 'gas':
            amount = np.random.lognormal(3.5, 0.3)
        else:
            amount = np.random.lognormal(3.5, 0.8)
        
        days_ago = np.random.randint(0, 365)
        date = pd.Timestamp.now() - pd.Timedelta(days=days_ago)
        
        data.append({
            'date': date.strftime('%Y-%m-%d %H:%M:%S'),
            'amount': round(amount, 2),
            'merchant': merchant,
            'category': category,
            'description': f'{category} purchase at {merchant}'
        })
    
    df = pd.DataFrame(data)
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Sample data created: {output_path}")
    except Exception as e:
        print(f"Error saving data: {e}")
        raise
    return df

def engineer_features(df):
    """Engineer features for anomaly detection"""
    features = pd.DataFrame()
    
    # Amount features
    features['log_amount'] = np.log1p(df['amount'].abs())
    features['amount_zscore'] = (df['amount'] - df['amount'].mean()) / df['amount'].std()
    features['is_round_amount'] = (df['amount'] % 1 == 0).astype(int)
    
    # Frequency features
    merchant_counts = df['merchant'].value_counts()
    features['merchant_frequency'] = df['merchant'].map(merchant_counts)
    
    category_counts = df['category'].value_counts()
    features['category_frequency'] = df['category'].map(category_counts)
    
    # Time features
    df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
    features['hour_of_day'] = df['date_parsed'].dt.hour.fillna(12)
    features['day_of_week'] = df['date_parsed'].dt.dayofweek.fillna(1)
    features['is_weekend'] = (features['day_of_week'] >= 5).astype(int)
    
    return features.fillna(0)

def create_synthetic_anomalies(features, anomaly_ratio=0.02):
    """Create synthetic anomalies for validation"""
    n_anomalies = int(len(features) * anomaly_ratio)
    anomaly_indices = np.random.choice(len(features), n_anomalies, replace=False)
    
    labels = np.zeros(len(features))
    features_modified = features.copy()
    
    for idx in anomaly_indices:
        labels[idx] = 1
        # Create high amount anomaly
        features_modified.loc[idx, 'log_amount'] *= np.random.uniform(3, 10)
        features_modified.loc[idx, 'merchant_frequency'] = 1
    
    return features_modified, labels

def train_model(features, labels, contamination=0.01):
    """Train Isolation Forest model"""
    X_train, X_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train_scaled)
    
    # Evaluate
    predictions = model.predict(X_test_scaled)
    predictions_binary = (predictions == -1).astype(int)
    
    print("\nModel Evaluation:")
    print(classification_report(y_test, predictions_binary))
    
    return model, scaler

def save_model(model, scaler, feature_names, output_dir="./"):
    """Save trained model and metadata"""
    # Validate and sanitize output directory
    output_dir = os.path.normpath(output_dir)
    if '..' in output_dir or output_dir.startswith('/'):
        raise ValueError("Invalid output directory")
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        model_path = os.path.join(output_dir, "anomaly_model_v1.joblib")
        scaler_path = os.path.join(output_dir, "anomaly_scaler_v1.joblib")
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        metadata = {
            "model_type": "IsolationForest",
            "feature_names": feature_names,
            "trained_at": datetime.now().isoformat(),
            "contamination": 0.01
        }
        
        metadata_path = os.path.join(output_dir, "anomaly_model_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Model saved: {model_path}")
        print(f"Scaler saved: {scaler_path}")
    except Exception as e:
        print(f"Error saving model: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Train anomaly detection model')
    parser.add_argument('--data_path', default='../data/sample_transactions.csv')
    parser.add_argument('--output_dir', default='./')
    parser.add_argument('--create_sample', action='store_true')
    
    args = parser.parse_args()
    
    try:
        if args.create_sample or not os.path.exists(args.data_path):
            create_sample_data(args.data_path)
        
        df = pd.read_csv(args.data_path)
        print(f"Loaded {len(df)} transactions")
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    features = engineer_features(df)
    features_with_anomalies, labels = create_synthetic_anomalies(features)
    
    model, scaler = train_model(features_with_anomalies, labels)
    save_model(model, scaler, list(features.columns), args.output_dir)
    
    print("Training completed successfully!")

if __name__ == "__main__":
    main()