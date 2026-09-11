import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import LinearSVC

from app.core.config import settings
from app.core.logging import logger
from app.ml.preprocessing import combine_ticket_text
from app.ml.evaluate import evaluate_predictions


def train_models(
    dataset_path: str = None,
    output_dir: str = None,
    version: str = "v1.0",
    algorithm: str = "LogisticRegression",
) -> Dict[str, Any]:
    start_time = time.time()

    if not dataset_path:
        dataset_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "training",
            "tickets.csv",
        )

    if not output_dir:
        output_dir = settings.MODEL_DIR

    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Loading training data from: {dataset_path}")
    df = pd.read_csv(dataset_path)

    # Basic data validation
    required_cols = {"title", "description", "category", "subcategory", "priority"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Dataset missing required columns. Must contain: {required_cols}")

    df = df.dropna(subset=["title", "category", "priority"])
    df["description"] = df["description"].fillna("")
    df["subcategory"] = df["subcategory"].fillna("General")

    # Combine text
    logger.info("Preprocessing ticket texts...")
    df["processed_text"] = df.apply(lambda r: combine_ticket_text(r["title"], r["description"]), axis=1)

    X = df["processed_text"].values
    y_cat = df["category"].values
    y_sub = df["subcategory"].values
    y_prio = df["priority"].values

    # Train-test split (80/20 stratified by category)
    X_train, X_test, y_cat_train, y_cat_test, y_sub_train, y_sub_test, y_prio_train, y_prio_test = (
        train_test_split(
            X, y_cat, y_sub, y_prio,
            test_size=0.20,
            random_state=42,
            stratify=y_cat,
        )
    )

    logger.info(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")

    # 1. TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True,
        min_df=2,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Helper to instantiate classifier
    def make_clf():
        if algorithm == "LinearSVC":
            base = LinearSVC(C=1.0, max_iter=2000, random_state=42)
            return CalibratedClassifierCV(base)
        return LogisticRegression(C=2.0, max_iter=1000, class_weight="balanced", random_state=42)

    # 2. Category Model
    logger.info("Training Category Model...")
    category_model = make_clf()
    category_model.fit(X_train_vec, y_cat_train)
    cat_preds = category_model.predict(X_test_vec)
    cat_eval = evaluate_predictions(y_cat_test, cat_preds)
    logger.info(f"Category Model Accuracy: {cat_eval['accuracy']:.4f}, F1: {cat_eval['f1_score']:.4f}")

    # 3. Subcategory Model
    logger.info("Training Subcategory Model...")
    subcategory_model = make_clf()
    subcategory_model.fit(X_train_vec, y_sub_train)
    sub_preds = subcategory_model.predict(X_test_vec)
    sub_eval = evaluate_predictions(y_sub_test, sub_preds)
    logger.info(f"Subcategory Model Accuracy: {sub_eval['accuracy']:.4f}, F1: {sub_eval['f1_score']:.4f}")

    # 4. Priority Model
    logger.info("Training Priority Model...")
    priority_model = make_clf()
    priority_model.fit(X_train_vec, y_prio_train)
    prio_preds = priority_model.predict(X_test_vec)
    prio_eval = evaluate_predictions(y_prio_test, prio_preds)
    logger.info(f"Priority Model Accuracy: {prio_eval['accuracy']:.4f}, F1: {prio_eval['f1_score']:.4f}")

    # Save artifacts
    logger.info(f"Saving model artifacts to {output_dir}...")
    joblib.dump(vectorizer, os.path.join(output_dir, "vectorizer.joblib"))
    joblib.dump(category_model, os.path.join(output_dir, "category_model.joblib"))
    joblib.dump(subcategory_model, os.path.join(output_dir, "subcategory_model.joblib"))
    joblib.dump(priority_model, os.path.join(output_dir, "priority_model.joblib"))

    duration = round(time.time() - start_time, 2)

    metadata = {
        "model_name": "TicketClassifier",
        "version": version,
        "algorithm": algorithm,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "duration_seconds": duration,
        "category_metrics": cat_eval,
        "subcategory_metrics": sub_eval,
        "priority_metrics": prio_eval,
        "overall_accuracy": cat_eval["accuracy"],
        "overall_f1": cat_eval["f1_score"],
        "categories": sorted(list(category_model.classes_)),
        "priorities": sorted(list(priority_model.classes_)),
    }

    with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Model training completed successfully in {duration}s!")
    return metadata
