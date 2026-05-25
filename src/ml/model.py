"""Neural network model for orbital residual prediction."""

import torch
import torch.nn as nn


FEATURE_NAMES = [
    'time_since_epoch_hours',
    'mean_motion_rev_per_day',
    'eccentricity',
    'inclination_deg',
    'bstar',
    'altitude_km',
]
DEFAULT_HIDDEN_DIMS = [256, 128, 64, 32]
DEFAULT_DROPOUT     = 0.15


class ResidualPredictor(nn.Module):
    """Fully connected network with BatchNorm for orbital residual prediction.

    Input features (6):
      time_since_epoch_hours, mean_motion_rev_per_day, eccentricity,
      inclination_deg, bstar, altitude_km

    Output:
      along_track_position_error_km
    """

    def __init__(self, input_dim: int = 6, hidden_dims: list = None, dropout_rate: float = DEFAULT_DROPOUT):
        super().__init__()

        if hidden_dims is None:
            hidden_dims = DEFAULT_HIDDEN_DIMS

        layers = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers += [
                nn.Linear(prev_dim, h),
                nn.BatchNorm1d(h),
                nn.ReLU(),
                nn.Dropout(dropout_rate),
            ]
            prev_dim = h
        layers.append(nn.Linear(prev_dim, 1))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


def create_model(device: torch.device) -> ResidualPredictor:
    """Create default model and move to device."""
    return ResidualPredictor(
        input_dim=len(FEATURE_NAMES),
        hidden_dims=DEFAULT_HIDDEN_DIMS,
        dropout_rate=DEFAULT_DROPOUT,
    ).to(device)
