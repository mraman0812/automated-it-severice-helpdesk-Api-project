from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.ml.model_manager import model_manager
from app.models.category import Category, SubCategory
from app.models.department import Department
from app.models.classification import TicketClassification
from app.models.ml_model import MLModel, ModelStatusEnum
from app.core.logging import logger


class ClassificationService:
    @staticmethod
    def predict_ticket(
        title: str,
        description: str,
        db: Optional[Session] = None,
        ticket_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run classification model on ticket title and description.
        If db and ticket_id are provided, record classification history in ticket_classifications table.
        """
        predictor = model_manager.get_predictor()
        prediction = predictor.predict(title, description)

        category_name = prediction["category"]
        subcategory_name = prediction["subcategory"]
        priority = prediction["priority"]
        dept_name = prediction["department"]
        confidence = prediction["confidence"]
        needs_review = prediction["needs_review"]

        category_id = None
        subcategory_id = None
        department_id = None

        if db:
            # Resolve Category ID
            cat_obj = db.query(Category).filter(Category.name == category_name).first()
            if cat_obj:
                category_id = cat_obj.id
                # Resolve SubCategory ID
                sub_obj = db.query(SubCategory).filter(
                    SubCategory.category_id == cat_obj.id,
                    SubCategory.name == subcategory_name
                ).first()
                if sub_obj:
                    subcategory_id = sub_obj.id

            # Resolve Department ID
            dept_obj = db.query(Department).filter(Department.name == dept_name).first()
            if dept_obj:
                department_id = dept_obj.id

            # If ticket_id is provided, store classification record
            if ticket_id:
                active_model = db.query(MLModel).filter(MLModel.status == ModelStatusEnum.ACTIVE).first()
                model_id = active_model.id if active_model else None

                classification_record = TicketClassification(
                    ticket_id=ticket_id,
                    model_id=model_id,
                    predicted_category=category_name,
                    predicted_subcategory=subcategory_name,
                    predicted_priority=priority,
                    confidence=confidence,
                    was_correct=None,
                )
                db.add(classification_record)
                db.flush()

        return {
            "category": category_name,
            "category_id": category_id,
            "subcategory": subcategory_name,
            "subcategory_id": subcategory_id,
            "priority": priority,
            "department": dept_name,
            "department_id": department_id,
            "confidence": confidence,
            "needs_review": needs_review,
        }
