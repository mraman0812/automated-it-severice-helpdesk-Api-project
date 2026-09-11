from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import Role, RoleEnum
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.department import Department
from app.core.logging import logger


class AssignmentService:
    ACTIVE_STATUSES = [
        TicketStatusEnum.OPEN,
        TicketStatusEnum.CLASSIFIED,
        TicketStatusEnum.ASSIGNED,
        TicketStatusEnum.IN_PROGRESS,
        TicketStatusEnum.WAITING_FOR_USER,
    ]

    @classmethod
    def assign_agent(cls, db: Session, department_id: Optional[int]) -> Optional[User]:
        """
        Assign an agent based on load balancing:
        Find active agents in the department, count their active tickets,
        and select the one with the fewest active tickets.
        If no agent in the department, fallback to general IT Helpdesk department agents.
        """
        # Get Agent role
        agent_role = db.query(Role).filter(Role.name == RoleEnum.AGENT.value).first()
        if not agent_role:
            return None

        # Try to find agents in the specific department
        query = db.query(User).filter(
            User.role_id == agent_role.id,
            User.is_active == True,  # noqa: E712
        )

        dept_agents = []
        if department_id:
            dept_agents = query.filter(User.department_id == department_id).all()

        # Fallback: all active agents if department has none
        if not dept_agents:
            dept_agents = query.all()

        if not dept_agents:
            logger.warning("No active agents found in system for auto-assignment.")
            return None

        # Load balancing: Calculate active ticket count per candidate agent
        agent_ids = [a.id for a in dept_agents]
        counts = (
            db.query(Ticket.assigned_to, func.count(Ticket.id))
            .filter(
                Ticket.assigned_to.in_(agent_ids),
                Ticket.status.in_(cls.ACTIVE_STATUSES),
            )
            .group_by(Ticket.assigned_to)
            .all()
        )
        workload_map = {a_id: 0 for a_id in agent_ids}
        for a_id, count in counts:
            if a_id in workload_map:
                workload_map[a_id] = count

        # Pick agent with minimum active tickets
        best_agent_id = min(workload_map, key=workload_map.get)
        best_agent = next((a for a in dept_agents if a.id == best_agent_id), None)

        if best_agent:
            logger.info(
                f"Auto-assigned ticket to agent: {best_agent.name} (Active workload: {workload_map[best_agent_id]})"
            )
        return best_agent
