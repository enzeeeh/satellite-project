"""
Main entry point for ML-corrected pass prediction.

Provides both training and inference workflows.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Import satcore physics (unified core library)
from satcore.ground_station import GroundStation  # type: ignore

# Import v2.0 modules
sys.path.insert(0, str(Path(__file__).parent))
from ml.train import generate_synthetic_training_data, train_model
from pipeline import predict_passes_with_correction


def main():
    parser = argparse.ArgumentParser(description="ML-corrected orbital pass prediction")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Training command
    train_parser = subparsers.add_parser('train', help='Train ML model')
    train_parser.add_argument('--epochs', type=int, default=50, help='Training epochs')
    train_parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    train_parser.add_argument('--learning-rate', type=float, default=0.001, help='Learning rate')
    train_parser.add_argument('--num-samples', type=int, default=500, help='Synthetic samples')
    train_parser.add_argument('--data-dir', default='data', help='Data directory')
    train_parser.add_argument('--model-dir', default='models', help='Model directory')
    
    # Prediction command
    pred_parser = subparsers.add_parser('predict', help='Predict passes with correction')
    pred_parser.add_argument('--tle', required=True, help='TLE file path')
    pred_parser.add_argument('--model', required=True, help='Model file path')
    pred_parser.add_argument('--hours', type=int, default=24, help='Prediction window')
    pred_parser.add_argument('--step', type=int, default=300, help='Time step (seconds)')
    pred_parser.add_argument('--threshold', type=float, default=10.0, help='Elevation threshold')
    pred_parser.add_argument('--station-lat', type=float, default=40.0, help='Station latitude')
    pred_parser.add_argument('--station-lon', type=float, default=-105.0, help='Station longitude')
    pred_parser.add_argument('--station-alt', type=float, default=1.6, help='Station altitude')
    pred_parser.add_argument('--no-correction', action='store_true', help='Disable ML correction')
    pred_parser.add_argument('--outdir', default='outputs', help='Output directory')
    
    args = parser.parse_args()
    
    if args.command == 'train':
        train_command(args)
    elif args.command == 'predict':
        predict_command(args)
    else:
        parser.print_help()


def train_command(args):
    """Execute training workflow."""
    data_dir = Path(args.data_dir)
    model_dir = Path(args.model_dir)
    
    data_dir.mkdir(exist_ok=True)
    model_dir.mkdir(exist_ok=True)
    
    train_csv = data_dir / 'train.csv'
    val_csv = data_dir / 'val.csv'
    model_path = model_dir / 'residual_model.pt'
    
    # Generate synthetic data
    print("Generating synthetic training data...")
    generate_synthetic_training_data(
        str(train_csv),
        str(val_csv),
        num_samples=args.num_samples
    )
    
    # Train model
    print("\nTraining model...")
    train_model(
        str(train_csv),
        str(val_csv),
        str(model_path),
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate
    )
    
    print(f"\n✓ Training complete. Model saved to: {model_path}")


def predict_command(args):
    """Execute prediction workflow."""
    # Setup
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Time window
    start_utc = datetime.utcnow()
    end_utc = start_utc + timedelta(hours=args.hours)
    
    # Ground station
    station = GroundStation(args.station_lat, args.station_lon, args.station_alt)
    
    print(f"Predicting passes (correction: {'OFF' if args.no_correction else 'ON'})")
    print(f"  TLE: {args.tle}")
    print(f"  Model: {args.model}")
    print(f"  Window: {start_utc.isoformat()} to {end_utc.isoformat()}")
    print(f"  Station: ({args.station_lat}°, {args.station_lon}°, {args.station_alt}km)")
    print()
    
    # Predict
    passes, corrections = predict_passes_with_correction(
        args.tle,
        args.model,
        start_utc,
        end_utc,
        args.step,
        station,
        args.threshold,
        apply_correction=not args.no_correction
    )
    
    # Output
    print(f"Detected {len(passes)} passes")
    if passes:
        print(f"\nPass predictions:")
        for i, p in enumerate(passes, 1):
            print(f"  Pass {i}: {p.start_time.isoformat()}Z to {p.end_time.isoformat()}Z")
            print(f"    Max elevation: {p.max_elevation_deg:.2f}°")
    
    # Correction statistics
    if corrections:
        import numpy as np
        corrections_nonzero = [c for c in corrections if c != 0]
        if corrections_nonzero:
            print(f"\nML Correction statistics:")
            print(f"  Mean correction: {np.mean(corrections_nonzero):.4f} km")
            print(f"  Std deviation: {np.std(corrections_nonzero):.4f} km")
            print(f"  Range: [{np.min(corrections_nonzero):.4f}, {np.max(corrections_nonzero):.4f}] km")


if __name__ == '__main__':
    main()
