"""Training utilities for ML model."""

import csv
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
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


def train_model(
    train_csv: str,
    val_csv: str,
    output_model_path: str,
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    device: str = None
) -> str:
    """Train residual predictor model."""
    
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    device = torch.device(device)
    print(f"Using device: {device}")
    
    # Load datasets
    train_dataset = ResidualDataset(train_csv)
    val_dataset = ResidualDataset(val_csv)
    
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Create model
    model = create_model(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    print(f"Training on {len(train_dataset)} samples for {epochs} epochs...")
    
    best_val_loss = float('inf')
    for epoch in range(epochs):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss = validate(model, val_loader, criterion, device)
        
        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch+1}/{epochs}: train_loss={train_loss:.6f}, val_loss={val_loss:.6f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), output_model_path)
    
    print(f"✓ Best model saved to {output_model_path}")
    return output_model_path
