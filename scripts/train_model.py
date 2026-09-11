"""
CLI command to train the initial ML models and populate app/ml/artifacts.
"""
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.train import train_models
from app.ml.model_manager import model_manager


def main():
    print("==================================================")
    print(" Training Automated IT Ticket Classifier Models   ")
    print("==================================================")
    metadata = train_models()
    print("\n--- Training Results ---")
    print(f"Version:            {metadata['version']}")
    print(f"Algorithm:          {metadata['algorithm']}")
    print(f"Overall Accuracy:   {metadata['overall_accuracy'] * 100:.2f}%")
    print(f"Overall F1 Score:   {metadata['overall_f1'] * 100:.2f}%")
    print(f"Training Samples:   {metadata['training_samples']}")
    print(f"Test Samples:       {metadata['test_samples']}")
    print(f"Duration:           {metadata['duration_seconds']}s")
    print("==================================================")

    # Reload into model manager
    model_manager.load_models()
    print("Model manager reloaded active artifacts.")


if __name__ == "__main__":
    main()
