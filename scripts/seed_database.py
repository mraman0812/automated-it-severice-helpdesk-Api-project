"""
Database Seeding Script.
Populates initial roles, departments, categories, subcategories, sample users, ML model record, and tickets.
"""
import sys
import os
from datetime import datetime, timezone, timedelta

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import SessionLocal, init_db
from app.core.security import get_password_hash
from app.models.role import Role, RoleEnum
from app.models.department import Department
from app.models.category import Category, SubCategory
from app.models.user import User
from app.models.ticket import Ticket, PriorityEnum, TicketStatusEnum
from app.models.ml_model import MLModel, ModelStatusEnum


def seed():
    print("Initializing database tables...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Roles
        roles_data = [
            (RoleEnum.ADMIN.value, "System Administrator with full access"),
            (RoleEnum.MANAGER.value, "IT Support Manager"),
            (RoleEnum.AGENT.value, "IT Support Agent / Technician"),
            (RoleEnum.EMPLOYEE.value, "General Company Employee"),
        ]
        role_map = {}
        for r_name, r_desc in roles_data:
            role = db.query(Role).filter(Role.name == r_name).first()
            if not role:
                role = Role(name=r_name, description=r_desc)
                db.add(role)
                db.flush()
            role_map[r_name] = role
        print("[OK] Roles seeded.")

        # 2. Departments
        departments_data = [
            ("IT Helpdesk", "General account access and first-level triage", "helpdesk@company.com"),
            ("Network Support", "LAN, WAN, VPN, WiFi and internet connectivity", "network@company.com"),
            ("Hardware Support", "Laptops, desktops, monitors, peripherals, and printers", "hardware@company.com"),
            ("Software Support", "Operating systems, enterprise software, and licensing", "software@company.com"),
            ("Email Support", "Exchange, Outlook, and email routing", "email@company.com"),
            ("Security", "Cybersecurity, malware, phishing, and incident response", "security@company.com"),
            ("Infrastructure", "Datacenter, servers, databases, and cloud infrastructure", "infra@company.com"),
        ]
        dept_map = {}
        for d_name, d_desc, d_email in departments_data:
            dept = db.query(Department).filter(Department.name == d_name).first()
            if not dept:
                dept = Department(name=d_name, description=d_desc, email=d_email)
                db.add(dept)
                db.flush()
            dept_map[d_name] = dept
        print("[OK] Departments seeded.")

        # 3. Categories and Subcategories
        categories_data = {
            "Network": [
                ("VPN", "Virtual private network client and tunnels"),
                ("WiFi", "Wireless local area network connections"),
                ("Internet Connectivity", "Workstation internet routing and gateway"),
                ("DNS", "Domain name resolution"),
            ],
            "Hardware": [
                ("Laptop", "Laptop chassis, batteries, and screens"),
                ("Monitor", "External displays and cables"),
                ("Printer", "Network and local printing devices"),
                ("Peripherals", "Keyboards, mice, and webcams"),
            ],
            "Software": [
                ("Application Crash", "Unexpected application freezes and terminations"),
                ("Software Installation", "Requests to deploy approved corporate tools"),
                ("License Issue", "Product activation keys and renewals"),
                ("Update Issue", "OS and browser update errors"),
            ],
            "Account & Access": [
                ("Password Reset", "Active directory and SSO password changes"),
                ("Login Problem", "Locked accounts and login errors"),
                ("MFA", "Multi-factor authenticator setup and resets"),
                ("Access Request", "Shared folder and application permissions"),
            ],
            "Email": [
                ("Outlook Problem", "Outlook desktop client and profile issues"),
                ("Email Not Sending", "Outgoing message failures and NDR bounces"),
                ("Email Not Receiving", "Missing incoming mail and quota limits"),
                ("Spam", "Junk mail and suspicious attachments"),
            ],
            "Security": [
                ("Phishing", "Fraudulent emails and credential harvesting"),
                ("Malware", "Viruses, ransomware, and quarantine alerts"),
                ("Suspicious Login", "Unfamiliar geographic logins"),
                ("Security Incident", "Lost devices and data leaks"),
            ],
            "Server / Infrastructure": [
                ("Server Down", "Core host, VM, or cluster outages"),
                ("Database Issue", "Connection pools, deadlocks, and disk space"),
                ("Storage", "SAN, NAS, and network file shares"),
                ("Backup", "Scheduled backup jobs and restoration"),
                ("System Outage", "Datacenter wide power and switch failures"),
            ],
        }

        for cat_name, subcats in categories_data.items():
            cat = db.query(Category).filter(Category.name == cat_name).first()
            if not cat:
                cat = Category(name=cat_name, description=f"{cat_name} related IT requests")
                db.add(cat)
                db.flush()

            for sub_name, sub_desc in subcats:
                sub = db.query(SubCategory).filter(
                    SubCategory.category_id == cat.id,
                    SubCategory.name == sub_name
                ).first()
                if not sub:
                    sub = SubCategory(category_id=cat.id, name=sub_name, description=sub_desc)
                    db.add(sub)
                    db.flush()
        print("[OK] Categories and Subcategories seeded.")

        # 4. Users
        users_data = [
            ("Admin User", "admin@example.com", "AdminPass123!", RoleEnum.ADMIN.value, None),
            ("IT Manager", "manager@example.com", "ManagerPass123!", RoleEnum.MANAGER.value, "IT Helpdesk"),
            ("Network Agent", "network.agent@example.com", "AgentPass123!", RoleEnum.AGENT.value, "Network Support"),
            ("Hardware Agent", "hardware.agent@example.com", "AgentPass123!", RoleEnum.AGENT.value, "Hardware Support"),
            ("Software Agent", "software.agent@example.com", "AgentPass123!", RoleEnum.AGENT.value, "Software Support"),
            ("Security Agent", "security.agent@example.com", "AgentPass123!", RoleEnum.AGENT.value, "Security"),
            ("Helpdesk Agent", "helpdesk.agent@example.com", "AgentPass123!", RoleEnum.AGENT.value, "IT Helpdesk"),
            ("Rajan Sharma", "rajan@example.com", "UserPass123!", RoleEnum.EMPLOYEE.value, None),
            ("Alice Smith", "alice@example.com", "UserPass123!", RoleEnum.EMPLOYEE.value, None),
        ]

        user_map = {}
        for name, email, pwd, role_n, dept_n in users_data:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                dept_id = dept_map[dept_n].id if dept_n and dept_n in dept_map else None
                user = User(
                    name=name,
                    email=email,
                    password_hash=get_password_hash(pwd),
                    role_id=role_map[role_n].id,
                    department_id=dept_id,
                    is_active=True,
                )
                db.add(user)
                db.flush()
            user_map[email] = user
        print("[OK] Users seeded (Admin, Manager, Agents, Employees).")

        # 5. Register Active Model Record
        model_rec = db.query(MLModel).filter(MLModel.version == "v1.0").first()
        if not model_rec:
            model_rec = MLModel(
                model_name="TicketClassifier",
                model_type="TFIDF_LogisticRegression",
                version="v1.0",
                accuracy=0.985,
                precision=0.982,
                recall=0.980,
                f1_score=0.981,
                file_path="app/ml/artifacts",
                status=ModelStatusEnum.ACTIVE,
                trained_at=datetime.now(timezone.utc),
            )
            db.add(model_rec)
            db.flush()
        print("[OK] Active ML Model registered.")

        # 6. Sample Tickets
        sample_tickets = [
            (
                "IT-2026-000001",
                "Cannot connect to company VPN from home",
                "Working remotely today and Cisco AnyConnect refuses to establish the tunnel. Authentication completes but connection drops immediately.",
                "Network", "VPN", PriorityEnum.HIGH, TicketStatusEnum.ASSIGNED,
                "rajan@example.com", "network.agent@example.com", "Network Support",
                0.96, False, 4,
            ),
            (
                "IT-2026-000002",
                "Laptop battery bulging trackpad",
                "Notice my ThinkPad battery is severely swollen and pushing the trackpad up so it won't click. Need replacement battery urgently.",
                "Hardware", "Laptop", PriorityEnum.HIGH, TicketStatusEnum.IN_PROGRESS,
                "alice@example.com", "hardware.agent@example.com", "Hardware Support",
                0.94, False, 4,
            ),
            (
                "IT-2026-000003",
                "Forgot my domain password after holidays",
                "Unable to login to my desktop computer. Self service reset says questions are not set.",
                "Account & Access", "Password Reset", PriorityEnum.MEDIUM, TicketStatusEnum.RESOLVED,
                "rajan@example.com", "helpdesk.agent@example.com", "IT Helpdesk",
                0.98, False, 24,
            ),
            (
                "IT-2026-000004",
                "Production database connection pool exhausted",
                "PostgreSQL primary database is throwing FATAL: remaining connection slots reserved for superuser. Multiple API endpoints returning 500 errors.",
                "Server / Infrastructure", "Database Issue", PriorityEnum.CRITICAL, TicketStatusEnum.IN_PROGRESS,
                "alice@example.com", "helpdesk.agent@example.com", "Infrastructure",
                0.95, False, 2,
            ),
            (
                "IT-2026-000005",
                "Vague error when saving file",
                "Something went wrong when trying to do stuff on the computer.",
                "Software", "Application Error", PriorityEnum.LOW, TicketStatusEnum.OPEN,
                "rajan@example.com", None, "IT Helpdesk",
                0.48, True, 72,
            ),
        ]

        now = datetime.now(timezone.utc)
        for num, title, desc, cat_n, sub_n, prio, st, creator_e, agent_e, dept_n, conf, review, sla_h in sample_tickets:
            t = db.query(Ticket).filter(Ticket.ticket_number == num).first()
            if not t:
                creator = user_map[creator_e]
                agent = user_map.get(agent_e)
                cat = db.query(Category).filter(Category.name == cat_n).first()
                dept = db.query(Department).filter(Department.name == dept_n).first()

                t = Ticket(
                    ticket_number=num,
                    title=title,
                    description=desc,
                    category_id=cat.id if cat else None,
                    department_id=dept.id if dept else None,
                    priority=prio,
                    status=st,
                    created_by=creator.id,
                    assigned_to=agent.id if agent else None,
                    predicted_category=cat_n,
                    predicted_subcategory=sub_n,
                    predicted_priority=prio.value,
                    confidence_score=conf,
                    needs_review=review,
                    sla_deadline=now + timedelta(hours=sla_h),
                    sla_breached=False,
                    resolution_note="Temporary password issued and MFA verified." if st == TicketStatusEnum.RESOLVED else None,
                    resolved_at=now - timedelta(hours=2) if st == TicketStatusEnum.RESOLVED else None,
                )
                db.add(t)

        db.commit()
        print("[OK] Sample tickets seeded.")
        print("\nSeed completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
