"""
Neural network model for orbital residual prediction.

Predicts along-track position error given orbital elements.
"""

import torch
import torch.nn as nn


class ResidualPredictor(nn.Module):
    """
    Fully connected neural network for orbital residual prediction.
    
    Input features:
    - time_since_tle_epoch_hours
    - mean_motion_rev_per_day
    - eccentricity
    - inclination_deg
    
    Output:
    - along_track_position_error_km
    """
    
    def __init__(self, input_dim: int = 4, hidden_dims: list = None, dropout_rate: float = 0.1):
        """
        Args:
            input_dim: Number of input features (default 4)
            hidden_dims: Hidden layer dimensions (default [64, 32, 16])
            dropout_rate: Dropout probability
        """
        super().__init__()
        
        if hidden_dims is None:
            hidden_dims = [64, 32, 16]
        
        layers = []
        prev_dim = input_dim
        
        # Build hidden layers
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout_rate))
            prev_dim = hidden_dim
        
        # Output layer (single value: residual magnitude)
        layers.append(nn.Linear(prev_dim, 1))
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch_size, 4)
        
        Returns:
            Predicted residual of shape (batch_size, 1)
        """
        return self.network(x)


def create_model(device: torch.device) -> ResidualPredictor:
    """Create and move model to device."""
    model = ResidualPredictor(input_dim=4, hidden_dims=[64, 32, 16], dropout_rate=0.1)
    return model.to(device)
