"""
Training script for orbital residual predictor.

Generates synthetic training data and trains the model.
"""

import csv
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from datetime import datetime, timedelta
import sys
import numpy as np

from .model import ResidualPredictor, create_model


class ResidualDataset:
    """Simple dataset loader for residuals."""
    
    def __init__(self, csv_path: str):
        """Load CSV with columns: time_since_epoch, mean_motion, eccentricity, inclination, target."""
        self.data = []
        self.targets = []
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                features = [
                    float(row['time_since_epoch_hours']),
                    float(row['mean_motion_rev_per_day']),
                    float(row['eccentricity']),
                    float(row['inclination_deg'])
                ]
                target = float(row['along_track_error_km'])
                self.data.append(features)
                self.targets.append(target)
        
        self.data = np.array(self.data, dtype=np.float32)
        self.targets = np.array(self.targets, dtype=np.float32)
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        return torch.from_numpy(self.data[idx]), torch.tensor(self.targets[idx], dtype=torch.float32)


def train_epoch(model, train_loader, optimizer, criterion, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    
    for batch_x, batch_y in train_loader:
        batch_x = batch_x.to(device)
        batch_y = batch_y.to(device).unsqueeze(1)
        
        optimizer.zero_grad()
        pred = model(batch_x)
        loss = criterion(pred, batch_y)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(train_loader)


def validate(model, val_loader, criterion, device):
    """Validate model."""
    model.eval()
    total_loss = 0.0
    
    with torch.no_grad():
        for batch_x, batch_y in val_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device).unsqueeze(1)
            
            pred = model(batch_x)
            loss = criterion(pred, batch_y)
            total_loss += loss.item()
    
    return total_loss / len(val_loader)


def compute_rmse(predictions, targets):
    """Compute RMSE."""
    mse = np.mean((predictions - targets) ** 2)
    return np.sqrt(mse)


def train_model(
    train_csv: str,
    val_csv: str,
    output_model_path: str,
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    device: str = None
):
    """
    Train the residual prediction model.
    
    Args:
        train_csv: Path to training CSV
        val_csv: Path to validation CSV
        output_model_path: Where to save trained model
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        device: 'cuda' or 'cpu'
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    device = torch.device(device)
    print(f"Using device: {device}")
    
    # Load datasets
    print(f"Loading training data from {train_csv}")
    train_dataset = ResidualDataset(train_csv)
    print(f"  Loaded {len(train_dataset)} training samples")
    
    print(f"Loading validation data from {val_csv}")
    val_dataset = ResidualDataset(val_csv)
    print(f"  Loaded {len(val_dataset)} validation samples")
    
    # Create data loaders
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False
    )
    
    # Create model
    model = create_model(device)
    print(f"Model created: {model}")
    
    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training loop
    print(f"\nTraining for {epochs} epochs...")
    best_val_loss = float('inf')
    
    for epoch in range(1, epochs + 1):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss = validate(model, val_loader, criterion, device)
        
        if epoch % 10 == 0 or epoch == 1:
            print(f"Epoch {epoch:3d} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), output_model_path)
    
    # Final evaluation with RMSE
    print(f"\nFinal validation (on best model):")
    model.load_state_dict(torch.load(output_model_path))
    model.eval()
    
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for batch_x, batch_y in val_loader:
            batch_x = batch_x.to(device)
            preds = model(batch_x).cpu().numpy()
            all_preds.extend(preds.flatten())
            all_targets.extend(batch_y.numpy())
    
    rmse = compute_rmse(np.array(all_preds), np.array(all_targets))
    print(f"  RMSE: {rmse:.6f} km")
    print(f"  Model saved to: {output_model_path}")


def generate_synthetic_training_data(output_train: str, output_val: str, num_samples: int = 500):
    """
    Generate synthetic training data.
    
    Simulates residuals based on orbital element variations.
    """
    np.random.seed(42)
    
    # Realistic orbital parameter ranges (ISS-like)
    time_since_epoch = np.random.uniform(0, 120, num_samples)  # 0-120 hours
    mean_motion = np.random.uniform(14.5, 15.5, num_samples)  # rev/day
    eccentricity = np.random.uniform(0.0001, 0.005, num_samples)
    inclination = np.random.uniform(97, 98, num_samples)  # degrees
    
    # Synthetic residual: proportional to time and orbital elements
    # Realistic model: drift grows over time, depends on inclination and eccentricity
    along_track_error = (
        0.05 * time_since_epoch +  # Linear drift with time
        0.1 * eccentricity * 100 +  # Eccentricity effect
        0.001 * (inclination - 97) +  # Inclination effect
        np.random.normal(0, 0.02, num_samples)  # Noise
    )
    along_track_error = np.clip(along_track_error, -0.5, 0.5)  # Clip to realistic range
    
    # Split into train/val (80/20)
    split_idx = int(0.8 * num_samples)
    
    # Write training CSV
    with open(output_train, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'time_since_epoch_hours', 'mean_motion_rev_per_day', 'eccentricity',
            'inclination_deg', 'along_track_error_km'
        ])
        writer.writeheader()
        for i in range(split_idx):
            writer.writerow({
                'time_since_epoch_hours': time_since_epoch[i],
                'mean_motion_rev_per_day': mean_motion[i],
                'eccentricity': eccentricity[i],
                'inclination_deg': inclination[i],
                'along_track_error_km': along_track_error[i]
            })
    
    # Write validation CSV
    with open(output_val, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'time_since_epoch_hours', 'mean_motion_rev_per_day', 'eccentricity',
            'inclination_deg', 'along_track_error_km'
        ])
        writer.writeheader()
        for i in range(split_idx, num_samples):
            writer.writerow({
                'time_since_epoch_hours': time_since_epoch[i],
                'mean_motion_rev_per_day': mean_motion[i],
                'eccentricity': eccentricity[i],
                'inclination_deg': inclination[i],
                'along_track_error_km': along_track_error[i]
            })
    
    print(f"Generated {split_idx} training samples -> {output_train}")
    print(f"Generated {num_samples - split_idx} validation samples -> {output_val}")
