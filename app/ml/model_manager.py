import os
import json
from typing import Optional, Dict, Any
import joblib

from app.core.config import settings
from app.core.logging import logger
from app.ml.predict import Predictor


class ModelManager:
    _instance: Optional["ModelManager"] = None

    def __init__(self):
        self.model_dir = settings.MODEL_DIR
        self.vectorizer = None
        self.category_model = None
        self.subcategory_model = None
        self.priority_model = None
        self.metadata: Dict[str, Any] = {}
        self.is_loaded = False
        self.predictor = Predictor()

    @classmethod
    def get_instance(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = ModelManager()
        return cls._instance

    def load_models(self) -> bool:
        vec_path = os.path.join(self.model_dir, "vectorizer.joblib")
        cat_path = os.path.join(self.model_dir, "category_model.joblib")
        sub_path = os.path.join(self.model_dir, "subcategory_model.joblib")
        prio_path = os.path.join(self.model_dir, "priority_model.joblib")
        meta_path = os.path.join(self.model_dir, "metadata.json")

        if not all(os.path.exists(p) for p in [vec_path, cat_path, sub_path, prio_path]):
            logger.warning("One or more model artifact files are missing from %s", self.model_dir)
            self.is_loaded = False
            self.predictor = Predictor()
            return False

        try:
            logger.info("Loading ML models into memory...")
            self.vectorizer = joblib.load(vec_path)
            self.category_model = joblib.load(cat_path)
            self.subcategory_model = joblib.load(sub_path)
            self.priority_model = joblib.load(prio_path)

            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)

            self.predictor = Predictor(
                vectorizer=self.vectorizer,
                category_model=self.category_model,
                subcategory_model=self.subcategory_model,
                priority_model=self.priority_model,
            )
            self.is_loaded = True
            logger.info(
                "ML models successfully loaded into memory! Active version: %s",
                self.metadata.get("version", "v1.0")
            )
            return True
        except Exception as e:
            logger.error("Error loading ML models: %s", e)
            self.is_loaded = False
            self.predictor = Predictor()
            return False

    def get_predictor(self) -> Predictor:
        return self.predictor

    def get_metadata(self) -> Dict[str, Any]:
        return self.metadata


model_manager = ModelManager.get_instance()
